# OMAC Reader

**One More Amazing Comic Reader** is a lightweight, open-source desktop application for reading and organizing comic book archives on Linux.

OMAC Reader is built with Python, PySide6, and Pillow. It supports opening CBZ archives, navigating comic pages, and editing the page order before saving the archive.

## Features

- **CBZ support:** Open comic book archives (`.cbz`).
- **Comic reader:** Navigate pages using keyboard shortcuts.
- **Page editor:** View comic pages in a thumbnail grid.
- **Reorder pages:** Drag and reorder pages to change their sequence.
- **Multi-select:** Select multiple pages for editing.
- **Add pages:** Import supported image files into a comic.
- **Remove pages:** Remove unwanted pages from an archive.
- **Save As:** Export your edited comic as a new CBZ archive.
- **Archive preservation:** Preserve original image data when saving, avoiding unnecessary image re-encoding.

### Supported image formats

JPG, JPEG, PNG, WebP, BMP, and GIF.

## Requirements

- Python 3
- pip
- A Linux desktop environment

## Installation

Clone the repository:

```bash
mkdir omac-reader
cd omac-reader
git clone https://github.com/one-dhiraj/omac-reader.git .
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Running the application

From the project directory, with the virtual environment activated:

```bash
python main.py
```

## Usage

1. Open a CBZ comic archive.
2. Read and navigate through its pages.
3. Open the page editor to organize the comic.
4. Select, reorder, add, or remove pages as needed.
5. Use **Save As** to export the edited comic to a CBZ archive.

Your edits remain in memory until you save them. Keep a backup of important comics before editing.

## Project structure

```text
omac-reader/
├── main.py
├── requirements.txt
└── app/
    ├── __init__.py
    ├── archive.py
    ├── reader.py
    └── editor.py
```

## Roadmap

- [ ] Add unsaved-changes warnings
- [ ] UI Design improvments
- [ ] Package the application for easier installation on Linux
- [ ] Explore support for additional comic archive formats

## License

OMAC Reader is intended to be free and open-source software. See [LICENSE](LICENSE) for the applicable license terms.

## Disclaimer

OMAC Reader is an independent project and is not affiliated with or endorsed by DC Comics or any other comic publisher. Comic files used with the application remain the responsibility of their respective owners.