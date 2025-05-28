from enum import Enum, auto
from typing import Tuple, Dict, Any


class MenuOption(Enum):
    """Represents an option in the menu."""

    TXT = ("my_txt_library/", "single_file_mp3_library/")
    EPUB = ("my_books_library/", "my_mp3_books_library/")
    PDF = ("my_books_library/", "my_mp3_books_library/", "PDF")
    LANGUAGE = auto()
    SPEEDRATE = auto()
    CLOSE = auto()


class MenuManager:
    """Manages the application menu."""

    def __init__(self) -> None:
        self.menu_options: Dict[str, Tuple[str, MenuOption]] = {
            "1": ("Read TXT", MenuOption.TXT),
            "2": ("Read EPUB", MenuOption.EPUB),
            "3": ("Read PDF", MenuOption.PDF),
            "4": ("Choose language", MenuOption.LANGUAGE),
            "5": ("Choose speed rate", MenuOption.SPEEDRATE),
            "6": ("Close\n", MenuOption.CLOSE),
        }

    def show_menu(self) -> MenuOption:
        """Displays the menu and returns the user's selection."""
        print("\nWelcome to Text-Reader By - Deiker Diaz\n")
        for key, (description, _) in self.menu_options.items():
            print("{}. {}".format(key, description))

        while True:
            choice: str = input("Make a selection: ")
            if choice in self.menu_options:
                return self.menu_options[choice][1]
            else:
                print("Invalid option. Please try again.")
