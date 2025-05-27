import os
import flet as ft

from flet import (
    FilePicker,
    FilePickerResultEvent,
    Row,
    Container,
    ElevatedButton,
    ListView,
    Text,
    ProgressRing,
    icons
)

from configs import AppData

# Updated imports for refactored backend
from textreader import process_file_for_ui 
from voicemanager import VoiceManager


def main(page: ft.Page):
    data = AppData()
    my_mp3_directories = os.listdir()
    if not "mp3_books_library" in my_mp3_directories:
        os.mkdir(f"mp3_books_library")

    # Save audios dir
    def get_directory_result(e: FilePickerResultEvent):
        directory_path.value = e.path if e.path else data.data["mp3_directory"]
        data.data["mp3_directory"] = directory_path.value
        data.save_changes(data.data)
        directory_path.update()

    get_directory_dialog = FilePicker(on_result=get_directory_result)
    directory_path = Text(max_lines=5, width=210, value=data.data["mp3_directory"])

    # Files to read
    def pick_files_result(e: FilePickerResultEvent):
        if e.files:
            selected_files.value = e.files[0].path
            selected_file_name.value = e.files[0].name
            selected_files.update()
            selected_file_name.update()
            no_selected_files.value = "" # Clear any previous "no file selected" message
            no_selected_files.update()


    pick_files_dialog = FilePicker(on_result=pick_files_result)

    selected_files = Text(max_lines=5, width=210, value="No file selected.") # Initial placeholder
    selected_file_name = Text(visible=False) # Stores the actual name for backend processing

    # UI elements for feedback
    no_selected_files = Text(color=ft.colors.RED) # For error messages like "Please select a file"
    audio_files = ListView(expand=1, spacing=10, padding=20, auto_scroll=True)
    state_info = Text("Idle", visible=True) # Start with "Idle"
    progress_ring = ProgressRing(width=16, height=16, stroke_width=2, visible=False)
    items_to_read = Text(visible=True) # To show "Reading X/Y" or "Processing..."

    info_items = {
        "audio_files_list": audio_files,
        "state_info": state_info,
        "progress_ring": progress_ring,
        "items_to_read": items_to_read,
    }

    def reset_ui_feedback_elements():
        """Helper to reset UI elements related to processing feedback."""
        info_items["state_info"].value = "Idle"
        info_items["progress_ring"].visible = False
        info_items["items_to_read"].value = ""
        # Do not clear audio_files_list here, it's cleared at the start of init_reading if needed
        info_items["state_info"].update()
        info_items["progress_ring"].update()
        info_items["items_to_read"].update()


    def init_reading(e):
        # 1. Clear previous results from the list view
        if info_items["audio_files_list"].controls:
            info_items["audio_files_list"].controls.clear()
            info_items["audio_files_list"].update()

        # 2. Validate input
        if not selected_files.value or selected_files.value == "No file selected.":
            no_selected_files.value = "You must select a file first!"
            no_selected_files.update()
            reset_ui_feedback_elements() # Reset other feedback elements
            return

        no_selected_files.value = "" # Clear error message
        no_selected_files.update()

        file_path = selected_files.value
        file_name = selected_file_name.value # This should be set by pick_files_result
        mp3_dir = directory_path.value

        if not file_name: # Should not happen if pick_files_result is working
            no_selected_files.value = "Error: File name is missing."
            no_selected_files.update()
            reset_ui_feedback_elements()
            return

        # 3. Update UI to show processing started
        info_items["state_info"].value = "Initializing..."
        info_items["progress_ring"].visible = True
        info_items["items_to_read"].value = "Preparing to read..."
        info_items["state_info"].update()
        info_items["progress_ring"].update()
        info_items["items_to_read"].update()
        page.update() # Ensure immediate UI update

        try:
            # Instantiate the refactored VoiceManager
            voice_manager_instance = VoiceManager()

            # Check if VoiceManager initialized correctly (engine is available)
            if not voice_manager_instance.engine or not voice_manager_instance.current_voice:
                error_msg = "Voice engine failed. Check installation or voice settings."
                print(f"flet-app.py: {error_msg}") # Log for debugging
                info_items["state_info"].value = error_msg
                info_items["progress_ring"].visible = False
                info_items["items_to_read"].value = "" # Clear any "Preparing..." message
                info_items["state_info"].update()
                info_items["progress_ring"].update()
                info_items["items_to_read"].update()
                page.update()
                return

            # Call the new textreader function (process_file_for_ui)
            # This function will internally call voice_manager_instance.generate_speech_audio
            # and handle its own UI updates via info_items for the TTS part.
            process_file_for_ui(
                file_path, 
                file_name, 
                mp3_dir,  # This is mp3_output_root_dir for process_file_for_ui
                voice_manager_instance, 
                info_items
            )
            # Note: process_file_for_ui and generate_speech_audio should handle 
            # hiding the progress ring and setting final messages in info_items.
            # If they don't, a final reset might be needed here, but ideally, they manage their full lifecycle.

        except Exception as ex:
            print(f"An unexpected error occurred in init_reading: {ex}")
            # Update UI to reflect the error
            if info_items.get("state_info"):
                info_items["state_info"].value = f"An unexpected error occurred: {ex}"
                info_items["state_info"].update()
            if info_items.get("progress_ring"):
                info_items["progress_ring"].visible = False
                info_items["progress_ring"].update()
            if info_items.get("items_to_read"):
                info_items["items_to_read"].value = "Operation failed."
                info_items["items_to_read"].update()
            page.update() # Ensure UI reflects the error state

    # No_selected_files Text is already defined above with color.
    # audio_files, state_info, progress_ring, items_to_read are also defined.
    # info_items dictionary is also defined.

    page.overlay.extend([get_directory_dialog, pick_files_dialog, selected_file_name])
    }

    page.overlay.extend([get_directory_dialog, pick_files_dialog, selected_file_name])
    page.window_width = 480
    page.window_resizable = False
    page.add(
        Row(
            [
                ElevatedButton(
                    "Change audio directory",
                    icon=icons.FOLDER_OPEN,
                    on_click=lambda _: get_directory_dialog.get_directory_path(),
                    disabled=page.web,
                ),
                directory_path,
            ]
        ),
        Row(
            [
                ElevatedButton(
                    "Select file",
                    icon=icons.UPLOAD_FILE,
                    on_click=lambda _: pick_files_dialog.pick_files(
                        # allow_multiple=True,
                        allowed_extensions=["epub", "txt", "pdf"],
                    ),
                ),
                selected_files,
            ]
        ),
        Row(
            [
                ElevatedButton(
                    "Generate audio",
                    icon=icons.AUDIO_FILE,
                    on_click=init_reading
                ),
                no_selected_files,
            ]
        ),
        Row(
            [
                Container(
                    content=audio_files,
                    margin=ft.margin.symmetric(horizontal=15),
                    padding=10,
                    alignment=ft.alignment.center,
                    bgcolor=ft.colors.BLUE_GREY_50,
                    width=400,
                    height=150,
                    border_radius=10,
                    # on_click=lambda e: open_mp3_folder
                ),
            ]
        ),
        Row(
            [
                state_info,
                progress_ring,
                items_to_read,
            ]
        )

    )

if __name__ == '__main__':
    ft.app(target=main)
