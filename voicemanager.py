import pyttsx3
import os
import json
from typing import Optional, Dict, Any, List, Tuple 

import flet as ft # For ft.Text used in _add_to_list

# --- Constants ---
CONFIG_FILE_NAME = "voice_config.json"
DEFAULT_LANGUAGE_INDEX = 0
DEFAULT_SPEED_RATE = 150

# --- Configuration Management ---
def load_voice_config() -> Dict[str, Any]:
    """Loads voice configuration (language index, speed rate) from JSON file."""
    defaults = {"language_index": DEFAULT_LANGUAGE_INDEX, "speed_rate": DEFAULT_SPEED_RATE}
    config_to_save = defaults.copy() # Start with defaults, update if file loads
    needs_saving = False

    try:
        with open(CONFIG_FILE_NAME, 'r') as f:
            loaded_config = json.load(f)
            if not isinstance(loaded_config, dict):
                print(f"Warning: {CONFIG_FILE_NAME} does not contain a valid JSON object. Using defaults and creating/overwriting file.")
                needs_saving = True
            else:
                # Validate language_index
                lang_idx = loaded_config.get("language_index")
                if isinstance(lang_idx, int):
                    config_to_save["language_index"] = lang_idx
                else:
                    print(f"Warning: 'language_index' in {CONFIG_FILE_NAME} is invalid. Using default.")
                    needs_saving = True # Will save default for this key
                
                # Validate speed_rate
                speed = loaded_config.get("speed_rate")
                if isinstance(speed, int):
                    config_to_save["speed_rate"] = speed
                else:
                    print(f"Warning: 'speed_rate' in {CONFIG_FILE_NAME} is invalid. Using default.")
                    needs_saving = True # Will save default for this key
                
                # Check if all default keys are present, if not, file needs update
                for key in defaults:
                    if key not in loaded_config:
                        print(f"Info: Key '{key}' not found in {CONFIG_FILE_NAME}. Adding default.")
                        needs_saving = True # config_to_save already has it from defaults

    except FileNotFoundError:
        print(f"Info: {CONFIG_FILE_NAME} not found. Creating with default settings.")
        needs_saving = True # config_to_save is already defaults
    except json.JSONDecodeError:
        print(f"Warning: Error decoding JSON from {CONFIG_FILE_NAME}. Creating with default settings.")
        needs_saving = True # config_to_save is already defaults
    except Exception as e:
        print(f"Unexpected error loading {CONFIG_FILE_NAME}: {e}. Using defaults.")
        needs_saving = True # config_to_save is already defaults

    if needs_saving:
        save_voice_config(config_to_save["language_index"], config_to_save["speed_rate"])
    
    return config_to_save


def save_voice_config(language_index: int, speed_rate: int) -> None:
    """Saves voice configuration to JSON file."""
    config_data = {
        "language_index": language_index,
        "speed_rate": speed_rate,
    }
    try:
        with open(CONFIG_FILE_NAME, "w") as f:
            json.dump(config_data, f, indent=4)
    except IOError as e:
        print(f"Error saving voice configuration to {CONFIG_FILE_NAME}: {e}")
    except Exception as e: # Catch other potential errors during save
        print(f"An unexpected error occurred while saving configuration: {e}")


