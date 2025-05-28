import os
import flet as ft
import subprocess  # For opening folder
import sys  # For platform check

from flet import (
    FilePicker, FilePickerResultEvent, Row, Column, Container,
    ElevatedButton, ListView, Text, ProgressRing, Dropdown, Slider, Tabs, Tab, RadioGroup, Radio,
    icons, MainAxisAlignment, CrossAxisAlignment, ControlEvent, Page
)

from configs import AppData
import textreader as reader_manager
from voicemanager import VoiceManager

# --- UI Text Translations ---
ui_texts = {
    "en": {
        "app_title": "Text-to-Speech App",
        "tab_processing": "Text to Audio",
        "tab_settings": "Voice Settings",
        "tab_ui_settings": "UI Settings",
        "change_audio_dir_btn": "Change Audio Directory",
        "select_file_btn": "Select File (.txt, .epub, .pdf)",
        "generate_audio_btn": "Generate Audio",
        "generated_files_label": "Generated Audio Files:",
        "status_idle": "Idle",
        "status_initializing": "Initializing...",
        "status_reading_file": "Reading {file_name}...",
        "status_generating_audio": "Generating audio...",
        "status_no_content": "No content from '{file_name}' or file is empty/unsupported.",
        "status_error": "Error: {error_message}",
        "status_engine_error": "Voice engine not available. Check configuration/logs.",
        "select_voice_label": "Select Voice",
        "speed_rate_label": "Speed Rate: {rate}",
        "save_voice_settings_btn": "Save Voice Settings",
        "voice_settings_note": "Note: Restart the app if voice options are not immediately available after system changes.",
        "select_ui_language_label": "Select UI Language:",
        "save_ui_settings_btn": "Save UI Settings",
        # "open_output_folder_btn": "Open Output Folder", # REMOVED
        "no_file_selected": "No file selected.",
        "select_file_first_error": "Error: Please select a file first!",
        "audio_dir_set_snackbar": "Audio directory set to: {path}",
        "voice_settings_saved_snackbar": "Voice settings saved successfully!",
        "voice_settings_failed_snackbar": "Failed to save voice settings.",
        "ui_settings_saved_snackbar": "UI settings saved. Restart may be needed for full effect.",
        "processing_complete": "Processing complete.",
        "folder_opened_snackbar": "Output folder opened: {path}",
        "folder_not_found_snackbar": "Could not open folder: {path} (Not found or invalid)",
        "folder_opening_auto": "Opening output folder...",
    },
    "es": {
        "app_title": "Aplicación de Texto a Voz",
        "tab_processing": "Texto a Audio",
        "tab_settings": "Config. de Voz",
        "tab_ui_settings": "Config. de UI",
        "change_audio_dir_btn": "Cambiar Directorio de Audio",
        "select_file_btn": "Seleccionar Archivo (.txt, .epub, .pdf)",
        "generate_audio_btn": "Generar Audio",
        "generated_files_label": "Archivos de Audio Generados:",
        "status_idle": "Inactivo",
        "status_initializing": "Inicializando...",
        "status_reading_file": "Leyendo {file_name}...",
        "status_generating_audio": "Generando audio...",
        "status_no_content": "Sin contenido de '{file_name}' o archivo vacío/no soportado.",
        "status_error": "Error: {error_message}",
        "status_engine_error": "Motor de voz no disponible. Revise configuración/logs.",
        "select_voice_label": "Seleccionar Voz",
        "speed_rate_label": "Velocidad: {rate}",
        "save_voice_settings_btn": "Guardar Config. de Voz",
        "voice_settings_note": "Nota: Reinicie la app si las opciones de voz no están disponibles tras cambios en el sistema.",
        "select_ui_language_label": "Seleccionar Idioma de UI:",
        "save_ui_settings_btn": "Guardar Config. de UI",
        # "open_output_folder_btn": "Abrir Carpeta de Salida", # REMOVED
        "no_file_selected": "Ningún archivo seleccionado.",
        "select_file_first_error": "Error: ¡Por favor, seleccione un archivo primero!",
        "audio_dir_set_snackbar": "Directorio de audio establecido en: {path}",
        "voice_settings_saved_snackbar": "¡Configuración de voz guardada exitosamente!",
        "voice_settings_failed_snackbar": "Error al guardar configuración de voz.",
        "ui_settings_saved_snackbar": "Configuración de UI guardada. Puede ser necesario reiniciar para efecto completo.",
        "processing_complete": "Procesamiento completo.",
        "folder_opened_snackbar": "Carpeta de salida abierta: {path}",
        "folder_not_found_snackbar": "No se pudo abrir la carpeta: {path} (No encontrada o inválida)",
        "folder_opening_auto": "Abriendo carpeta de salida...",
    }
}

