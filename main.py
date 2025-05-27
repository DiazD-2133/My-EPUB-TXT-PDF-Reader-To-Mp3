import os
from typing import List, Union, Dict, Tuple, Optional 

import files_dirs as files_dirs_manager 
from voicemanager import VoiceManager
from menumanager import MenuManager, MenuOption
# Import necessary components from the refactored textreader
from textreader import TextFileReader, EpubFileReader, PdfFileReader, AbstractReader, clean_book_chapters


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

def run_app_cycle(
    menu_instance: MenuManager,
    voice_manager_instance: VoiceManager, 
) -> bool:
    """Runs a single cycle of the application menu and actions for CLI."""
    selection: MenuOption = menu_instance.show_menu()

    if selection.name in SUPPORTED_FILE_EXTENSIONS:
        input_dir: str = selection.value[0]
        # mp3_output_root_dir is where the "single_file_mp3_library" or "my_mp3_books_library/" is.
        mp3_output_root_dir: str = selection.value[1] 
        selected_file_type_name: str = selection.name 

        print(f"\nProcessing all {selected_file_type_name} files in directory: '{input_dir}'")
        
        try:
            files_in_dir = files_dirs_manager.get_files_names(input_dir)
            if not files_in_dir:
                print(f"No files found in '{input_dir}'.")
                return True 
        except Exception as e:
            print(f"Error listing files in '{input_dir}': {e}")
            return True 

        processed_any_file_successfully = False
        for file_name_from_dir in files_in_dir:
            full_file_path = os.path.join(input_dir, file_name_from_dir)
            
            file_base_name, file_ext_from_name = os.path.splitext(file_name_from_dir)
            
            if not (os.path.isfile(full_file_path) and \
                    file_ext_from_name.lower() == "." + selected_file_type_name.lower()):
                continue 

            print(f"\n--- Attempting to process: {file_name_from_dir} ---")

            reader: Optional[AbstractReader] = None
            # Reader's target_mp3_dir is where it checks for *already existing* outputs.
            reader_target_mp3_dir = mp3_output_root_dir 
            
            if selected_file_type_name == "TXT":
                reader = TextFileReader([file_name_from_dir], reader_target_mp3_dir)
            elif selected_file_type_name == "EPUB":
                reader = EpubFileReader([file_name_from_dir], reader_target_mp3_dir)
            elif selected_file_type_name == "PDF":
                reader = PdfFileReader([file_name_from_dir], reader_target_mp3_dir)
            
            if not reader: 
                print(f"Error: No reader configured for file type {selected_file_type_name}.")
                continue

            # input_folder for extract_book_content is the directory where the file resides.
            extracted_data = reader.extract_book_content(input_folder=input_dir)

            # Handle "skipped" or no content
            is_skipped = False
            if isinstance(extracted_data, dict) and "skipped" in extracted_data: # For TXT
                print(extracted_data["skipped"]) 
                is_skipped = True
            elif isinstance(extracted_data, list) and extracted_data and isinstance(extracted_data[0], dict) and "skipped" in extracted_data[0]: # For EPUB/PDF
                 print(extracted_data[0]["skipped"])
                 is_skipped = True
            if is_skipped:
                continue 
            
            if not extracted_data: 
                print(f"No content extracted from '{file_name_from_dir}' or file is empty/unsupported.")
                continue
            
            text_content_map: Dict[str, str] = {}
            actual_mp3_output_for_book = mp3_output_root_dir # Default for TXT files
            
            if selected_file_type_name == "TXT":
                if isinstance(extracted_data, dict): # Expected: {"book_name_base": "content"}
                    text_content_map = extracted_data
                else:
                    print(f"Error: Unexpected data structure from TextFileReader for {file_name_from_dir}.")
                    continue
            elif selected_file_type_name in ["EPUB", "PDF"]:
                if isinstance(extracted_data, list) and extracted_data: # Expected: [("slug", {chapters})]
                    book_name_slug, chapters_map = extracted_data[0]
                    text_content_map = clean_book_chapters(chapters_map) 
                    actual_mp3_output_for_book = os.path.join(mp3_output_root_dir, book_name_slug)
                    try:
                        if not os.path.exists(actual_mp3_output_for_book):
                           os.makedirs(actual_mp3_output_for_book, exist_ok=True)
                           print(f"Created MP3 output directory: {actual_mp3_output_for_book}")
                    except OSError as e:
                        print(f"Error creating MP3 subfolder '{actual_mp3_output_for_book}': {e}")
                        continue 
                else:
                    print(f"Error: No processable content structure from {file_name_from_dir} for {selected_file_type_name}.")
                    continue
            
            if not text_content_map: 
                print(f"No text found to convert for {file_name_from_dir} after processing.")
                continue

            print(f"Starting audio generation for {file_name_from_dir} -> {actual_mp3_output_for_book}")
            try:
                voice_manager_instance.generate_speech_audio(
                    text_content_map,
                    actual_mp3_output_for_book,
                    selected_file_type_name.lower(), 
                    info_items=None 
                )
                processed_any_file_successfully = True
                print(f"--- Finished processing {file_name_from_dir} ---")
            except Exception as e_tts:
                print(f"Error during TTS for {file_name_from_dir}: {e_tts}")
        
        if not processed_any_file_successfully:
             print(f"No {selected_file_type_name} files were processed successfully in '{input_dir}'.")
        return True 

    elif selection == MenuOption.LANGUAGE: 
        voice_manager_instance.select_language_cli()
        return True 
    elif selection == MenuOption.SPEEDRATE: 
        voice_manager_instance.change_speed_rate_cli()
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
    menu: MenuManager = MenuManager()

    app_active: bool = True
    while app_active:
        app_active = run_app_cycle(menu, voice_manager)
