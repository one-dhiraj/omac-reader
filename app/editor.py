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
    QHBoxLayout,
    QPushButton,
    QMessageBox,
    QFileDialog,
    QProgressDialog
)

from pathlib import Path
from PIL import Image

from app.archive import load_page_thumbnail

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
        self.thumbnail_cache = {}

        self.page_info_label = QLabel("0 pages · 0 selected")
        self.page_info_label.setObjectName("page_info_label")
        self.page_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

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
        self.page_grid.itemSelectionChanged.connect(
            self._update_editor_status
        )

        self.remove_button = QPushButton("Remove Selected Pages")
        self.remove_button.clicked.connect(self.remove_selected_pages)
        self.remove_button.setEnabled(False)

        self.add_button = QPushButton("Add Pages")
        self.add_button.clicked.connect(self.add_pages)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.page_info_label)
        button_layout.addStretch()
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.remove_button)

        layout = QVBoxLayout(self)
        layout.addLayout(button_layout)
        layout.addWidget(self.page_grid)

    def _update_editor_status(self):
        page_count = len(self.pages)
        selected_count = len(self.page_grid.selectedItems())

        page_text = "page" if page_count == 1 else "pages"

        self.page_info_label.setText(
            f"{page_count} {page_text} · {selected_count} selected"
        )

        self.remove_button.setEnabled(selected_count > 0)

    def set_pages(self, pages):
        self.pages = pages
        self.thumbnail_cache.clear()
        return self.refresh_page_grid()

    def _create_page_item(self, page, index):
        page_id = id(page)

        if page_id not in self.thumbnail_cache:
            image = load_page_thumbnail(page)
            pixmap = QPixmap.fromImage(ImageQt(image))
            self.thumbnail_cache[page_id] = QIcon(pixmap)

        item = QListWidgetItem(
            self.thumbnail_cache[page_id],
            f"Page {index + 1}\n{page['name']}",
        )

        item.setData(Qt.ItemDataRole.UserRole, page)
        item.setTextAlignment(Qt.AlignmentFlag.AlignHCenter)

        return item


    def _update_page_labels(self):
        for index in range(self.page_grid.count()):
            page = self.page_grid.item(index).data(
                Qt.ItemDataRole.UserRole
            )

            self.page_grid.item(index).setText(
                f"Page {index + 1}\n{page['name']}"
            )

    def refresh_page_grid(self):
        self.page_grid.clear()

        if not self.pages:
            return True

        missing_thumbnails = any(
            id(page) not in self.thumbnail_cache
            for page in self.pages
        )

        progress = None
        items = []

        if missing_thumbnails:
            progress = QProgressDialog(
                "Preparing page thumbnails...",
                "Cancel",
                0,
                len(self.pages),
                self,
            )
            progress.setWindowTitle("Opening Editor")
            progress.setWindowModality(
                Qt.WindowModality.WindowModal
            )
            progress.setMinimumDuration(0)
            progress.setAutoClose(False)
            progress.setAutoReset(False)
            progress.show()

        try:
            for index, page in enumerate(self.pages):
                if progress is not None:
                    if progress.wasCanceled():
                        self.page_grid.clear()
                        return False

                    progress.setLabelText(
                        f"Preparing thumbnails: "
                        f"{index + 1} of {len(self.pages)}"
                    )

                item = self._create_page_item(page, index)
                items.append(item)

                if progress is not None:
                    progress.setValue(index + 1)

                    if progress.wasCanceled():
                        self.page_grid.clear()
                        return False

            # Populate the grid only after all items are prepared.
            for item in items:
                self.page_grid.addItem(item)

            self._update_editor_status()
            return True

        finally:
            if progress is not None:
                progress.close()
    
    def remove_selected_pages(self):
        selected_rows = sorted(
            {
                self.page_grid.row(item)
                for item in self.page_grid.selectedItems()
            },
            reverse=True,
        )

        if not selected_rows:
            return

        if len(selected_rows) >= len(self.pages):
            QMessageBox.information(
                self,
                "Cannot Remove Pages",
                "At least one page must remain in the comic.",
            )
            return

        for row in selected_rows:
            page = self.pages.pop(row)

            self.page_grid.takeItem(row)
            self.thumbnail_cache.pop(id(page), None)

        self._update_page_labels()
        self._update_editor_status()
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
        cancelled = False

        progress = QProgressDialog(
            "Preparing selected images...",
            "Cancel",
            0,
            len(file_paths),
            self,
        )
        progress.setWindowTitle("Adding Pages")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setWindowFlag(
            Qt.WindowType.WindowCloseButtonHint, False
        )
        progress.setMinimumDuration(0)
        progress.setAutoClose(False)
        progress.setAutoReset(False)

        try:
            for index, file_path in enumerate(file_paths):
                if progress.wasCanceled():
                    cancelled = True
                    break

                progress.setLabelText(
                    f"Preparing image {index + 1} of {len(file_paths)}:\n"
                    f"{Path(file_path).name}"
                )

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

                progress.setValue(index + 1)

                if progress.wasCanceled():
                    cancelled = True
                    break

        finally:
            progress.close()

        # Do not modify the comic if the user cancels.
        if cancelled:
            QMessageBox.information(
                self,
                "Adding Pages Cancelled",
                "The operation was cancelled. "
                "No selected pages were added.",
            )
            return

        if not added_pages:
            QMessageBox.warning(
                self,
                "Unable to Add Pages",
                "None of the selected files could be opened as images.",
            )
            return

        # Commit the prepared batch only after processing finishes.
        start_index = len(self.pages)
        self.pages.extend(added_pages)

        # Generate thumbnails only for the newly added pages.
        for offset, page in enumerate(added_pages):
            item = self._create_page_item(
                page,
                start_index + offset,
            )
            self.page_grid.addItem(item)

        self._update_page_labels()
        self._update_editor_status()

        # Notify main.py that the page list has changed.
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