current_lang_code = "en"


def T(key: str, **kwargs):
    return ui_texts.get(current_lang_code, ui_texts["en"]).get(key, f"<{key}>").format(**kwargs)


def main(page: Page):
    global current_lang_code

    app_data = AppData()
    voice_manager = VoiceManager(app_data)
    current_lang_code = app_data.data.get("ui_language", "en")

    page.title = T("app_title")
    page.vertical_alignment = MainAxisAlignment.START
    page.horizontal_alignment = CrossAxisAlignment.CENTER
    page.window_width = 520  # Adjusted width
    page.window_height = 680  # Adjusted height
    page.window_resizable = False

    # --- UI Helper Functions ---
    def show_snackbar(message_key: str, error: bool = False, **kwargs):
        message = T(message_key, **kwargs)
        page.show_snack_bar(
            ft.SnackBar(
                Text(message, color=ft.colors.WHITE if not error else ft.colors.BLACK),
                open=True,
                bgcolor=ft.colors.RED_ACCENT_700 if error else ft.colors.GREEN_ACCENT_700,
            )
        )

    def _open_folder_path(path_to_open: str | None):
        """Helper function to open a folder path."""
        if path_to_open and os.path.isdir(path_to_open):
            try:
                if sys.platform == "win32":
                    os.startfile(path_to_open)
                elif sys.platform == "darwin":
                    subprocess.run(["open", path_to_open], check=True)
                else:
                    subprocess.run(["xdg-open", path_to_open], check=True)
                show_snackbar("folder_opened_snackbar", path=path_to_open)
            except Exception as ex:
                print(f"Error opening folder {path_to_open}: {ex}")
                show_snackbar("folder_not_found_snackbar", error=True, path=path_to_open)
        elif path_to_open:  # Path provided but not a directory
            show_snackbar("folder_not_found_snackbar", error=True, path=path_to_open)
        # If path_to_open is None, do nothing (already handled by caller)

    # --- File and Directory Selection Callbacks ---
    def get_directory_result(e: FilePickerResultEvent):
        if e.path:
            directory_path_text.value = e.path
            directory_path_text.tooltip = e.path
            app_data.data["mp3_directory"] = e.path
            app_data.save_changes(app_data.data)
            directory_path_text.update()
            show_snackbar("audio_dir_set_snackbar", path=e.path)
        else:
            current_dir = app_data.data["mp3_directory"]
            directory_path_text.value = current_dir
            directory_path_text.tooltip = current_dir
            directory_path_text.update()

    def pick_files_result(e: FilePickerResultEvent):
        if e.files and e.files[0].path:
            selected_file_name_hidden.value = e.files[0].name
            selected_file_path_text.tooltip = e.files[0].path

            display_path = e.files[0].path
            if len(display_path) > 30:
                display_path = "..." + display_path[-27:]
            selected_file_path_text.value = display_path

            selected_file_path_text.update()
            selected_file_name_hidden.update()
            error_message_text.value = ""
            error_message_text.update()
            generate_audio_button.disabled = False
            generate_audio_button.update()
        else:
            selected_file_path_text.value = T("no_file_selected")
            selected_file_name_hidden.value = ""
            selected_file_path_text.update()
            selected_file_name_hidden.update()
            generate_audio_button.disabled = True
            generate_audio_button.update()

    get_directory_dialog = FilePicker(on_result=get_directory_result)
    pick_files_dialog = FilePicker(on_result=pick_files_result)
    selected_file_name_hidden = Text(visible=False)
    page.overlay.extend([get_directory_dialog, pick_files_dialog, selected_file_name_hidden])

    # --- UI Elements ---
    directory_path_text = Text(app_data.data["mp3_directory"], max_lines=1, overflow="ellipsis", width=280,
                               tooltip=app_data.data["mp3_directory"])  # Wider
    selected_file_path_text = Text(T("no_file_selected"), max_lines=1, overflow="ellipsis", width=280)  # Wider
    error_message_text = Text("", color=ft.colors.RED, weight=ft.FontWeight.BOLD)
    audio_files_list = ListView(expand=False, spacing=5, padding=10, height=150, auto_scroll=True)
    status_info_text = Text(T("status_idle"), italic=True)
    progress_ring_indicator = ProgressRing(width=20, height=20, stroke_width=3, visible=False)
    items_processed_text = Text("", size=12)

    ui_feedback_controls = {
        "audio_files_list": audio_files_list,
        "state_info": status_info_text,
        "progress_ring": progress_ring_indicator,
        "items_to_read": items_processed_text,
    }

    def reset_ui_before_processing():
        audio_files_list.controls.clear()
        audio_files_list.update()
        status_info_text.value = T("status_initializing")
        status_info_text.update()
        items_processed_text.value = ""
        items_processed_text.update()
        progress_ring_indicator.visible = True
        progress_ring_indicator.update()
        error_message_text.value = ""
        error_message_text.update()
        generate_audio_button.disabled = True
        generate_audio_button.update()
        page.update()

    def init_reading_process(e: ControlEvent):
        reset_ui_before_processing()

        selected_file_full_path = selected_file_path_text.tooltip
        original_file_name = selected_file_name_hidden.value
        mp3_output_directory = directory_path_text.tooltip

        if not selected_file_full_path or not original_file_name or selected_file_path_text.value == T(
                "no_file_selected"):
            error_message_text.value = T("select_file_first_error")
            error_message_text.update()
            status_info_text.value = T("status_idle")
            status_info_text.update()
            progress_ring_indicator.visible = False
            progress_ring_indicator.update()
            generate_audio_button.disabled = False
            generate_audio_button.update()
            return

        if not voice_manager.engine:
            error_message_text.value = T("status_engine_error")
            error_message_text.update()
            status_info_text.value = "Engine Error"
            status_info_text.update()
            progress_ring_indicator.visible = False
            progress_ring_indicator.update()
            generate_audio_button.disabled = False
            generate_audio_button.update()
            return

        generated_path_for_book = None
        try:
            status_info_text.value = T("status_reading_file", file_name=original_file_name)
            status_info_text.update()
            page.update()

            extracted_content = reader_manager.get_temporal_books(
                selected_file_full_path, original_file_name, mp3_output_directory
            )

            if not extracted_content:
                status_info_text.value = T("status_no_content", file_name=original_file_name)
                progress_ring_indicator.visible = False
                items_processed_text.value = ""  # Clear
                # Update controls directly here instead of relying on ui_feedback_controls for this specific case
                status_info_text.update()
                progress_ring_indicator.update()
                items_processed_text.update()
                generate_audio_button.disabled = False
                generate_audio_button.update()
                return  # Exit if no content

            status_info_text.value = T("status_generating_audio")
            status_info_text.update()
            page.update()

            # This call now returns the path to the generated audio folder/file
            generated_path_for_book = reader_manager.start_reading(
                voice_manager,
                extracted_content,
                mp3_output_directory,
                original_file_name,
                ui_feedback_controls  # ui_feedback_controls is still used by start_reading internally
            )
        except Exception as ex:
            print(f"An error occurred during text-to-speech processing: {ex}")
            status_info_text.value = T("status_error", error_message=str(ex)[:50])
            progress_ring_indicator.visible = False
            status_info_text.update()
            progress_ring_indicator.update()
        finally:
            if progress_ring_indicator.visible:  # Ensure ring is off
                progress_ring_indicator.visible = False
                progress_ring_indicator.update()

            is_error_or_no_content = "Error" in status_info_text.value or \
                                     T("status_no_content", file_name=original_file_name) in status_info_text.value or \
                                     "failed" in status_info_text.value.lower()

            # If generate_audio finished and didn't set "Processing complete." via ui_feedback_controls
            if not is_error_or_no_content and T("processing_complete") not in status_info_text.value:
                status_info_text.value = T("processing_complete")
                status_info_text.update()

            generate_audio_button.disabled = False  # Re-enable button
            generate_audio_button.update()

            if generated_path_for_book:
                # Automatically open the folder
                # Add a small delay or status update before opening for better UX
                status_info_text.value = T("folder_opening_auto")
                status_info_text.update()
                page.update()  # Ensure message is shown
                # Consider a brief ft.time.sleep(0.5) if page update isn't immediate enough,
                # but direct call is usually fine. Flet is single-threaded for UI updates.
                _open_folder_path(generated_path_for_book)
                # After opening, revert status or keep "Processing complete."
                # Status info is likely already "Processing complete." from generate_audio
            else:
                print("No specific path returned by start_reading, folder not opened.")

            page.update()  # Final page update

    generate_audio_button = ElevatedButton(
        text=T("generate_audio_btn"),
        icon=icons.AUDIO_FILE_ROUNDED,
        on_click=init_reading_process,
        disabled=True,
        tooltip="Select a file first"
    )

    # --- Voice Settings Tab Elements ---
    available_voices_options = []
    if voice_manager.engine:
        available_voices_options = [
            ft.dropdown.Option(key=voice_id, text=name)
            for voice_id, name in voice_manager.get_available_voices().items()
        ]

    voice_dropdown = Dropdown(
        label=T("select_voice_label"),
        options=available_voices_options,
        value=voice_manager.get_current_voice_id(),
        width=450,
        disabled=not bool(voice_manager.engine and available_voices_options),
        on_change=lambda e: voice_manager.set_current_voice_id(e.control.value)
    )

    speed_slider_label = Text(T("speed_rate_label", rate=voice_manager.get_speed_rate()))
    speed_slider = Slider(
        min=50, max=500, divisions=90,
        value=voice_manager.get_speed_rate(),
        label="{value}",
        width=300,
        disabled=not bool(voice_manager.engine),
        on_change_end=lambda e: voice_manager.set_speed_rate(int(e.control.value)),
        on_change=lambda e: setattr(speed_slider_label, 'value',
                                    T("speed_rate_label", rate=int(e.control.value))) or speed_slider_label.update()
    )

    def save_voice_settings_action(e: ControlEvent):
        if voice_manager.save_settings():
            show_snackbar("voice_settings_saved_snackbar")
        else:
            show_snackbar("voice_settings_failed_snackbar", error=True)
        current_id = voice_manager.get_current_voice_id()
        if voice_dropdown.value != current_id:
            voice_dropdown.value = current_id
            voice_dropdown.update()
        current_speed = voice_manager.get_speed_rate()
        if speed_slider.value != current_speed:
            speed_slider.value = current_speed
            speed_slider.update()
        speed_slider_label.value = T("speed_rate_label", rate=current_speed)
        speed_slider_label.update()

    save_voice_settings_button = ElevatedButton(
        text=T("save_voice_settings_btn"),
        icon=icons.SAVE_ALT_ROUNDED,
        on_click=save_voice_settings_action,
        disabled=not bool(voice_manager.engine)
    )

    # --- UI Settings Tab Elements ---
    ui_language_radio_group = RadioGroup(
        content=Row(
            [Radio(value="en", label="English"), Radio(value="es", label="Español")],
            alignment=MainAxisAlignment.CENTER
        ),
        value=current_lang_code
    )

    def save_ui_settings_action(e: ControlEvent):
        global current_lang_code
        selected_lang = ui_language_radio_group.value
        if selected_lang and selected_lang != current_lang_code:  # Only update if changed
            app_data.data["ui_language"] = selected_lang
            app_data.save_changes(app_data.data)
            current_lang_code = selected_lang
            update_all_ui_texts()
            show_snackbar("ui_settings_saved_snackbar")
        elif not selected_lang:  # Should not happen with RadioGroup
            show_snackbar("No language selected for UI.", error=True)

    save_ui_settings_button = ElevatedButton(
        text=T("save_ui_settings_btn"),
        icon=icons.LANGUAGE_ROUNDED,
        on_click=save_ui_settings_action
    )

    # --- Update UI Text Function ---
    change_audio_dir_button_ref = ft.Ref[ElevatedButton]()
    select_file_button_ref = ft.Ref[ElevatedButton]()
    generated_files_label_ref = ft.Ref[Text]()
    voice_settings_note_ref = ft.Ref[Text]()
    select_ui_language_label_ref = ft.Ref[Text]()
    tab_processing_ref = ft.Ref[Tab]()
    tab_settings_ref = ft.Ref[Tab]()
    tab_ui_settings_ref = ft.Ref[Tab]()

    def update_all_ui_texts():
        page.title = T("app_title")
        if change_audio_dir_button_ref.current: change_audio_dir_button_ref.current.text = T("change_audio_dir_btn")
        if select_file_button_ref.current: select_file_button_ref.current.text = T("select_file_btn")
        generate_audio_button.text = T("generate_audio_btn")
        if generated_files_label_ref.current: generated_files_label_ref.current.value = T("generated_files_label")

        # Smart update for status and selected file text
        # This logic tries to preserve dynamic messages and only translate static placeholders
        current_status_is_placeholder = any(
            status_info_text.value == T("status_idle", lang=lang_code) for lang_code in ui_texts.keys())
        if current_status_is_placeholder:
            status_info_text.value = T("status_idle")

        current_file_text_is_placeholder = any(
            selected_file_path_text.value == T("no_file_selected", lang=lang_code) for lang_code in ui_texts.keys())
        if current_file_text_is_placeholder:
            selected_file_path_text.value = T("no_file_selected")

        voice_dropdown.label = T("select_voice_label")
        # Ensure rate is fetched if voice_manager is available, otherwise use a default for the string
        current_rate_for_label = voice_manager.get_speed_rate() if voice_manager else 150
        speed_slider_label.value = T("speed_rate_label", rate=current_rate_for_label)

        save_voice_settings_button.text = T("save_voice_settings_btn")
        if voice_settings_note_ref.current: voice_settings_note_ref.current.value = T("voice_settings_note")
        if select_ui_language_label_ref.current: select_ui_language_label_ref.current.value = T(
            "select_ui_language_label")
        save_ui_settings_button.text = T("save_ui_settings_btn")  # Save UI settings button text

        if tab_processing_ref.current: tab_processing_ref.current.text = T("tab_processing")
        if tab_settings_ref.current: tab_settings_ref.current.text = T("tab_settings")
        if tab_ui_settings_ref.current: tab_ui_settings_ref.current.text = T("tab_ui_settings")

        # Update RadioGroup labels (more complex if Radio itself is not a ref)
        # For simplicity, assume labels are static or recreate RadioGroup if needed,
        # or access Radio controls via ui_language_radio_group.content.controls
        if isinstance(ui_language_radio_group.content, Row):
            for i, radio_control in enumerate(ui_language_radio_group.content.controls):
                if isinstance(radio_control, Radio):
                    if radio_control.value == "en":
                        radio_control.label = "English"
                    elif radio_control.value == "es":
                        radio_control.label = "Español"

        page.update()

    # --- Page Layout using Tabs ---
    tab_processing_content = Column(
        [
            Row([
                ElevatedButton(ref=change_audio_dir_button_ref, text=T("change_audio_dir_btn"),
                               icon=icons.FOLDER_OPEN_ROUNDED,
                               on_click=lambda _: get_directory_dialog.get_directory_path(
                                   dialog_title="Select MP3 Output Directory",
                                   initial_directory=app_data.data["mp3_directory"]),
                               disabled=page.web),
                directory_path_text,
            ], alignment=MainAxisAlignment.START),
            Row([
                ElevatedButton(ref=select_file_button_ref, text=T("select_file_btn"), icon=icons.UPLOAD_FILE_ROUNDED,
                               on_click=lambda _: pick_files_dialog.pick_files(dialog_title="Select File to Convert",
                                                                               allowed_extensions=["txt", "epub",
                                                                                                   "pdf"],
                                                                               allow_multiple=False)),
                selected_file_path_text,
            ], alignment=MainAxisAlignment.START),
            error_message_text,
            generate_audio_button,  # Removed the Row here as open_output_folder_button is removed
            ft.Divider(),
            Text(ref=generated_files_label_ref, value=T("generated_files_label"), weight=ft.FontWeight.BOLD),
            Container(content=audio_files_list, border=ft.border.all(1, ft.colors.OUTLINE), border_radius=5, padding=5,
                      width=480),
            ft.Divider(),
            Row([status_info_text, progress_ring_indicator, items_processed_text], spacing=10,
                vertical_alignment=CrossAxisAlignment.CENTER, alignment=MainAxisAlignment.CENTER),
        ], spacing=12, horizontal_alignment=CrossAxisAlignment.CENTER,
    )

    tab_processing = Tab(ref=tab_processing_ref, text=T("tab_processing"), icon=icons.RECORD_VOICE_OVER_ROUNDED,
                         content=Container(content=tab_processing_content, padding=15))

    tab_voice_settings_content = Column(
        [
            Text(T("select_voice_label"), size=18, weight=ft.FontWeight.BOLD),
            voice_dropdown,
            ft.Container(height=10),
            speed_slider_label,
            speed_slider,
            ft.Container(height=20),
            save_voice_settings_button,  # Changed ref assignment, direct variable used
            Text(ref=voice_settings_note_ref, value=T("voice_settings_note"), italic=True, size=10,
                 color=ft.colors.ON_SURFACE_VARIANT)
        ], spacing=15, horizontal_alignment=CrossAxisAlignment.CENTER,
    )
    tab_settings = Tab(ref=tab_settings_ref, text=T("tab_settings"), icon=icons.SETTINGS_VOICE_ROUNDED,
                       content=Container(content=tab_voice_settings_content, padding=20))

    tab_ui_settings_content = Column(
        [
            Text(ref=select_ui_language_label_ref, value=T("select_ui_language_label"), size=16,
                 weight=ft.FontWeight.BOLD),
            ui_language_radio_group,
            ft.Container(height=20),
            save_ui_settings_button  # Changed ref assignment, direct variable used
        ], spacing=15, horizontal_alignment=CrossAxisAlignment.CENTER,
    )
    tab_ui_settings = Tab(ref=tab_ui_settings_ref, text=T("tab_ui_settings"), icon=icons.TRANSLATE_ROUNDED,
                          content=Container(content=tab_ui_settings_content, padding=20))

    page.add(
        Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[tab_processing, tab_settings, tab_ui_settings],
            expand=True,
        )
    )
    update_all_ui_texts()  # Call it once to set initial texts


if __name__ == '__main__':
    ft.app(target=main)
