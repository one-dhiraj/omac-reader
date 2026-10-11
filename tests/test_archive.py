from io import BytesIO
from zipfile import ZipFile

import pytest
from PIL import Image

from app.archive import load_cbz, save_cbz


def make_image_bytes(color="red", image_format="PNG"):
    """Create a small image in memory for testing."""
    buffer = BytesIO()

    image = Image.new("RGB", (10, 10), color=color)
    image.save(buffer, format=image_format)

    return buffer.getvalue()


def test_load_cbz_sorts_pages_naturally(tmp_path):
    comic_path = tmp_path / "comic.cbz"

    with ZipFile(comic_path, "w") as archive:
        archive.writestr("page10.png", make_image_bytes("blue"))
        archive.writestr("page2.png", make_image_bytes("green"))
        archive.writestr("page1.png", make_image_bytes("red"))

    pages = load_cbz(comic_path)

    assert [page["name"] for page in pages] == [
        "page1.png",
        "page2.png",
        "page10.png",
    ]


def test_load_cbz_rejects_invalid_archive(tmp_path):
    comic_path = tmp_path / "invalid.cbz"
    comic_path.write_text("This is not a ZIP archive.")

    with pytest.raises(ValueError, match="not a valid CBZ"):
        load_cbz(comic_path)


def test_load_cbz_rejects_archive_without_images(tmp_path):
    comic_path = tmp_path / "no_images.cbz"

    with ZipFile(comic_path, "w") as archive:
        archive.writestr("readme.txt", "No comic pages here.")

    with pytest.raises(ValueError, match="No supported image pages"):
        load_cbz(comic_path)


def test_save_cbz_preserves_image_bytes_and_page_order(tmp_path):
    source_path = tmp_path / "source.cbz"
    output_path = tmp_path / "saved.cbz"

    first_image = make_image_bytes("red")
    second_image = make_image_bytes("blue")

    with ZipFile(source_path, "w") as archive:
        archive.writestr("original1.png", first_image)
        archive.writestr("original2.png", second_image)

    pages = load_cbz(source_path)

    # Reverse the order before saving.
    pages.reverse()

    save_cbz(output_path, pages)

    with ZipFile(output_path, "r") as archive:
        names = archive.namelist()

        assert names == ["0001.png", "0002.png"]
        assert archive.read("0001.png") == second_image
        assert archive.read("0002.png") == first_image

    reopened_pages = load_cbz(output_path)

    assert [page["name"] for page in reopened_pages] == [
        "0001.png",
        "0002.png",
    ]


def test_save_cbz_rejects_empty_page_list(tmp_path):
    output_path = tmp_path / "empty.cbz"

    with pytest.raises(ValueError, match="no pages"):
        save_cbz(output_path, [])