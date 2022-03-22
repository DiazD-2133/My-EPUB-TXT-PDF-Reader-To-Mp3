import os
import textreader
from voicemanager import VoiceManager, Voice
from menumanager import MenuManager


project_dirs = textreader.get_names()

needed_folders = ["my_txt_library", "my_mp3_books_library", "single_file_mp3_library", "my_books_library"]
my_files_extension = ("TXT", "EPUB", "PDF")

for folder in needed_folders:
    if not folder in project_dirs:
        os.mkdir(f"{folder}")


reader = VoiceManager()
voice = Voice()
menu = MenuManager()


def read_files(ext, directory, base_mp3_dir):
    files_list = textreader.get_names(directory)
    if ext == "TXT":
        my_text = textreader.ReadTxt(files_list, base_mp3_dir)
        return my_text.read_files(directory)
    elif ext == "EPUB":
        my_text = textreader.ReadEPUB(files_list, base_mp3_dir)
        return my_text.read_files(directory)


def clean_book_content(book):
    empty_chapters = []
    for chapter in book:
        if len(book[chapter]) < 21:
            empty_chapters.append(chapter)
    for chapter in empty_chapters:
        book.pop(chapter)
    return book


def restart_app():
    print("Restarting...")
    os.system("python main.py")
    exit()


def create_mp3_directory(base_mp3_dir, folder_name):
    my_mp3_directories = os.listdir(base_mp3_dir)
    if not folder_name in my_mp3_directories:
        os.mkdir(f"{base_mp3_dir}{folder_name}")
    return base_mp3_dir + folder_name + "/"


def app():
    selection = menu.show_menu()

    if selection.name in my_files_extension:
        file_extension = selection.name
        temporal_book = None

        base_file_dir = selection.value[0]
        base_mp3_dir = selection.value[1]

        if file_extension == "TXT":
            temporal_book = read_files(file_extension, base_file_dir, base_mp3_dir)
            if temporal_book:
                voice.read(reader, file_extension, base_mp3_dir, temporal_book)
        elif file_extension == "EPUB":
            temporal_book = read_files(file_extension, base_file_dir, base_mp3_dir)
            book = temporal_book[1]
            if book:
                base_mp3_dir = create_mp3_directory(base_mp3_dir, temporal_book[0])
                book = clean_book_content(book)
                voice.read(reader, file_extension, base_mp3_dir, book)
            else:
                temporal_book = temporal_book[1]
        if not temporal_book:
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
