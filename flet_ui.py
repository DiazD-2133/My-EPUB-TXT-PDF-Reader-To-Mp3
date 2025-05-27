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

import textreader as reader_manager
from voicemanager import VoiceManager, Voice


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

    pick_files_dialog = FilePicker(on_result=pick_files_result)

    selected_files = Text(max_lines=5, width=210,)
    selected_file_name = Text(visible=False)

    def init_reading(e):
        selected_files.update()
        if selected_files.value:
            file_path = selected_files.value
            file_name = selected_file_name.value
            mp3_dir = directory_path.value
            no_selected_files.value = ""
            no_selected_files.update()

            reader = VoiceManager()
            voice = Voice()

            info_items["state_info"].visible = True
            info_items["progress_ring"].visible = True
            info_items["items_to_read"].visible = True
            info_items["state_info"].update()
            info_items["progress_ring"].update()
            info_items["items_to_read"].update()

            temporal_book = reader_manager.get_temporal_books(file_path, file_name, mp3_dir)
            reader_manager.start_reading(voice, reader, temporal_book, mp3_dir, file_name, info_items)

        else:
            no_selected_files.value = "You need to choose a file!"
            no_selected_files.update()

    no_selected_files = Text()

    audio_files = ListView(expand=1, spacing=10, padding=20, auto_scroll=True)
    state_info = Text()
    progress_ring = ProgressRing(width=16, height=16, stroke_width=2, visible=False)
    items_to_read = Text()

    info_items = {
        "audio_files_list": audio_files,
        "state_info": state_info,
        "progress_ring": progress_ring,
        "items_to_read": items_to_read,
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