# --- Voice Engine Manager ---
class VoiceManager:
    def __init__(self):
        self.config = load_voice_config() # load_voice_config now returns a complete config
        self.current_language_index = self.config["language_index"] # Should exist due to load_voice_config logic
        self.current_speed_rate = self.config["speed_rate"]     # Should exist
        
        self.engine: Optional[pyttsx3.Engine] = None
        self.voices: List[pyttsx3.voice.Voice] = [] 
        self.current_voice: Optional[pyttsx3.voice.Voice] = None

        self._initialize_engine()

    def _initialize_engine(self) -> None:
        """Initializes the pyttsx3 engine, loads voices, and sets properties."""
        try:
            self.engine = pyttsx3.init()
            if not self.engine:
                print("Error: pyttsx3.init() returned None. Engine not initialized.")
                return
        except Exception as e:
            print(f"Critical Error: pyttsx3 engine failed to initialize: {e}")
            self.engine = None
            return

        try:
            self.engine.setProperty("rate", self.current_speed_rate)
            self.voices = self.engine.getProperty("voices")

            if not self.voices:
                print("Warning: No voices found by pyttsx3 engine. Cannot set a voice.")
                self.current_voice = None
                return 

            # Validate current_language_index
            if not (0 <= self.current_language_index < len(self.voices)):
                old_idx = self.current_language_index
                self.current_language_index = DEFAULT_LANGUAGE_INDEX
                print(f"Warning: Saved language index {old_idx} is out of range (0-{len(self.voices)-1}). Defaulting to {self.current_language_index}.")
                # Persist the corrected index
                save_voice_config(self.current_language_index, self.current_speed_rate)
            
            self.current_voice = self.voices[self.current_language_index]
            self.engine.setProperty("voice", self.current_voice.id)
            print(f"VoiceManager initialized: LangIdx={self.current_language_index}, Speed={self.current_speed_rate}, VoiceSet={self.current_voice.name if self.current_voice else 'None'}")

        except Exception as e:
            print(f"Error during engine property setting or voice retrieval: {e}")
            self.engine = None 
            self.voices = []
            self.current_voice = None

    # --- UI Helper Methods ---
    def _update_ui_element(self, ui_key: str, property_name: str, value: Any, info_items: Optional[Dict[str, Any]]):
        if info_items and ui_key in info_items:
            control = info_items.get(ui_key)
            if control and hasattr(control, 'update'): 
                try:
                    if property_name == "controls.append" and hasattr(control, 'controls'):
                        control.controls.append(value)
                    elif property_name == "controls.clear" and hasattr(control, 'controls'):
                        control.controls.clear()
                    else:
                        setattr(control, property_name, value)
                    control.update()
                except Exception as e:
                    print(f"Error updating UI element '{ui_key}' property '{property_name}': {e}")

    def _set_text_value(self, ui_key: str, text_value: str, info_items: Optional[Dict[str, Any]]):
        self._update_ui_element(ui_key, "value", text_value, info_items)

    def _set_visibility(self, ui_key: str, visible: bool, info_items: Optional[Dict[str, Any]]):
        self._update_ui_element(ui_key, "visible", visible, info_items)

    def _add_to_list(self, ui_key: str, item_text: str, info_items: Optional[Dict[str, Any]]):
        # Create ft.Text here as it's a Flet specific object
        self._update_ui_element(ui_key, "controls.append", ft.Text(item_text), info_items)
    
    def _clear_list(self, ui_key: str, info_items: Optional[Dict[str, Any]]):
        self._update_ui_element(ui_key, "controls.clear", None, info_items)

    def generate_speech_audio(self, text_content_map: Dict[str, str], 
                              output_folder_path: str, file_type: str, 
                              info_items: Optional[Dict[str, Any]] = None):
        
        if not self.engine or not self.current_voice:
            err_msg = "Voice engine not ready or no voice selected. Initialize VoiceManager or check logs."
            print(f"Error in generate_speech_audio: {err_msg}")
            self._set_text_value("state_info", err_msg, info_items)
            self._set_visibility("progress_ring", False, info_items)
            return

        self._clear_list("audio_files_list", info_items)
        self._set_text_value("state_info", "Starting audio generation...", info_items)
        self._set_text_value("items_to_read", "Preparing...", info_items)
        self._set_visibility("progress_ring", True, info_items)

        item_count = 0
        total_items = len(text_content_map)
        all_successful = True

        if total_items == 0:
            self._set_text_value("state_info", "No text content provided to process.", info_items)
            self._set_visibility("progress_ring", False, info_items)
            return

        for item_name, text_content in text_content_map.items():
            item_count += 1
            display_item_name = item_name[:35] + "..." if len(item_name) > 35 else item_name
            
            self._set_text_value("state_info", f"Generating: {display_item_name}", info_items)
            self._set_text_value("items_to_read", f"Processing {item_count}/{total_items}: {display_item_name}", info_items)

            zeros = ""
            filename_prefix = ""
            if file_type.lower() != "txt":
                if item_count <= 9: zeros = "00"
                elif item_count <= 99: zeros = "0"
                filename_prefix = f"{zeros}{item_count} - "
            
            safe_item_name = "".join(c if c.isalnum() or c in " .-_" else "_" for c in item_name)
            safe_item_name = safe_item_name[:100] 
            
            mp3_file_name = f"{filename_prefix}{safe_item_name}.mp3"

            if not os.path.exists(output_folder_path):
                try:
                    os.makedirs(output_folder_path, exist_ok=True)
                    print(f"Info: Created output directory {output_folder_path}")
                except OSError as e:
                    print(f"Error creating directory {output_folder_path}: {e}")
                    self._set_text_value("state_info", f"Error creating directory: {e}", info_items)
                    all_successful = False
                    continue 

            full_file_path = os.path.join(output_folder_path, mp3_file_name)

            try:
                self.engine.setProperty("voice", self.current_voice.id) # Ensure voice is set for this operation
                self.engine.save_to_file(text_content, full_file_path)
                self.engine.runAndWait()
                self._add_to_list("audio_files_list", mp3_file_name, info_items) # Pass text of filename
                print(f"Successfully saved: {full_file_path}")
            except Exception as e:
                print(f"Error saving MP3 {full_file_path}: {e}")
                self._set_text_value("state_info", f"Error saving: {display_item_name}", info_items)
                all_successful = False
        
        self._set_visibility("progress_ring", False, info_items)
        final_message = "Finished audio generation successfully." if all_successful else "Finished with some errors. Check console."
        self._set_text_value("state_info", final_message, info_items)
        self._set_text_value("items_to_read", "Processing complete.", info_items)

    def update_voice_settings(self, lang_index: Optional[int] = None, speed: Optional[int] = None) -> None:
        """Updates voice language index and/or speed rate, saves config, and re-initializes engine."""
        config_changed = False
        # Use temporary variables to check before assigning to self
        temp_lang_idx = self.current_language_index
        temp_speed_rate = self.current_speed_rate

        if lang_index is not None and isinstance(lang_index, int) and lang_index != temp_lang_idx:
            temp_lang_idx = lang_index
            config_changed = True
        
        if speed is not None and isinstance(speed, int) and speed != temp_speed_rate:
            temp_speed_rate = speed
            config_changed = True
        
        if config_changed:
            print(f"Updating voice settings: LangIdx={temp_lang_idx}, Speed={temp_speed_rate}")
            self.current_language_index = temp_lang_idx
            self.current_speed_rate = temp_speed_rate
            save_voice_config(self.current_language_index, self.current_speed_rate)
            self._initialize_engine() # Re-initialize with new settings
        else:
            print("Voice settings not changed or invalid types provided.")

    # CLI-based methods (can be adapted or used for debugging)
    def change_speed_rate_cli(self):
        try:
            new_speed_str = input(f"Current speed: {self.current_speed_rate}. New speed (e.g., 150): ")
            new_speed = int(new_speed_str)
            if 50 <= new_speed <= 500: # Basic range check
                 self.update_voice_settings(speed=new_speed)
            else:
                print("Speed out of reasonable range (50-500).")
        except ValueError:
            print("Invalid input. Please enter a number.")

    def select_language_cli(self):
        if not self.voices:
            print("No voices available.")
            return
        print("\nAvailable voices:")
        for i, voice in enumerate(self.voices):
            print(f"{i}: {voice.name} (ID: {voice.id})")
        try:
            new_idx_str = input(f"Current language index: {self.current_language_index}. New index: ")
            new_idx = int(new_idx_str)
            if 0 <= new_idx < len(self.voices):
                self.update_voice_settings(lang_index=new_idx)
            else:
                print("Index out of range.")
        except ValueError:
            print("Invalid input. Please enter a number.")

# Note: The old static 'Voice' class is intentionally removed as per instructions.
# All its functionality is now integrated into 'VoiceManager.generate_speech_audio'
# and the UI helper methods within the VoiceManager class.
