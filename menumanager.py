from enum import Enum, auto


class AppTasks(Enum):
    TXT = ("my_txt_library/", "single_file_mp3_library/")
    EPUB = ("my_books_library/", "my_mp3_books_library/")
    PDF = ("my_books_library/", "my_mp3_books_library/", "PDF")
    LANGUAGE = auto()
    SPEEDRATE = auto()
    CLOSE = auto()


class MenuManager:
    def __init__(self):
        self.todolist = [("Read txt file", AppTasks.TXT), ("Read EPUB file", AppTasks.EPUB),
                         ("Read PDF file", AppTasks.PDF),
                         ("Choose language", AppTasks.LANGUAGE), ("Choose speed rate", AppTasks.SPEEDRATE),
                         ("Close\n", AppTasks.CLOSE)]

        self.keys_list = [_ for _ in range(len(self.todolist))]
        self.menu = {str(value + 1): self.todolist[value] for value in self.keys_list}

    def show_menu(self) -> Enum:
        print("\nWelcome to Text-Reader By - Souji21\n")
        for index in self.menu:
            print(f"{index}. {self.menu[index][0]}")

        choose = input("Make a selection: ")
        if not choose in self.menu:
            print("That option does not exist!")
            self.show_menu()
        else:
            return self.menu[choose][1]
