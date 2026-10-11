import os

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from io import BytesIO
from pathlib import Path

from PIL import Image
from PySide6.QtWidgets import QFileDialog, QMessageBox

from app.editor import PageEditor


def make_page(name, color="red"):
    """Create a sample page without needing an image file."""
    image = Image.new("RGB", (10, 10), color=color)

    buffer = BytesIO()
    image.save(buffer, format="PNG")

    return {
        "name": name,
        "image": image,
        "data": buffer.getvalue(),
    }


def test_remove_selected_pages(qtbot):
    editor = PageEditor()
    qtbot.addWidget(editor)

    editor.set_pages([
        make_page("page1.png"),
        make_page("page2.png", "green"),
        make_page("page3.png", "blue"),
    ])

    editor.page_grid.item(1).setSelected(True)

    editor.remove_selected_pages()

    assert [page["name"] for page in editor.pages] == [
        "page1.png",
        "page3.png",
    ]
    assert editor.page_grid.count() == 2


def test_cannot_remove_all_pages(qtbot, monkeypatch):
    editor = PageEditor()
    qtbot.addWidget(editor)

    editor.set_pages([
        make_page("page1.png"),
        make_page("page2.png", "blue"),
    ])

    # Prevent the test from opening a real message box.
    monkeypatch.setattr(
        QMessageBox,
        "information",
        lambda *args, **kwargs: QMessageBox.StandardButton.Ok,
    )

    for row in range(editor.page_grid.count()):
        editor.page_grid.item(row).setSelected(True)

    editor.remove_selected_pages()

    assert len(editor.pages) == 2
    assert editor.page_grid.count() == 2


def test_reorder_pages_updates_page_list(qtbot):
    editor = PageEditor()
    qtbot.addWidget(editor)

    editor.set_pages([
        make_page("page1.png"),
        make_page("page2.png", "green"),
        make_page("page3.png", "blue"),
    ])

    # Simulate a completed reorder in the thumbnail grid.
    item = editor.page_grid.takeItem(0)
    editor.page_grid.insertItem(2, item)

    editor._on_rows_moved()

    assert [page["name"] for page in editor.pages] == [
        "page2.png",
        "page3.png",
        "page1.png",
    ]


def test_add_pages(qtbot, tmp_path, monkeypatch):
    editor = PageEditor()
    qtbot.addWidget(editor)

    editor.set_pages([make_page("existing.png")])

    new_image_path = tmp_path / "new_page.png"
    Image.new("RGB", (10, 10), "blue").save(new_image_path)

    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileNames",
        lambda *args, **kwargs: ([str(new_image_path)], "Image Files"),
    )

    editor.add_pages()

    assert [page["name"] for page in editor.pages] == [
        "existing.png",
        "new_page.png",
    ]
    assert editor.page_grid.count() == 2
    assert editor.pages[-1]["data"] == Path(new_image_path).read_bytes()

def test_remove_pages_emits_updated_page_list(qtbot):
    editor = PageEditor()
    qtbot.addWidget(editor)

    editor.set_pages([
        make_page("page1.png"),
        make_page("page2.png", "green"),
        make_page("page3.png", "blue"),
    ])

    with qtbot.waitSignal(editor.pages_reordered, timeout=1000) as blocker:
        editor.page_grid.item(1).setSelected(True)
        editor.remove_selected_pages()

    emitted_pages = blocker.args[0]

    assert [page["name"] for page in emitted_pages] == [
        "page1.png",
        "page3.png",
    ]

def test_add_pages_emits_updated_page_list(qtbot, tmp_path, monkeypatch):
    editor = PageEditor()
    qtbot.addWidget(editor)

    editor.set_pages([make_page("existing.png")])

    new_image_path = tmp_path / "new_page.png"
    Image.new("RGB", (10, 10), "blue").save(new_image_path)

    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileNames",
        lambda *args, **kwargs: ([str(new_image_path)], "Image Files"),
    )

    with qtbot.waitSignal(editor.pages_reordered, timeout=1000) as blocker:
        editor.add_pages()

    emitted_pages = blocker.args[0]

    assert [page["name"] for page in emitted_pages] == [
        "existing.png",
        "new_page.png",
    ]

def test_reorder_pages_emits_updated_page_list(qtbot):
    editor = PageEditor()
    qtbot.addWidget(editor)

    editor.set_pages([
        make_page("page1.png"),
        make_page("page2.png", "green"),
        make_page("page3.png", "blue"),
    ])

    with qtbot.waitSignal(editor.pages_reordered, timeout=1000) as blocker:
        item = editor.page_grid.takeItem(0)
        editor.page_grid.insertItem(2, item)
        editor._on_rows_moved()

    emitted_pages = blocker.args[0]

    assert [page["name"] for page in emitted_pages] == [
        "page2.png",
        "page3.png",
        "page1.png",
    ]

def test_edit_and_save_comic_preserves_final_order_and_bytes(
    qtbot, tmp_path
):
    from app.archive import load_cbz, save_cbz
    from zipfile import ZipFile

    source_path = tmp_path / "original.cbz"
    output_path = tmp_path / "edited.cbz"

    # Create a comic with three pages.
    original_pages = [
        make_page("page1.png", "red"),
        make_page("page2.png", "green"),
        make_page("page3.png", "blue"),
    ]

    save_cbz(source_path, original_pages)

    # Load the comic as the application would.
    editor = PageEditor()
    qtbot.addWidget(editor)
    editor.set_pages(load_cbz(source_path))

    # Remove the second page.
    editor.page_grid.item(1).setSelected(True)
    editor.remove_selected_pages()

    # Move the remaining first page to the end.
    item = editor.page_grid.takeItem(0)
    editor.page_grid.insertItem(1, item)
    editor._on_rows_moved()

    # Save the edited comic.
    save_cbz(output_path, editor.pages)

    # Verify the saved archive.
    with ZipFile(output_path, "r") as archive:
        assert archive.namelist() == ["0001.png", "0002.png"]

    saved_pages = load_cbz(output_path)

    assert [page["name"] for page in saved_pages] == [
        "0001.png",
        "0002.png",
    ]

    # The original third page should now be first,
    # followed by the original first page.
    assert saved_pages[0]["data"] == original_pages[2]["data"]
    assert saved_pages[1]["data"] == original_pages[0]["data"]