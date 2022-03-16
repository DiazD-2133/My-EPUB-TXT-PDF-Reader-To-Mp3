from abc import ABC, abstractmethod
import os

import zipfile

import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup


def get_index(file_dir):
    archive = zipfile.ZipFile(file_dir)
    web_page = archive.read("OEBPS/content.opf")
    soup = BeautifulSoup(web_page, "html.parser")
    contents = soup.find_all(name="itemref")
    book = {}
    for c in contents:
        book[c.get("idref").split(".")[0]] = ""
    return book


def get_item_name(name):
    item_name = ""
    if "/" in name:
        item_name = name.split("/")[1]
    item_name = item_name.split(".")[0]
    return item_name


class OpenFile(ABC):
    @abstractmethod
    def read_files(self, folder):
        pass


class ReadTxt(OpenFile):
    def __init__(self):
        self.files = []
        self.files_dict = {}

    def read_files(self, folder):
        self.files = os.listdir(folder)
        for file in self.files:
            file_dir = folder + file
            with open(file_dir, "r", encoding='utf-8') as data:
                text = data.read()

                file_name = file.split(".txt")[0]
                self.files_dict[file_name] = text

        return self.files_dict


class ReadEPUB(OpenFile):
    def __init__(self):
        self.files = []
        self.book = {}

        self.blacklist = ['[document]', 'noscript', 'header', 'html', 'meta', 'head', 'input', 'script']

    def chap2text(self, chap):
        output = ''
        soup = BeautifulSoup(chap, 'html.parser')
        text = soup.find_all(text=True)
        for t in text:
            if t.parent.name not in self.blacklist:
                output += '{} '.format(t)
        return output

    def read_files(self, folder):
        self.files = os.listdir(folder)
        for file in self.files:
            file_dir = folder + file
            file_name = file.split(".")[0]
            file_ext = file.split(".")[1]
            if file_ext == "epub":
                book = epub.read_epub(file_dir)

                self.book = get_index(file_dir)

                for item in book.get_items():
                    if item.get_type() == ebooklib.ITEM_DOCUMENT:
                        item_name = item.get_name()
                        item_name = get_item_name(item_name)
                        if item_name in self.book:
                            self.book[item_name] = self.chap2text(item.get_content())
                        else:
                            # Trying to fix some Sanderson´s books issues
                            item_name = f"x{item_name}"
                            self.book[item_name] = self.chap2text(item.get_content())

            return file_name, self.book
