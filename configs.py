import json
import os # For checking/creating mp3_books_library

class AppData:
    def __init__(self):
        self.config_file_path = 'configs.json'
        default_mp3_dir = "mp3_books_library"
        
        default_config = {
            "mp3_directory": default_mp3_dir,
            "language": 0,      # Default language index
            "speed_rate": 150   # Default speed rate
        }
        
        # Ensure default mp3_directory exists
        if not os.path.exists(default_mp3_dir):
            try:
                os.mkdir(default_mp3_dir)
                print(f"Info: Created default MP3 directory '{default_mp3_dir}'.")
            except OSError as e:
                print(f"Warning: Could not create default MP3 directory '{default_mp3_dir}': {e}")
                # Fallback to current directory if creation fails for some reason
                default_config["mp3_directory"] = "." 

        loaded_successfully = False
        config_needs_rewrite = False # Flag to indicate if save_changes should be called

        try:
            with open(self.config_file_path, 'r') as openfile:
                json_object = json.load(openfile)
                # Basic validation: check if it's a dict and has all expected keys
                if isinstance(json_object, dict) and all(key in json_object for key in default_config.keys()):
                    # Further check if types are correct, if desired, or handle in consuming code
                    self.data = json_object
                    # Check if loaded mp3_directory exists, if not, reset to default and mark for rewrite
                    if not os.path.isdir(self.data.get("mp3_directory", default_mp3_dir)):
                        print(f"Warning: Configured mp3_directory '{self.data.get('mp3_directory')}' does not exist or is not a directory. Resetting to default.")
                        self.data["mp3_directory"] = default_mp3_dir
                        config_needs_rewrite = True
                    loaded_successfully = True
                else:
                    print("Warning: config.json is malformed (not a dict or missing keys). Using default configuration.")
                    config_needs_rewrite = True # Mark to save defaults
        except FileNotFoundError:
            print("Info: config.json not found. Creating with default configuration.")
            config_needs_rewrite = True # Mark to save defaults
        except json.JSONDecodeError:
            print("Warning: config.json is not valid JSON. Using default configuration.")
            config_needs_rewrite = True # Mark to save defaults
        except Exception as e: # Catch other potential errors during file load
            print(f"Error loading config.json: {e}. Using default configuration.")
            config_needs_rewrite = True


        if not loaded_successfully:
            self.data = default_config.copy() # Use a copy for self.data
        
        # Ensure all default keys are present in self.data if loaded from file but was incomplete
        # This also handles cases where new default keys are added to the app
        for key, value in default_config.items():
            if key not in self.data:
                print(f"Info: Adding missing key '{key}' with default value '{value}' to config.")
                self.data[key] = value
                config_needs_rewrite = True


        if config_needs_rewrite:
            self.save_changes(self.data) # Save defaults/updated config if file was missing, corrupt, or updated

    def save_changes(self, new_data): 
        """Saves the provided data dictionary to the config file."""
        # It's generally better practice for save_changes to save self.data,
        # and have other methods update self.data.
        # However, to match flet-app.py's call `data.save_changes(data.data)`,
        # this method takes new_data. If new_data is intended to update self.data,
        # it should be assigned: self.data = new_data before saving.
        # For now, just saving what's passed.
        try:
            with open(self.config_file_path, "w") as save_file: # Renamed save_data to save_file
                json.dump(new_data, save_file, indent=4)
        except IOError as e:
            print(f"Error saving configuration to {self.config_file_path}: {e}")
        except Exception as e: # Catch other potential errors during save
            print(f"An unexpected error occurred while saving configuration: {e}")
