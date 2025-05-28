import pyttsx3
import os
from configs import AppData
from flet import Text  # For UI updates, passed via info_items


class VoiceManager:
    def __init__(self, app_data: AppData):
        self.app_data = app_data
        self.engine = None
        self.voices_map = {}  # Stores {voice.id: voice.name}
        self.current_voice_id = None
        self.speed_rate = 150

        self._load_config_and_initialize_engine()

    def _load_config_and_initialize_engine(self):
        # Load config
        try:
            # Use .get for safer dictionary access
            self.current_voice_id = self.app_data.data.get("voice_id")
            self.speed_rate = int(self.app_data.data.get("speed_rate", 150))
        except (ValueError, TypeError):
            print("Warning: Voice config data is invalid or types are wrong. Using defaults.")
            self.current_voice_id = None  # Will be set to default later
            self.speed_rate = 150
            # Mark for rewrite if types were wrong
            self.app_data.data["voice_id"] = self.current_voice_id
            self.app_data.data["speed_rate"] = self.speed_rate
            self.save_settings()

        # Initialize engine
        try:
            self.engine = pyttsx3.init()
            if not self.engine:
                print("Error: pyttsx3 engine could not be initialized (returned None).")
                return

            available_voices = self.engine.getProperty("voices")
            if not available_voices:
                print("Warning: No voices found by pyttsx3 engine.")
                self.engine = None  # Mark as not available
                return

            for v in available_voices:
                self.voices_map[v.id] = v.name

            # Set voice
            if self.current_voice_id and self.current_voice_id in self.voices_map:
                self.engine.setProperty("voice", self.current_voice_id)
            elif available_voices:  # Default to first voice if saved one is invalid or not set
                default_voice = available_voices[0]
                self.current_voice_id = default_voice.id
                print(
                    f"Info: Defaulting to voice: {self.voices_map.get(self.current_voice_id, 'Unknown')} ({self.current_voice_id})")
                self.engine.setProperty("voice", self.current_voice_id)
                self.app_data.data["voice_id"] = self.current_voice_id  # Save corrected/default ID
                self.save_settings()  # Save immediately
            else:  # No voices, no current_voice_id
                self.current_voice_id = None
                print("Error: No voices available to set a default voice.")
                self.engine = None  # Mark as not available
                return

            # Set speed
            self.engine.setProperty("rate", self.speed_rate)

        except Exception as e:
            print(f"Error: pyttsx3 engine initialization or property setting failed: {e}")
            self.engine = None

    def get_available_voices(self) -> dict:
        """Returns a dictionary of available voices {id: name}."""
        return self.voices_map.copy()

    def get_current_voice_id(self) -> str | None:
        return self.current_voice_id

    def set_current_voice_id(self, voice_id: str):
        if self.engine and voice_id in self.voices_map:
            self.current_voice_id = voice_id
            self.engine.setProperty("voice", self.current_voice_id)
            self.app_data.data["voice_id"] = self.current_voice_id
            # self.save_settings() # Save is handled by a dedicated button in UI
        elif not self.engine:
            print("Warning: Could not set voice ID. Engine not ready.")
        else:
            print(f"Warning: Voice ID '{voice_id}' not found in available voices.")

    def get_speed_rate(self) -> int:
        return self.speed_rate

    def set_speed_rate(self, rate: int):
        if self.engine:
            # Add validation for rate if desired (e.g., 50 to 500)
            if 50 <= rate <= 500:
                self.speed_rate = rate
                self.engine.setProperty("rate", self.speed_rate)
                self.app_data.data["speed_rate"] = self.speed_rate
                # self.save_settings() # Save is handled by a dedicated button in UI
            else:
                print(f"Warning: Speed rate {rate} is out of a reasonable range (50-500). Not set.")
        else:
            print("Warning: Could not set speed rate. Engine not ready.")

    def save_settings(self):
        try:
            self.app_data.save_changes(self.app_data.data)
            print("Voice settings saved.")
            return True
        except Exception as e:
            print(f"Error saving voice settings: {e}")
            return False

    def _update_ui_feedback(self, info_items, state_msg="", items_msg="", ring_visible=False, clear_list=False,
                            add_to_list_item_name=None):
        if not info_items: return

        if "state_info" in info_items and info_items["state_info"]:
            info_items["state_info"].value = state_msg
            info_items["state_info"].update()

        if "items_to_read" in info_items and info_items["items_to_read"]:
            info_items["items_to_read"].value = items_msg
            info_items["items_to_read"].update()

        if "progress_ring" in info_items and info_items["progress_ring"]:
            info_items["progress_ring"].visible = ring_visible
            info_items["progress_ring"].update()

        audio_list_control = info_items.get("audio_files_list")
        if audio_list_control and hasattr(audio_list_control, "controls"):
            if clear_list:
                audio_list_control.controls.clear()
            if add_to_list_item_name:
                # Assuming ft.Text is the type of control for list items
                audio_list_control.controls.append(Text(add_to_list_item_name))
            audio_list_control.update()

    def generate_audio(self, file_extension: str, folder_dir: str, files_data: dict, info_items: dict):
        if not self.engine or not self.current_voice_id:
            err_msg = "Voice engine not ready or no voice selected. Cannot generate audio."
            print(f"Error in generate_audio: {err_msg}")
            self._update_ui_feedback(info_items, state_msg=err_msg, ring_visible=False)
            return

        self._update_ui_feedback(info_items, clear_list=True)

        total_items = len(files_data)
        if total_items == 0:
            self._update_ui_feedback(info_items, state_msg="No text data found to process.", ring_visible=False)
            return

        all_successful = True
        processed_item_idx = 0

        for data_name, text_content in files_data.items():
            processed_item_idx += 1

            display_data_name = data_name[:25] + "..." if len(data_name) > 25 else data_name
            current_item_msg = f"Item {processed_item_idx}/{total_items}"
            print(f"\nProcessing {current_item_msg}: {data_name}")
            self._update_ui_feedback(info_items,
                                     state_msg=f"Generating: {display_data_name}",
                                     items_msg=current_item_msg,
                                     ring_visible=True)

            zeros = ""
            if file_extension.lower() != "txt":  # For EPUB/PDF chapters
                if processed_item_idx <= 9:
                    zeros = "00"
                elif processed_item_idx <= 99:
                    zeros = "0"

            # Sanitize data_name for use in filename
            safe_data_name = "".join(c if c.isalnum() or c in " .-_()" else "_" for c in data_name)
            safe_data_name = safe_data_name[:100]  # Limit length

            mp3_file_name = f"{zeros}{processed_item_idx} - {safe_data_name}.mp3" if file_extension.lower() != "txt" else f"{safe_data_name}.mp3"

            if not os.path.exists(folder_dir):
                try:
                    os.makedirs(folder_dir, exist_ok=True)
                except OSError as e:
                    error_msg = f"Error creating folder {folder_dir}: {e}"
                    print(error_msg)
                    self._update_ui_feedback(info_items, state_msg=error_msg, ring_visible=False)
                    all_successful = False
                    continue  # Skip this item, try next

            full_file_path = os.path.join(folder_dir, mp3_file_name)

            try:
                # Voice and rate are already set on the engine instance
                self.engine.save_to_file(text_content, full_file_path)
                self.engine.runAndWait()

                self._update_ui_feedback(info_items, add_to_list_item_name=mp3_file_name)
                print(f"Done! File saved as {full_file_path}")

            except Exception as e:
                error_msg = f"Error saving {mp3_file_name}: {e}"
                print(error_msg)
                # Update state_info for this specific error, but it might be overwritten
                self._update_ui_feedback(info_items, state_msg=f"Error on {display_data_name}",
                                         items_msg=current_item_msg)
                all_successful = False

        final_state_message = f"Finished {total_items} items."
        if not all_successful:
            final_state_message += " Some errors occurred (see console)."

        self._update_ui_feedback(info_items,
                                 state_msg=final_state_message,
                                 items_msg="Processing complete.",
                                 ring_visible=False)
