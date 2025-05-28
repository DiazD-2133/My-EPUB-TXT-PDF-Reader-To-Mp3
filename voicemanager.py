import json
import os
import pyttsx3
from typing import List, Dict, Tuple, Optional


# --- Constants ---
VOICE_CONFIG_FILE = "voice_config.json"
DEFAULT_LANGUAGE_INDEX = 0
DEFAULT_SPEED_RATE = 150


# --- Configuration Management ---
def load_voice_config() -> Tuple[int, int]:
    """Loads voice configuration (language index, speed rate) from JSON file."""
    try:
        with open(VOICE_CONFIG_FILE, "r") as f:
            config_data = json.load(f)
            language_index = int(config_data.get("language_index", DEFAULT_LANGUAGE_INDEX))
            speed_rate = int(config_data.get("speed_rate", DEFAULT_SPEED_RATE))
            return language_index, speed_rate
    except FileNotFoundError:
        print(
            "Warning: {} not found. Using default voice settings and creating file.".format(
                VOICE_CONFIG_FILE
            )
        )
        save_voice_config(DEFAULT_LANGUAGE_INDEX, DEFAULT_SPEED_RATE)
        return DEFAULT_LANGUAGE_INDEX, DEFAULT_SPEED_RATE
    except (json.JSONDecodeError, ValueError) as e: # Catch invalid JSON or int conversion errors
        print(
            "Warning: Invalid data in {}: {}. Using defaults and recreating file.".format(
                VOICE_CONFIG_FILE, e
            )
        )
        save_voice_config(DEFAULT_LANGUAGE_INDEX, DEFAULT_SPEED_RATE) # Overwrite with defaults
        return DEFAULT_LANGUAGE_INDEX, DEFAULT_SPEED_RATE
    except Exception as e: # Catch-all for other IOErrors or unexpected issues
        print(
            "Error loading voice config from {}: {}. Using default settings.".format(
                VOICE_CONFIG_FILE, e
            )
        )
        return DEFAULT_LANGUAGE_INDEX, DEFAULT_SPEED_RATE


def save_voice_config(language_index: int, speed_rate: int) -> None:
    """Saves voice configuration to JSON file."""
    config_data = {
        "language_index": language_index,
        "speed_rate": speed_rate,
    }
    try:
        with open(VOICE_CONFIG_FILE, "w") as f:
            json.dump(config_data, f, indent=4)
    except IOError as e:
        print("Error saving voice configuration to {}: {}".format(VOICE_CONFIG_FILE, e))


