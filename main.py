import os
from typing import List, Union, Dict, Tuple

import textreader as reader_manager
import files_dirs as files_dirs_manager

from voicemanager import VoiceManager, Voice
from menumanager import MenuManager, MenuOption


# --- Constants ---
NEEDED_FOLDERS: List[str] = [
    "my_txt_library",
    "my_mp3_books_library",
    "single_file_mp3_library",
    "my_books_library",
]
SUPPORTED_FILE_EXTENSIONS: tuple[str, str, str] = ("TXT", "EPUB", "PDF")


# --- Initialization Functions ---
def create_initial_folders() -> None:
    """Creates necessary application folders if they don't exist."""
    project_dirs: List[str] = files_dirs_manager.get_files_names()
    for folder_name in NEEDED_FOLDERS:
        if folder_name not in project_dirs:
            try:
                os.mkdir(folder_name)
                print("Created directory: {}".format(folder_name))
            except OSError as e:
                print("Error creating directory {}: {}".format(folder_name, e))


# --- Core Application Logic ---
def handle_file_reading(
    selection: MenuOption, voice_instance: Voice, voice_manager_instance: VoiceManager
) -> None:
    """Handles the process of reading a selected file type."""
    temporal_books_library: Union[
        Dict[str, str], List[Tuple[str, Dict[str, str]]], None
    ] = reader_manager.get_temporal_books(selection)

    if not temporal_books_library:
        print("There are no files to read for the selected type or an error occurred.")
        return

    reader_manager.start_reading(
        voice_instance, voice_manager_instance, temporal_books_library, selection
    )


def run_app_cycle(
    menu_instance: MenuManager,
    voice_instance: Voice,
    voice_manager_instance: VoiceManager,
) -> bool:
    """Runs a single cycle of the application menu and actions."""
    selection: MenuOption = menu_instance.show_menu()

    if selection.name in SUPPORTED_FILE_EXTENSIONS:
        handle_file_reading(selection, voice_instance, voice_manager_instance)
        return True  # Continue running
    elif selection == MenuOption.LANGUAGE: # Compare with Enum member directly
        voice_manager_instance.select_language()
        return True  # Continue running
    elif selection == MenuOption.SPEEDRATE: # Compare with Enum member directly
        voice_manager_instance.change_speed_rate()
        return True  # Continue running
    elif selection == MenuOption.CLOSE: # Compare with Enum member directly
        print("Exiting application...")
        return False  # Stop running
    else:
        # This case should ideally not be reached if menu.show_menu() is robust
        print("Unknown selection. Please try again.")
        return True # Continue running, allow user to retry


# --- Main Execution ---
if __name__ == "__main__":
    create_initial_folders()

    # Initialize core components
    voice_manager: VoiceManager = VoiceManager()
    voice: Voice = Voice()
    menu: MenuManager = MenuManager()

    app_active: bool = True
    while app_active:
        app_active = run_app_cycle(menu, voice, voice_manager)
