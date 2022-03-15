import os
from textreader import ReadTxt
from voicemanager import VoiceManager, Voice

project_dirs = os.listdir()

needed_folders = ["my_txt_library", "my_mp3_books_library", "single_file_mp3_library"]
for folder in needed_folders:
    if not folder in project_dirs:
        os.mkdir(f"{folder}")

txt_dir = "my_txt_library/"
single_file_mp3_library = "single_file_mp3_library/"

reader = VoiceManager()


def read_files(directory):
    my_text = ReadTxt()
    return my_text.read_files(directory)


def restart_app():
    print("Restarting...")
    os.system("python main.py")
    exit()


def my_menu():
    options = ("1", "2", "3", "4", "5")
    choose = input("\nWelcome to Text-Reader By - Souji21\n\n"
                   "1. Read a file txt\n"
                   "2. Choose language\n"
                   "3. Choose speed rate\n"
                   "4. Reset\n"
                   "5. Close\n\n"
                   "Make a selection: ")
    while not choose in options:
        print("\nWrong answer!\n")
        print("You must choose one of the enumerated options")
        choose = input("\nWelcome to Text-Reader By - Souji21\n\n"
                       "1. Read txt file\n"
                       "2. Choose language\n"
                       "3. Choose speed rate\n"
                       "4. Reset\n"
                       "5. Close\n\n"
                       "Make a selection: ")
    if choose == "1":
        my_files = read_files(txt_dir)
        if my_files:
            voice = Voice()
            voice.read_text(reader, single_file_mp3_library, my_files)
        else:
            print("There are not files to read!")
            restart_app()
    elif choose == "2":
        reader.selectReaderLanguage()
    elif choose == "3":
        reader.changeSpeedRate()
    elif choose == "4":
        restart_app()
    elif choose == "5":
        return
    my_menu()


my_menu()