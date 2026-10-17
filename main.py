import sys
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QProgressDialog,
    QSizePolicy,
    QStackedWidget,
    QToolBar,
    QToolButton,
    QWidget
)
from PySide6.QtGui import QAction, QIcon
from PySide6.QtCore import Qt
from app.archive import (
    load_comic,
    save_cbz,
    SaveCancelledError,
)
from app.reader import ComicReader
from app.editor import PageEditor
from app.style import apply_app_style

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        icon_path = (
            Path(__file__).resolve().parent
            / "assets"
            / "omac-reader.png"
        )
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setWindowTitle("OMAC Reader")
        self.setWindowIcon(QIcon(str(icon_path)))

        self.current_file = None
        self.comic_pages = []
        self.has_unsaved_changes = False
        self.editor_loaded = False

        self.create_actions()
        self.create_views()
        self.create_toolbar()

        self.statusBar().showMessage("Ready")
    
    def create_navigation_shortcuts(self):
        shortcuts = [
            ("Left", self.reader.previous_page),
            ("Right", self.reader.next_page),
            ("Home", self.reader.first_page),
            ("End", self.reader.last_page),
        ]

        for key, callback in shortcuts:
            action = QAction(key, self)
            action.setShortcut(key)
            action.setShortcutContext(
                Qt.ShortcutContext.WindowShortcut
            )
            action.triggered.connect(
                lambda checked=False, cb=callback: (
                    cb()
                    if self.pages_view.currentWidget() is self.reader
                    else None
                )
            )
            self.addAction(action)

    def create_actions(self):
        self.open_action = QAction("Open Comic", self)
        self.open_action.setShortcut("Ctrl+O")
        self.open_action.setToolTip("Ctrl+O")
        self.open_action.triggered.connect(self.open_comic)

        self.reader_action = QAction("Reader", self)
        self.reader_action.setShortcut("Alt+R")
        self.reader_action.setToolTip("Alt+R")
        self.reader_action.setCheckable(True)
        self.reader_action.setChecked(True)
        self.reader_action.triggered.connect(
            lambda: self.switch_mode(0)
        )

        self.editor_action = QAction("Page Editor", self)
        self.editor_action.setShortcut("Alt+E")
        self.editor_action.setToolTip("Alt+E")
        self.editor_action.setCheckable(True)
        self.editor_action.triggered.connect(
            lambda: self.switch_mode(1)
        )

        self.save_as_action = QAction("Save As...", self)
        self.save_as_action.setShortcut("Ctrl+Shift+S")
        self.save_as_action.setToolTip("Ctrl+Shift+S")
        self.save_as_action.triggered.connect(self.save_comic_as)
        self.save_as_action.setEnabled(False)

    def create_views(self):
        self.pages_view = QStackedWidget()

        self.reader = ComicReader()
        self.editor = PageEditor()
        self.create_navigation_shortcuts()

        self.editor.pages_reordered.connect(
            self.on_pages_reordered
        )

        self.pages_view.addWidget(self.reader)
        self.pages_view.addWidget(self.editor)

        self.setCentralWidget(self.pages_view)

    def create_toolbar(self):
        toolbar = QToolBar("Main Toolbar", self)
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        toolbar.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonTextOnly
        )
        toolbar.setContextMenuPolicy(
            Qt.ContextMenuPolicy.PreventContextMenu
        )
        self.addToolBar(toolbar)

        toolbar.addAction(self.open_action)
        toolbar.addAction(self.save_as_action)
        toolbar.addSeparator()
        toolbar.addAction(self.reader_action)
        toolbar.addAction(self.editor_action)
        
        # Add an expanding spacer to push everything following it to the right side
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)
        
        # Create the close button
        self.close_btn = QToolButton(self)
        self.close_btn.setObjectName("toolbar_close_button") # Target object name for QSS styling
        self.close_btn.setText("✕")                           # Clean text cross symbol
        self.close_btn.setToolTip("Close Application")
        
        # Connect click to the window's close slot
        self.close_btn.clicked.connect(self.close)
        
        toolbar.addWidget(self.close_btn)
    
    def switch_mode(self, index):
        self.pages_view.setCurrentIndex(index)

        self.reader_action.setChecked(index == 0)
        self.editor_action.setChecked(index == 1)

        self.statusBar().showMessage(
            "Reader mode" if index == 0 else "Page editor mode"
        )

        if index == 1 and not self.editor_loaded:
            self.editor_loaded = self.editor.set_pages(self.comic_pages)

            if not self.editor_loaded:
                self.switch_mode(0)
                return

    def open_comic(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Comic",
            "",
            "Comic Files (*.cbz *.cbr);;CBZ Files (*.cbz);;CBR Files (*.cbr);;All Files (*)",
        )

        if not file_path:
            return

        # Load first, so an invalid archive cannot replace the current comic.
        try:
            loaded_pages = load_comic(file_path)
        except (OSError, ValueError) as exc:
            QMessageBox.critical(
                self,
                "Unable to open comic",
                str(exc),
            )
            return

        # Protect edits to the currently open comic.
        if not self.confirm_unsaved_changes():
            return

        self.current_file = file_path
        self.comic_pages = loaded_pages
        self.has_unsaved_changes = False

        self.save_as_action.setEnabled(True)

        self.reader.set_pages(self.comic_pages)
        self.editor.pages = self.comic_pages
        self.editor_loaded = False
        self.editor.page_grid.clear()

        self.set_unsaved_changes(False)
        self.switch_mode(0)

        self.statusBar().showMessage(
            f"Loaded {len(self.comic_pages)} pages"
        )

    def on_pages_reordered(self, reordered_pages):
        # Preserve the page currently displayed by the reader.
        current_page = self.reader.current_page()

        self.comic_pages = reordered_pages

        new_index = next(
            (
                index
                for index, page in enumerate(self.comic_pages)
                if page is current_page
            ),
            0,
        )

        self.reader.set_pages(self.comic_pages, new_index)

        self.statusBar().showMessage(
            f"{len(self.comic_pages)} pages — order updated"
        )

        self.set_unsaved_changes(True)

    def set_unsaved_changes(self, unsaved):
        self.has_unsaved_changes = unsaved

        filename = (
            Path(self.current_file).name
            if self.current_file
            else "Untitled"
        )

        marker = " *" if unsaved else ""
        # self.setWindowTitle(f"OMAC Reader — {filename}{marker}")

    def confirm_unsaved_changes(self):
        if not self.has_unsaved_changes:
            return True

        choice = QMessageBox.question(
            self,
            "Unsaved Changes",
            "You have unsaved changes. Do you want to save them?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save,
        )

        if choice == QMessageBox.StandardButton.Save:
            return self.save_comic_as()

        if choice == QMessageBox.StandardButton.Discard:
            return True

        return False
    
    
    def save_comic_as(self):
        if not self.comic_pages:
            QMessageBox.warning(
                self,
                "Nothing to Save",
                "Open a comic before saving.",
            )
            return False

        if self.has_unsaved_changes == False:
                    QMessageBox.warning(
                        self,
                        "Nothing to Save",
                        "Make some changes before saving.",
                    )
                    return False

        if self.current_file:
            default_name = (
                f"{Path(self.current_file).stem}_edited.cbz"
            )
        else:
            default_name = "untitled.cbz"

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Comic As",
            default_name,
            "Comic Book ZIP (*.cbz)",
        )

        if not file_path:
            return False

        if Path(file_path).suffix.lower() != ".cbz":
            file_path += ".cbz"

        progress = QProgressDialog(
            "Preparing to save comic...",
            "Cancel",
            0,
            len(self.comic_pages),
            self,
        )
        progress.setWindowTitle("Saving Comic")
        progress.setWindowModality(
            Qt.WindowModality.WindowModal
        )
        progress.setMinimumDuration(0)
        progress.setAutoClose(False)
        progress.setAutoReset(False)

        def update_progress(current, total):
            progress.setLabelText(
                f"Saving page {current} of {total}..."
            )
            progress.setValue(current)

        progress.show()

        try:
            save_cbz(
                file_path,
                self.comic_pages,
                progress_callback=update_progress,
                cancel_check=progress.wasCanceled,
            )

        except SaveCancelledError:
            self.statusBar().showMessage("Saving cancelled")

            QMessageBox.information(
                self,
                "Saving Cancelled",
                "The save operation was cancelled. "
                "Your unsaved changes have been preserved.",
            )
            return False

        except Exception as exc:
            QMessageBox.critical(
                self,
                "Unable to Save Comic",
                f"The comic could not be saved:\n{exc}",
            )
            return False

        finally:
            progress.close()

        self.current_file = file_path
        self.set_unsaved_changes(False)

        self.statusBar().showMessage(
            f"Saved {len(self.comic_pages)} pages to "
            f"{Path(file_path).name}"
        )

        return True

    def closeEvent(self, event):
        if self.confirm_unsaved_changes():
            event.accept()
        else:
            event.ignore()

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("OMAC Reader")
    app.setDesktopFileName("omac-reader")
    apply_app_style(app)
    icon_path = (
        Path(__file__).resolve().parent
        / "assets"
        / "omac-reader.png"
    )
    app.setWindowIcon(QIcon(str(icon_path)))

    window = MainWindow()
    window.showMaximized()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()