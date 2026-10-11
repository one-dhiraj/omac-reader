
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
    Load image pages while retaining their original image bytes.
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
                image_data = archive.read(name)

                with Image.open(BytesIO(image_data)) as image:
                    image.load()

                    pages.append({
                        "name": Path(name).name,
                        "image": image.convert("RGB").copy(),
                        "data": image_data,
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


def save_cbz(file_path, pages):
    """
    Save pages in their current order without re-encoding
    images whose original bytes are available.
    """
    if not pages:
        raise ValueError("Cannot save a comic with no pages.")

    with ZipFile(
        file_path,
        mode="w",
        compression=ZIP_DEFLATED,
    ) as archive:
        for index, page in enumerate(pages, start=1):
            image_data = page.get("data")

            if image_data is None:
                # Fallback for pages without retained original bytes.
                image_buffer = BytesIO()
                page["image"].save(image_buffer, format="PNG")
                image_data = image_buffer.getvalue()
                extension = ".png"
            else:
                extension = Path(page["name"]).suffix.lower()

                if extension not in SUPPORTED_IMAGES:
                    extension = ".png"

            archive_name = f"{index:04d}{extension}"

            # Image formats such as JPEG and WebP are already compressed.
            # Store their bytes directly instead of compressing them again.
            archive.writestr(
                archive_name,
                image_data,
                compress_type=ZIP_STORED,
            )
