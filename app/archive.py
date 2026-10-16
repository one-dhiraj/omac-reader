import rarfile
from pathlib import Path
from zipfile import ZipFile, BadZipFile, ZIP_DEFLATED, ZIP_STORED
from io import BytesIO
import re

from PIL import Image

SUPPORTED_IMAGES = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".bmp",
    ".gif",
}


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

    except (rarfile.Error, OSError) as exc:
        raise ValueError(
            f"Unable to read this CBR archive: {exc}"
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
        with rarfile.RarFile(source_path, "r") as archive:
            return archive.read(archive_name)

    with ZipFile(source_path, "r") as archive:
        return archive.read(archive_name)

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

def save_cbz(file_path, pages):
    """
    Save pages in their current order, reading original bytes
    one page at a time without re-encoding unchanged images.
    """
    if not pages:
        raise ValueError("Cannot save a comic with no pages.")

    with ZipFile(
        file_path,
        mode="w",
        compression=ZIP_DEFLATED,
    ) as archive:
        for index, page in enumerate(pages, start=1):
            image_data = load_page_data(page)

            extension = Path(page["name"]).suffix.lower()

            if extension not in SUPPORTED_IMAGES:
                extension = ".png"

            archive.writestr(
                f"{index:04d}{extension}",
                image_data,
                compress_type=ZIP_STORED,
            )
