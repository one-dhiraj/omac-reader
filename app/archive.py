import rarfile
from pathlib import Path
from zipfile import ZipFile, BadZipFile, ZIP_DEFLATED, ZIP_STORED
from io import BytesIO
import re
import os
import tempfile

from PIL import Image

SUPPORTED_IMAGES = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".bmp",
    ".gif",
}
class SaveCancelledError(Exception):
    """Raised when the user cancels a comic save operation."""

def cbr_extraction_available():
    """Return whether a compatible RAR extraction tool is available."""
    try:
        rarfile.tool_setup()
    except rarfile.RarCannotExec:
        return False

    return True

def natural_sort_key(path):
    """Sort page1, page2, page10 in human reading order."""
    return [
        int(part) if part.isdigit() else part.lower()
        for part in re.split(r"(\d+)", path)
    ]

def load_cbz(file_path):
    """
    Load page metadata without decoding or retaining image data.
    """
    comic_path = Path(file_path)
    pages = []

    try:
        with ZipFile(comic_path, "r") as archive:
            image_names = [
                name
                for name in archive.namelist()
                if not name.endswith("/")
                and Path(name).suffix.lower() in SUPPORTED_IMAGES
            ]

            image_names.sort(key=natural_sort_key)

            for name in image_names:
                pages.append({
                    "name": Path(name).name,
                    "source_path": str(comic_path.resolve()),
                    "archive_name": name,
                    "archive_type": "cbz",
                })

    except BadZipFile as exc:
        raise ValueError(
            "This file is not a valid CBZ archive."
        ) from exc

    if not pages:
        raise ValueError(
            "No supported image pages were found in this archive."
        )

    return pages


def load_cbr(file_path):
    """Load CBR page metadata without extracting all images."""
    comic_path = Path(file_path)
    pages = []

    try:
        with rarfile.RarFile(comic_path, "r") as archive:
            image_names = [
                info.filename
                for info in archive.infolist()
                if not info.is_dir()
                and Path(info.filename).suffix.lower()
                in SUPPORTED_IMAGES
            ]

            image_names.sort(key=natural_sort_key)

            for name in image_names:
                pages.append({
                    "name": Path(name).name,
                    "source_path": str(comic_path.resolve()),
                    "archive_name": name,
                    "archive_type": "cbr",
                })

    except FileNotFoundError as exc:
        raise ValueError(
            f"The CBR file could not be found:\n{comic_path}"
        ) from exc

    except PermissionError as exc:
        raise ValueError(
            f"Permission denied while opening the CBR file:\n{comic_path}"
        ) from exc

    except rarfile.Error as exc:
        error_name = type(exc).__name__.lower()

        if any(
            term in error_name
            for term in ("cannotexec", "noexec", "execerror")
        ):
            message = (
                "A compatible RAR extraction utility is missing "
                "or could not be executed. Install a supported "
                "utility, such as unrar or unar."
            )
        elif any(
            term in error_name
            for term in ("password", "encrypted")
        ):
            message = (
                "This CBR archive may be password-protected. "
                "Encrypted archives are not currently supported."
            )
        else:
            message = (
                "Unable to read this CBR archive. It may be corrupted "
                "or use an unsupported RAR format."
            )

        raise ValueError(f"{message}\nDetails: {exc}") from exc

    except OSError as exc:
        raise ValueError(
            f"Unable to access the CBR file:\n{comic_path}\n"
            f"Details: {exc}"
        ) from exc

    if not pages:
        raise ValueError(
            "No supported image pages were found in this CBR archive."
        )

    return pages

def load_comic(file_path):
    """Load page metadata from a supported comic archive."""
    extension = Path(file_path).suffix.lower()

    if extension == ".cbz":
        return load_cbz(file_path)

    if extension == ".cbr":
        return load_cbr(file_path)

    raise ValueError(
        "Unsupported comic format. Please select a CBZ or CBR file."
    )

def load_page_data(page):
    """Read the original image bytes for one page only."""
    if "data" in page:
        return page["data"]

    source_path = page["source_path"]
    archive_name = page["archive_name"]

    if page.get("archive_type", "cbz") == "cbr":
        try:
            with rarfile.RarFile(source_path, "r") as archive:
                return archive.read(archive_name)

        except (rarfile.Error, OSError) as exc:
            error_name = type(exc).__name__.lower()

            if any(
                term in error_name
                for term in ("cannotexec", "noexec", "execerror")
            ):
                message = (
                    "A compatible RAR extraction utility is missing "
                    "or could not be executed. Install a supported "
                    "utility, such as unrar or unar, and try again."
                )
            else:
                message = (
                    f"Unable to extract page '{Path(archive_name).name}' "
                    "from the CBR archive. The archive may be corrupted, "
                    "encrypted, or use an unsupported RAR format."
                )

            raise ValueError(f"{message}\nDetails: {exc}") from exc

    try:
        with ZipFile(source_path, "r") as archive:
            return archive.read(archive_name)

    except (BadZipFile, OSError, KeyError) as exc:
        raise ValueError(
            f"Unable to read page '{Path(archive_name).name}' "
            f"from the CBZ archive.\nDetails: {exc}"
        ) from exc

def load_page_image(page):
    """
    Decode one page into a PIL image.
    """
    if "image" in page:
        return page["image"]

    image_data = load_page_data(page)

    with Image.open(BytesIO(image_data)) as source:
        source.load()
        return source.convert("RGBA" if "A" in source.getbands() else "RGB")


def load_page_thumbnail(page, size=(120, 160)):
    """
    Create a small thumbnail without converting the full-resolution
    page into a Qt image first.
    """
    if "image" in page:
        image = page["image"].copy()
        image.thumbnail(size, Image.Resampling.LANCZOS)
        return image

    image_data = load_page_data(page)

    with Image.open(BytesIO(image_data)) as source:
        source.thumbnail(size, Image.Resampling.LANCZOS)
        return source.convert(
            "RGBA" if "A" in source.getbands() else "RGB"
        )


def save_cbz(file_path, pages, progress_callback=None, cancel_check=None):
    """
    Save pages in their current order to a CBZ file.

    Writes to a temporary file first, replacing the destination
    only after the archive has been saved successfully.
    """
    if not pages:
        raise ValueError("Cannot save a comic with no pages.")

    destination = Path(file_path)
    temporary_path = None

    try:
        # Create the temporary file in the destination directory
        # so the final replacement happens on the same filesystem.
        fd, temporary_name = tempfile.mkstemp(
            prefix=f".{destination.name}.",
            suffix=".tmp",
            dir=destination.parent,
        )
        os.close(fd)
        temporary_path = Path(temporary_name)

        with ZipFile(
            temporary_path,
            mode="w",
            compression=ZIP_DEFLATED,
        ) as archive:
            total_pages = len(pages)

            for index, page in enumerate(pages, start=1):
                if cancel_check is not None and cancel_check():
                    raise SaveCancelledError(
                        "Saving was cancelled."
                    )

                image_data = load_page_data(page)

                extension = Path(page["name"]).suffix.lower()

                if extension not in SUPPORTED_IMAGES:
                    extension = ".png"

                archive.writestr(
                    f"{index:04d}{extension}",
                    image_data,
                    compress_type=ZIP_STORED,
                )

                if progress_callback is not None:
                    progress_callback(index, total_pages)

                if cancel_check is not None and cancel_check():
                    raise SaveCancelledError(
                        "Saving was cancelled."
                    )

        # Publish the completed archive only after closing it successfully.
        os.replace(temporary_path, destination)
        temporary_path = None

    finally:
        # Remove incomplete temporary output after cancellation or failure.
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass
