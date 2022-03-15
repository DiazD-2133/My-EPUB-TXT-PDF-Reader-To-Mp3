from abc import ABC, abstractmethod
import os

import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup


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
        self.files_dict = {}

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
        cont = 0
        zeros = "000"
        # mark = ""
        for file in self.files:
            file_dir = folder + file
            file_name = file.split(".")[0]
            file_ext = file.split(".")[1]
            if file_ext == "epub":
                book = epub.read_epub(file_dir)

                chapters = []
                for item in book.get_items():
                    if item.get_type() == ebooklib.ITEM_DOCUMENT:
                        chapters.append(item.get_content())

                for chapter in chapters:
                    text = self.chap2text(chapter)

                    if cont > 100:
                        zeros = "0"
                    elif cont < 10:
                        zeros = "000"
                    elif cont > 9:
                        zeros = "00"

                    # mark += f"{zeros}{cont}" + "\n" + text

                    self.files_dict[f"{zeros}{cont} - {file_name}"] = text
                    cont += 1
                # with open(f"my_mp3_books_library/{file_name}.txt", mode="w") as new_book:
                #     new_book.write(mark)

            return file_name, self.files_dict



