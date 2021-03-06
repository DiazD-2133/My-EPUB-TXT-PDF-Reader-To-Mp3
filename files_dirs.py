import os
import zipfile
from bs4 import BeautifulSoup


# Sometimes I'm not going to need any *args
def get_files_names(*args):
    if args:
        dirs_and_files = os.listdir(args[0])
    else:
        dirs_and_files = os.listdir()
    return dirs_and_files


def get_item_name(name):
    if "/" in name:
        name = name.split("/")[1]
    item_name = name.split(".")[0]
    return item_name


def create_mp3_directory(base_mp3_dir, folder_name):
    my_mp3_directories = os.listdir(base_mp3_dir)
    if not folder_name in my_mp3_directories:
        os.mkdir(f"{base_mp3_dir}{folder_name}")
    return base_mp3_dir + folder_name + "/"


def get_opf(file_dir):
    archive = zipfile.ZipFile(file_dir)

    # there are books that don't have .opf files in its folder
    try:
        web_page = archive.read("OEBPS/content.opf")
    except KeyError:
        web_page = archive.read("content.opf")

    soup = BeautifulSoup(web_page, "html.parser")

    return soup


def already_exists(book_name, mp3_library):
    if book_name in mp3_library:
        print(f"Book named = {book_name} already exists in my_mp3_books_library!")
    else:
        return False
