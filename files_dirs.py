import os


def get_names(*args):
    if args:
        dirs_and_files = os.listdir(args[0])
    else:
        dirs_and_files = os.listdir()
    return dirs_and_files


def get_item_name(name):
    if "/" in name:
        name = name.split("/")[1]
    item_name = name.split(".")[0]
    return item_name


def create_mp3_directory(base_mp3_dir, folder_name):
    my_mp3_directories = os.listdir(base_mp3_dir)
    if not folder_name in my_mp3_directories:
        os.mkdir(f"{base_mp3_dir}{folder_name}")
    return base_mp3_dir + folder_name + "/"
