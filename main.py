import os

import textreader as reader_manager
import files_dirs as files_dirs_manager

from voicemanager import VoiceManager, Voice
from menumanager import MenuManager


project_dirs = files_dirs_manager.get_files_names()

needed_folders = ["my_txt_library", "my_mp3_books_library", "single_file_mp3_library", "my_books_library"]
my_files_extension = ("TXT", "EPUB", "PDF")

for folder in needed_folders:
    if not folder in project_dirs:
        os.mkdir(f"{folder}")


reader = VoiceManager()
voice = Voice()
menu = MenuManager()


def app():
    selection = menu.show_menu()

    if selection.name in my_files_extension:
        temporal_books_library = reader_manager.get_temporal_books(selection)

        if not temporal_books_library:
            print("There are not files to read!")
            return True
        reader_manager.start_reading(voice, reader, temporal_books_library, selection)
    elif selection.name == "LANGUAGE":
        reader.select_language()
    elif selection.name == "SPEEDRATE":
        reader.change_speedRate()
    elif selection.name == "CLOSE":
        return False

    return True

run = True

while run:
    run = app()
