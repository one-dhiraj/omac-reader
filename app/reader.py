from PIL.ImageQt import ImageQt

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QKeySequence, QPixmap, QShortcut
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
)


class ComicReader(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.pages = []
        self.current_page_index = 0

        self.image_label = QLabel("Open a comic to start reading.")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.previous_button = QPushButton("← Previous")
        self.previous_button.clicked.connect(self.previous_page)

        self.page_counter = QLabel("No pages loaded")
        self.page_counter.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.next_button = QPushButton("Next →")
        self.next_button.clicked.connect(self.next_page)

        navigation = QHBoxLayout()
        navigation.addWidget(self.previous_button)
        navigation.addStretch()
        navigation.addWidget(self.page_counter)
        navigation.addStretch()
        navigation.addWidget(self.next_button)

        layout = QVBoxLayout(self)
        layout.addWidget(self.image_label, 1)
        layout.addLayout(navigation)

        self._update_navigation()

    def _create_shortcuts(self):
        shortcuts = [
            (Qt.Key.Key_Left, self.previous_page),
            (Qt.Key.Key_Right, self.next_page),
            (Qt.Key.Key_Home, self.first_page),
            (Qt.Key.Key_End, self.last_page),
        ]

        self.shortcuts = []

        for key, callback in shortcuts:
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.setContext(
                Qt.ShortcutContext.WidgetWithChildrenShortcut
            )
            shortcut.activated.connect(callback)
            self.shortcuts.append(shortcut)

    def set_pages(self, pages, current_index=0):
        self.pages = pages

        if self.pages:
            self.current_page_index = max(
                0, min(current_index, len(self.pages) - 1)
            )
        else:
            self.current_page_index = 0

        self.show_page()

    def current_page(self):
        if not self.pages:
            return None

        return self.pages[self.current_page_index]

    def show_page(self):
        if not self.pages:
            self.image_label.setPixmap(QPixmap())
            self.image_label.setText("Open a comic to start reading.")
            self._update_navigation()
            return

        page = self.current_page()
        image = ImageQt(page["image"])
        pixmap = QPixmap.fromImage(image)

        self.image_label.setPixmap(
            pixmap.scaled(
                QSize(
                    max(1, self.image_label.width()),
                    max(1, self.image_label.height()),
                ),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

        self._update_navigation()

    def _update_navigation(self):
        has_pages = bool(self.pages)

        self.previous_button.setEnabled(
            has_pages and self.current_page_index > 0
        )
        self.next_button.setEnabled(
            has_pages
            and self.current_page_index < len(self.pages) - 1
        )

        if has_pages:
            self.page_counter.setText(
                f"Page {self.current_page_index + 1} "
                f"of {len(self.pages)}"
            )
        else:
            self.page_counter.setText("No pages loaded")

    def previous_page(self):
        if self.pages and self.current_page_index > 0:
            self.current_page_index -= 1
            self.show_page()

    def next_page(self):
        if self.pages and self.current_page_index < len(self.pages) - 1:
            self.current_page_index += 1
            self.show_page()

    def first_page(self):
        if self.pages:
            self.current_page_index = 0
            self.show_page()

    def last_page(self):
        if self.pages:
            self.current_page_index = len(self.pages) - 1
            self.show_page()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.show_page()