import json
import os  # For checking/creating mp3_books_library


class AppData:
    def __init__(self):
        self.config_file_path = 'configs.json'
        default_mp3_dir = "mp3_books_library"

        default_config = {
            "mp3_directory": default_mp3_dir,
            "voice_id": None,
            "speed_rate": 150,
            "ui_language": "en"  # Default UI language ('en', 'es', etc.)
        }

        # Ensure default mp3_directory exists
        if not os.path.exists(default_mp3_dir):
            try:
                os.mkdir(default_mp3_dir)
                print(f"Info: Created default MP3 directory '{default_mp3_dir}'.")
            except OSError as e:
                print(f"Warning: Could not create default MP3 directory '{default_mp3_dir}': {e}")
                default_config["mp3_directory"] = "."

        loaded_successfully = False
        config_needs_rewrite = False

        try:
            with open(self.config_file_path, 'r') as openfile:
                json_object = json.load(openfile)
                # Check if it's a dict. Key check will be done later.
                if isinstance(json_object, dict):
                    self.data = json_object
                    # Validate mp3_directory existence
                    if not os.path.isdir(self.data.get("mp3_directory", default_mp3_dir)):
                        print(
                            f"Warning: Configured mp3_directory '{self.data.get('mp3_directory')}' does not exist. Resetting to default.")
                        self.data["mp3_directory"] = default_mp3_dir
                        config_needs_rewrite = True
                    loaded_successfully = True
                else:
                    print("Warning: config.json is malformed (not a dict). Using default configuration.")
                    config_needs_rewrite = True  # Mark to save defaults
        except FileNotFoundError:
            print("Info: config.json not found. Creating with default configuration.")
            config_needs_rewrite = True
        except json.JSONDecodeError:
            print("Warning: config.json is not valid JSON. Using default configuration.")
            config_needs_rewrite = True
        except Exception as e:
            print(f"Error loading config.json: {e}. Using default configuration.")
            config_needs_rewrite = True

        if not loaded_successfully:
            self.data = default_config.copy()

        # Ensure all default keys are present and potentially add new ones
        for key, value in default_config.items():
            if key not in self.data:
                print(f"Info: Adding missing key '{key}' with default value '{value}' to config.")
                self.data[key] = value
                config_needs_rewrite = True
            # Optional: Type check existing values and reset if wrong, though this can be complex
            # For example, if self.data["speed_rate"] is a string, try to convert or reset.
            # For now, we assume consuming code handles type errors gracefully or AppData init does.

        if config_needs_rewrite:
            self.save_changes(self.data)  # Save defaults/updated config

    def save_changes(self, new_data):
        self.data = new_data
        try:
            with open(self.config_file_path, "w") as save_file:
                json.dump(self.data, save_file, indent=4)
        except IOError as e:
            print(f"Error saving configuration to {self.config_file_path}: {e}")
        except Exception as e:
            print(f"An unexpected error occurred while saving configuration: {e}")
