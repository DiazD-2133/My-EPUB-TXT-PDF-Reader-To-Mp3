from abc import ABC, abstractmethod

from bs4 import BeautifulSoup

import ebooklib
from ebooklib import epub

from voicemanager import VoiceManager, Voice
import files_dirs as files_dirs_manager

reader = VoiceManager()
voice = Voice()


def clean_book_content(book):
    empty_chapters = []
    for chapter in book:
        if len(book[chapter]) < 30:
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
                print(f"File named = {mp3_file_name.split('.')[0]} already exists in single_file_mp3_library!")
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
    def get_epub_index(file_dir):
        index = files_dirs_manager.get_opf(file_dir)
        contents = index.find_all(name="itemref")

        new_chaps_list = []
        book = {}

        # Get order an id
        for content in contents:
            book[content.get("idref")] = ""

        # Get chaps name
        for book_chap in book:
            new_chap = index.find(id=f"{book_chap}")

            new_chap_name = new_chap.get("href").split(".")[0]
            if "/" in new_chap_name:
                new_chap_name = new_chap_name.split("/")[1]
            new_chaps_list.append(new_chap_name)

        book = {}
        for chap in new_chaps_list:
            book[chap] = ""
        return book

    def read_files(self, folder):
        books = []
        for file in self.files:
            book_name = file.split(".")[0]

            if book_name in self.mp3_files:
                print(f"File named = {book_name} already exists in my_mp3_books_library!")
            else:
                file_dir = folder + file
                file_ext = file.split(".")[1]
                if file_ext == "epub":
                    book = epub.read_epub(file_dir)

                    self.book = self.get_epub_index(file_dir)

                    for item in book.get_items():
                        if item.get_type() == ebooklib.ITEM_DOCUMENT:
                            item_name = item.get_name()
                            item_name = files_dirs_manager.get_item_name(item_name)
                            self.book[item_name] = self.clean(item.get_content())

                temporal_book = (book_name, self.book)
                books.append(temporal_book)

        return books


def get_temporal_books(selection):
    ext = selection.name

    directory = selection.value[0]
    base_mp3_dir = selection.value[1]

    files_list = files_dirs_manager.get_names(directory)
    if ext == "TXT":
        my_text = ReadTxt(files_list, base_mp3_dir)
        return my_text.read_files(directory)
    elif ext == "EPUB":
        my_text = ReadEPUB(files_list, base_mp3_dir)
        return my_text.read_files(directory)


def start_reading(temporal_books_library, selection):
    file_extension = selection.name
    base_mp3_dir = selection.value[1]

    if type(temporal_books_library) == list:
        print(f"There are {len(temporal_books_library)} books to read!")

        for epub_book in temporal_books_library:
            book = epub_book[1]
            book = clean_book_content(book)
            if book:
                base_mp3_dir = selection.value[1]
                base_mp3_dir = files_dirs_manager.create_mp3_directory(base_mp3_dir, epub_book[0])
                voice.read(reader, file_extension, base_mp3_dir, book)
    elif type(temporal_books_library) == dict:
        voice.read(reader, file_extension, base_mp3_dir, temporal_books_library)
