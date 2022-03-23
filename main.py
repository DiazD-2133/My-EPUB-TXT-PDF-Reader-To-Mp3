import os

import textreader as reader_manager
import files_dirs as files_dirs_manager

from voicemanager import VoiceManager, Voice
from menumanager import MenuManager


project_dirs = files_dirs_manager.get_names()

needed_folders = ["my_txt_library", "my_mp3_books_library", "single_file_mp3_library", "my_books_library"]
my_files_extension = ("TXT", "EPUB", "PDF")

for folder in needed_folders:
    if not folder in project_dirs:
        os.mkdir(f"{folder}")


reader = VoiceManager()
voice = Voice()
menu = MenuManager()


def restart_app():
    print("Restarting...")
    os.system("python main.py")
    exit()


def app():
    selection = menu.show_menu()

    if selection.name in my_files_extension:
        file_extension = selection.name
        temporal_books_library = None

        base_file_dir = selection.value[0]
        base_mp3_dir = selection.value[1]

        if file_extension == "TXT":
            temporal_books_library = reader_manager.read_files(file_extension, base_file_dir, base_mp3_dir)
            if temporal_books_library:
                voice.read(reader, file_extension, base_mp3_dir, temporal_books_library)
        elif file_extension == "EPUB":
            temporal_books_library = reader_manager.read_files(file_extension, base_file_dir, base_mp3_dir)
            print(f"There are {len(temporal_books_library)} books to read!")
            for epub_book in temporal_books_library:
                base_mp3_dir = selection.value[1]
                book = epub_book[1]
                book = reader_manager.clean_book_content(book)
                if book:
                    base_mp3_dir = files_dirs_manager.create_mp3_directory(base_mp3_dir, epub_book[0])
                    voice.read(reader, file_extension, base_mp3_dir, book)
                else:
                    temporal_books_library = temporal_books_library[1]
        if not temporal_books_library:
            print("There are not files to read!")
            restart_app()
    elif selection.name == "LANGUAGE":
        reader.selectReaderLanguage()
    elif selection.name == "SPEEDRATE":
        reader.changeSpeedRate()
    elif selection.name == "RESET":
        restart_app()
    elif selection.name == "CLOSE":
        return
    app()

app()
