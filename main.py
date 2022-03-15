import os
import textreader
from voicemanager import VoiceManager, Voice
from menumanager import MenuManager

project_dirs = os.listdir()

needed_folders = ["my_txt_library", "my_mp3_books_library", "single_file_mp3_library", "my_books_library"]
for folder in needed_folders:
    if not folder in project_dirs:
        os.mkdir(f"{folder}")

files_extensions = ("TXT", "EPUB", "PDF")

reader = VoiceManager()
voice = Voice()


def read_files(ext, directory):
    if ext == "TXT":
        my_text = textreader.ReadTxt()
        return my_text.read_files(directory)
    elif ext == "EPUB":
        my_text = textreader.ReadEPUB()
        return my_text.read_files(directory)


def restart_app():
    print("Restarting...")
    os.system("python main.py")
    exit()


menu = MenuManager()


def app():
    selection = menu.show_menu()
    my_files = None

    if selection.name in files_extensions:
        base_txt_dir = selection.value[0]
        base_mp3_dir = selection.value[1]

        if selection.name == "TXT":
            my_files = read_files(selection.name, base_txt_dir)
            if my_files:
                voice.read_text(reader, base_mp3_dir, my_files)
        elif selection.name == "EPUB":
            my_files = read_files(selection.name, base_txt_dir)
            if my_files:
                voice.read_epub(reader, base_mp3_dir, my_files)
        if not my_files:
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
