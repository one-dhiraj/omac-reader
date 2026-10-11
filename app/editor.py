from io import BytesIO

from PIL.ImageQt import ImageQt

from PySide6.QtGui import QIcon, QPixmap, QDropEvent

from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QAbstractItemView,
    QVBoxLayout,
    QPushButton,
    QMessageBox,
    QFileDialog,
)

from pathlib import Path
from PIL import Image
from PIL.ImageQt import ImageQt

class ReorderableListWidget(QListWidget):
    items_reordered = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # We handle reordering ourselves, without Qt drag-and-drop.
        self.setDragEnabled(False)
        self.setAcceptDrops(False)
        self.viewport().setAcceptDrops(False)

        self._pressed_item = None
        self._press_position = None
        self._is_reordering = False

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._pressed_item = self.itemAt(
                event.position().toPoint()
            )
            self._press_position = event.position().toPoint()
            self._is_reordering = False

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if (
            self._pressed_item is not None
            and event.buttons() & Qt.MouseButton.LeftButton
        ):
            distance = (
                event.position().toPoint()
                - self._press_position
            ).manhattanLength()

            if distance >= 10:
                self._is_reordering = True
                self.setCursor(Qt.CursorShape.ClosedHandCursor)

            if self._is_reordering:
                event.accept()
                return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if (
            event.button() == Qt.MouseButton.LeftButton
            and self._is_reordering
            and self._pressed_item is not None
        ):
            source_row = self.row(self._pressed_item)
            target_row = self.indexAt(
                event.position().toPoint()
            ).row()

            if target_row < 0:
                target_row = self.count() - 1

            if (
                source_row >= 0
                and target_row >= 0
                and source_row != target_row
            ):
                item = self.takeItem(source_row)
                self.insertItem(target_row, item)
                self.setCurrentItem(item)

                self.items_reordered.emit()

            self.unsetCursor()
            self._reset_drag_state()
            event.accept()
            return

        self._reset_drag_state()
        super().mouseReleaseEvent(event)

    def _reset_drag_state(self):
        self._pressed_item = None
        self._press_position = None
        self._is_reordering = False
        self.unsetCursor()

class PageEditor(QWidget):
    pages_reordered = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.pages = []

        title = QLabel("Page Editor")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.page_grid = ReorderableListWidget()
        self.page_grid.setViewMode(QListWidget.ViewMode.IconMode)
        self.page_grid.setResizeMode(QListWidget.ResizeMode.Adjust)

        self.page_grid.setMovement(QListWidget.Movement.Snap)
        self.page_grid.setWrapping(True)

        self.page_grid.setIconSize(QSize(120, 160))
        self.page_grid.setGridSize(QSize(150, 210))
        self.page_grid.setSpacing(8)

        self.page_grid.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
        )

        self.page_grid.items_reordered.connect(
            self._on_rows_moved
        )

        self.remove_button = QPushButton("Remove Selected Pages")
        self.remove_button.clicked.connect(self.remove_selected_pages)

        self.add_button = QPushButton("Add Pages")
        self.add_button.clicked.connect(self.add_pages)

        layout = QVBoxLayout(self)
        layout.addWidget(title)
        layout.addWidget(self.add_button)
        layout.addWidget(self.remove_button)
        layout.addWidget(self.page_grid)

    def set_pages(self, pages):
        self.pages = pages
        self.refresh_page_grid()

    def refresh_page_grid(self):
        self.page_grid.clear()

        for index, page in enumerate(self.pages):
            pixmap = QPixmap.fromImage(ImageQt(page["image"]))

            thumbnail = pixmap.scaled(
                QSize(120, 160),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

            item = QListWidgetItem(
                QIcon(thumbnail),
                f"Page {index + 1}\n{page['name']}",
            )

            item.setData(Qt.ItemDataRole.UserRole, page)
            item.setTextAlignment(Qt.AlignmentFlag.AlignHCenter)

            self.page_grid.addItem(item)

    
    def remove_selected_pages(self):
        selected_items = self.page_grid.selectedItems()

        if not selected_items:
            return

        selected_pages = [
            item.data(Qt.ItemDataRole.UserRole)
            for item in selected_items
        ]

        if len(selected_pages) >= len(self.pages):
            QMessageBox.information(
                self,
                "Cannot Remove Pages",
                "At least one page must remain in the comic.",
            )
            return

        for page in selected_pages:
            self.pages.remove(page)

        self.refresh_page_grid()
        self.pages_reordered.emit(self.pages.copy())

    
    def add_pages(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Add Pages",
            "",
            "Image Files (*.png *.jpg *.jpeg *.webp *.bmp *.gif);;All Files (*)",
        )

        if not file_paths:
            return

        added_pages = []
        failed_files = []

        for file_path in file_paths:
            try:
                image_data = Path(file_path).read_bytes()

                with Image.open(BytesIO(image_data)) as source:
                    source.load()

                    # Normalize the image mode for reliable display.
                    if "A" in source.getbands():
                        image = source.convert("RGBA")
                    else:
                        image = source.convert("RGB")

                added_pages.append({
                    "name": Path(file_path).name,
                    "image": image,
                    "data": image_data,
                })

            except (OSError, ValueError) as exc:
                failed_files.append(
                    f"{Path(file_path).name}: {exc}"
                )

        if not added_pages:
            QMessageBox.warning(
                self,
                "Unable to Add Pages",
                "None of the selected files could be opened as images.",
            )
            return

        # Append the new pages to the end of the current comic.
        self.pages.extend(added_pages)

        # Rebuild thumbnails with the updated page numbering.
        self.refresh_page_grid()

        # Notify main.py so the reader receives the new page list.
        self.pages_reordered.emit(self.pages.copy())

        if failed_files:
            QMessageBox.warning(
                self,
                "Some Images Were Skipped",
                f"Added {len(added_pages)} page(s).\n\n"
                + "\n".join(failed_files),
            )

    def _on_rows_moved(self, *args):
        reordered_pages = [
            self.page_grid.item(row).data(Qt.ItemDataRole.UserRole)
            for row in range(self.page_grid.count())
        ]

        self.pages = reordered_pages

        for index, page in enumerate(self.pages):
            self.page_grid.item(index).setText(
                f"Page {index + 1}\n{page['name']}"
            )

        self.pages_reordered.emit(self.pages.copy())