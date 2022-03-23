from abc import ABC, abstractmethod

import zipfile
from bs4 import BeautifulSoup

import ebooklib
from ebooklib import epub

import files_dirs as files_dirs_manager


def clean_book_content(book):
    empty_chapters = []
    for chapter in book:
        if len(book[chapter]) < 21:
            empty_chapters.append(chapter)
    for chapter in empty_chapters:
        book.pop(chapter)
    return book


class OpenFile(ABC):
    @abstractmethod
    def read_files(self, folder):
        pass


class ReadTxt(OpenFile):
    def __init__(self, files_list, mp3_dir):
        self.files = files_list
        self.files_dict = {}
        self.mp3_files = files_dirs_manager.get_names(mp3_dir)

    def read_files(self, folder):
        for file in self.files:
            mp3_file_name = file.replace(".txt", ".mp3")
            if mp3_file_name in self.mp3_files:
                print(f"File named = {mp3_file_name.split('.')[0]} already exists!")
            else:

                file_dir = folder + file
                with open(file_dir, "r", encoding='utf-8') as data:
                    text = data.read()

                    file_name = file.split(".")[0]
                    self.files_dict[file_name] = text

        return self.files_dict


class ReadEPUB(OpenFile):
    def __init__(self, files_list, mp3_dir):
        self.files = files_list
        self.book = {}
        self.mp3_files = files_dirs_manager.get_names(mp3_dir)

        self.blacklist = ['[document]', 'noscript', 'header', 'html', 'meta', 'head', 'input', 'script']

    def clean(self, chap):
        output = ''
        soup = BeautifulSoup(chap, 'html.parser')
        text = soup.find_all(text=True)
        for t in text:
            if t.parent.name not in self.blacklist:
                output += '{} '.format(t)
        return output

    @staticmethod
    def get_epub_index(file_dir, chaps_list):
        archive = zipfile.ZipFile(file_dir)
        new_chaps_list = []

        try:
            web_page = archive.read("OEBPS/content.opf")
        except KeyError:
            web_page = archive.read("content.opf")

        soup = BeautifulSoup(web_page, "html.parser")
        contents = soup.find_all(name="itemref")

        book = {}
        for content in contents:
            book[content.get("idref").split(".")[0]] = ""

        # Some books doesn't have the same idref-html name
        for book_chap in book:
            if book_chap not in chaps_list:
                new_chap = soup.find(id=f"{book_chap}")
                new_chaps_list.append(new_chap.get("href").split(".")[0])
        if new_chaps_list:
            for chap in new_chaps_list:
                book[chap] = ""
        return book

    def read_files(self, folder):
        books = []
        for file in self.files:
            book_name = file.split(".")[0]

            if book_name in self.mp3_files:
                print(f"File named = {book_name} already exists")
            else:
                file_dir = folder + file
                file_ext = file.split(".")[1]
                if file_ext == "epub":
                    book = epub.read_epub(file_dir)
                    item_names = []

                    for item in book.get_items():
                        if item.get_type() == ebooklib.ITEM_DOCUMENT:
                            item_name = files_dirs_manager.get_item_name(item.get_name())
                            item_names.append(item_name)

                    self.book = self.get_epub_index(file_dir, item_names)

                    for item in book.get_items():
                        if item.get_type() == ebooklib.ITEM_DOCUMENT:
                            item_name = item.get_name()
                            item_name = files_dirs_manager.get_item_name(item_name)
                            if item_name in self.book:
                                self.book[item_name] = self.clean(item.get_content())
                            else:
                                # Trying to fix some Sanderson´s books issues
                                item_name = f"x{item_name}"
                                self.book[item_name] = self.clean(item.get_content())

                temporal_book = (book_name, self.book)
                books.append(temporal_book)

        return books


def read_files(ext, directory, base_mp3_dir):
    files_list = files_dirs_manager.get_names(directory)
    if ext == "TXT":
        my_text = ReadTxt(files_list, base_mp3_dir)
        return my_text.read_files(directory)
    elif ext == "EPUB":
        my_text = ReadEPUB(files_list, base_mp3_dir)
        return my_text.read_files(directory)