# --- Voice Engine Manager ---
class VoiceManager:
    """Manages voice settings and the pyttsx3 text-to-speech engine."""

    def __init__(self) -> None:
        self.language_index, self.speed_rate = load_voice_config()
        self.engine: Optional[pyttsx3.Engine] = None
        self.voices: List[pyttsx3.voice.Voice] = []
        self.current_voice: Optional[pyttsx3.voice.Voice] = None

        self._initialize_engine()

    def _initialize_engine(self) -> None:
        """Initializes the pyttsx3 engine and loads available voices."""
        try:
            self.engine = pyttsx3.init()
            if not self.engine: # Check if engine failed to initialize
                print("Error: pyttsx3 engine could not be initialized.")
                return

            self.voices = self.engine.getProperty("voices")
            if not self.voices:
                print("Error: No voices available on the system.")
                self.engine = None # Disable engine if no voices
                return

            # Validate and set current voice
            if not (0 <= self.language_index < len(self.voices)):
                print(
                    "Warning: Saved language index {} is invalid. Resetting to default {}.".format(
                        self.language_index, DEFAULT_LANGUAGE_INDEX
                    )
                )
                self.language_index = DEFAULT_LANGUAGE_INDEX
                save_voice_config(self.language_index, self.speed_rate) # Save corrected index

            self.current_voice = self.voices[self.language_index]
            self.engine.setProperty("voice", self.current_voice.id)
            self.engine.setProperty("rate", self.speed_rate)

        except RuntimeError as e: # Catch pyttsx3 runtime errors
            print("RuntimeError initializing text-to-speech engine: {}".format(e))
            self.engine = None
            self.voices = []
            self.current_voice = None
        except Exception as e: # Catch any other unexpected errors
            print("Unexpected error initializing text-to-speech engine: {}".format(e))
            self.engine = None
            self.voices = []
            self.current_voice = None

    def _get_user_confirmation(self, prompt: str) -> bool:
        """Gets a 'y/n' confirmation from the user."""
        while True:
            user_input: str = input(prompt + " (y/n): ").lower()
            if user_input == "y":
                return True
            if user_input == "n":
                return False
            print("Invalid input. Please enter 'y' or 'n'.")

    def _prompt_for_speed_rate(self) -> Optional[int]:
        """Prompts the user for a new speed rate and validates it."""
        while True:
            try:
                speed_rate_str: str = input(
                    "\nEnter the new voice speed rate (e.g., 150).\n"
                    "Recommended: 120 (slower) to 180 (faster): "
                )
                new_speed_rate: int = int(speed_rate_str)
                if 50 <= new_speed_rate <= 500: # Basic sanity check for rate
                    return new_speed_rate
                else:
                    print("Speed rate seems too low or high. Please choose a value between 50 and 500.")
            except ValueError:
                print("Invalid input. Please enter a number for the speed rate.")
            
            if not self._get_user_confirmation("Try entering speed rate again?"):
                return None


    def change_speed_rate(self) -> None:
        """Allows the user to change the voice speed rate."""
        if not self.engine:
            print("Voice engine not available. Cannot change speed rate.")
            return

        print("\nCurrent speed rate: {}".format(self.speed_rate))
        if self._get_user_confirmation("Do you want to change the voice speed rate?"):
            new_speed = self._prompt_for_speed_rate()
            if new_speed is not None:
                self.speed_rate = new_speed
                try:
                    self.engine.setProperty("rate", self.speed_rate)
                    save_voice_config(self.language_index, self.speed_rate)
                    print("Voice speed rate changed to {}.".format(self.speed_rate))
                except Exception as e:
                    print("Error setting new speed rate: {}".format(e))


    def select_language(self) -> None:
        """Allows the user to select a new voice language."""
        if not self.engine or not self.voices:
            print("Voice engine or voices not available. Cannot select language.")
            return

        current_lang_name = "Unknown"
        if self.current_voice:
            try:
                current_lang_name = self.current_voice.name.split("-")[1].split()[0]
            except (AttributeError, IndexError):
                pass # Keep as Unknown
        print("\nCurrent language: {}".format(current_lang_name))

        if not self._get_user_confirmation("Do you want to change the language?"):
            return

        print("\nAvailable voices:")
        for i, voice_obj in enumerate(self.voices):
            try:
                lang_name_display = voice_obj.name # More descriptive name
            except (AttributeError, IndexError):
                lang_name_display = "Unknown Voice {}".format(i + 1)
            print("{}: {}".format(i + 1, lang_name_display))

        while True:
            try:
                choice_str = input("Choose voice by its number (or 0 to cancel): ")
                choice = int(choice_str)
                if choice == 0:
                    return
                if 1 <= choice <= len(self.voices):
                    self.language_index = choice - 1
                    self.current_voice = self.voices[self.language_index]
                    self.engine.setProperty("voice", self.current_voice.id)
                    save_voice_config(self.language_index, self.speed_rate)
                    try:
                        new_lang_name = self.current_voice.name.split("-")[1].split()[0]
                    except: new_lang_name = "Selected"
                    print("Language changed to {}.".format(new_lang_name))
                    break
                else:
                    print("Invalid choice. Please select a number from the list.")
            except ValueError:
                print("Invalid input. Please enter a number.")
            except Exception as e:
                print("Error setting new language: {}".format(e))
                break

    def generate_speech_audio(
        self,
        text_content_map: Dict[str, str], # chapter_name -> chapter_text
        output_folder_path: str,
        file_type: str, # To determine naming convention (TXT vs others)
    ) -> None:
        """
        Generates MP3 audio files from the given text content.
        For 'TXT', files are named directly. For others, they are numbered.
        """
        if not self.engine or not self.current_voice:
            print("Text-to-speech engine is not available. Cannot generate audio.")
            return

        if not os.path.exists(output_folder_path):
            try:
                os.makedirs(output_folder_path, exist_ok=True)
            except OSError as e:
                print("Error creating output directory {}: {}".format(output_folder_path, e))
                return

        item_count = 0
        total_items = len(text_content_map)

        for item_name, text_to_read in text_content_map.items():
            item_count += 1
            print(
                "\nProcessing item {} of {}: {}...".format(
                    item_count, total_items, item_name
                )
            )

            base_mp3_filename = item_name + ".mp3"
            if file_type.upper() == "TXT":
                # For TXT, item_name is the original filename (without .txt)
                # Output path is directly in the 'single_file_mp3_library/'
                final_output_path = os.path.join(output_folder_path, base_mp3_filename)
            else:
                # For EPUB/PDF, item_name is the chapter name/number
                # Files are numbered and placed in a book-specific subfolder
                # e.g., my_mp3_books_library/BookTitle/001 - ChapterName.mp3
                padded_count = "{:03d}".format(item_count)
                final_mp3_filename = "{} - {}".format(padded_count, base_mp3_filename)
                final_output_path = os.path.join(output_folder_path, final_mp3_filename)

            try:
                # Ensure engine has the correct voice set (might be redundant if not changed elsewhere)
                self.engine.setProperty("voice", self.current_voice.id)
                self.engine.save_to_file(text_to_read, final_output_path)
                self.engine.runAndWait()
                print("Successfully saved: {}".format(final_output_path))
            except RuntimeError as e:
                print("RuntimeError generating audio for {}: {}".format(item_name, e))
            except Exception as e:
                print("Unexpected error generating audio for {}: {}".format(item_name, e))

# Remove the old Voice class if it's no longer needed.
# Based on the refactoring, its `read` method is now `VoiceManager.generate_speech_audio`.

__all__ = ['VoiceManager', 'load_voice_config', 'save_voice_config']
