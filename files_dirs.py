import os
import zipfile
from typing import List, Optional
from bs4 import BeautifulSoup


def get_files_names(directory: Optional[str] = None) -> List[str]:
    """
    Returns a list of files and directories in the given directory.
    If no directory is specified, lists contents of the current directory.
    """
    try:
        if directory:
            return os.listdir(directory)
        return os.listdir()
    except FileNotFoundError:
        print("Error: Directory not found at {}".format(directory))
        return []
    except OSError as e:
        print("Error listing directory {}: {}".format(directory, e))
        return []


def get_item_name(name: str) -> str:
    """Extracts the item name from a file path (removes directory and extension)."""
    if "/" in name:
        name = name.split("/")[-1]  # Get the last part after splitting by /
    item_name: str = name.split(".")[0]
    return item_name


def create_mp3_directory(base_mp3_dir: str, folder_name: str) -> str:
    """
    Creates a directory for MP3 files if it doesn't already exist.
    Returns the path to the created or existing directory.
    """
    full_path: str = os.path.join(base_mp3_dir, folder_name)
    try:
        if not os.path.exists(full_path):
            os.mkdir(full_path)
    except OSError as e:
        print("Error creating directory {}: {}".format(full_path, e))
        # Depending on desired behavior, you might want to return base_mp3_dir or raise the exception
        return os.path.join(base_mp3_dir, "") # Return base path if creation fails

    return os.path.join(full_path, "") # Ensure trailing slash for consistency


def get_opf(file_dir: str) -> Optional[BeautifulSoup]:
    """
    Extracts and parses the .opf file from an EPUB (zip archive).
    Returns a BeautifulSoup object or None if an error occurs.
    """
    try:
        with zipfile.ZipFile(file_dir, "r") as archive:
            opf_paths_to_try: List[str] = ["OEBPS/content.opf", "content.opf"]
            web_page_content: Optional[bytes] = None
            for opf_path in opf_paths_to_try:
                try:
                    web_page_content = archive.read(opf_path)
                    break  # Found and read the OPF file
                except KeyError:
                    continue  # Try the next path

            if web_page_content is None:
                print("Error: OPF file not found in EPUB: {}".format(file_dir))
                return None

            soup: BeautifulSoup = BeautifulSoup(web_page_content, "html.parser")
            return soup
    except FileNotFoundError:
        print("Error: EPUB file not found at {}".format(file_dir))
        return None
    except zipfile.BadZipFile:
        print("Error: Invalid or corrupted EPUB file: {}".format(file_dir))
        return None
    except Exception as e:
        print("An unexpected error occurred while processing EPUB {}: {}".format(file_dir, e))
        return None


def already_exists(book_name: str, mp3_library: List[str]) -> bool:
    """Checks if a book already exists in the MP3 library."""
    if book_name in mp3_library:
        print(
            "Book named = {} already exists in my_mp3_books_library!".format(
                book_name
            )
        )
        return True
    return False
