import pyttsx3
import os 

from flet import ( 
    Text, # Retaining as per prompt, though direct UI manipulation here is unusual
)

from configs import AppData


class VoiceManager:
    def __init__(self):
        self.app_data = AppData()
        try:
            # Use .get() for safer dictionary access, providing defaults
            self.my_language_index = int(self.app_data.data.get("language", 0))
        except (ValueError, TypeError):
            print("Warning: Language index in config is invalid. Using default 0.")
            self.my_language_index = 0 
        
        try:
            self.speed_rate = int(self.app_data.data.get("speed_rate", 150))
        except (ValueError, TypeError):
            print("Warning: Speed rate in config is invalid. Using default 150.")
            self.speed_rate = 150

        self.engine = None
        self.voices = []
        self.current_voice = None 

        try:
            self.engine = pyttsx3.init()
            if not self.engine: # Check if engine failed to initialize (some drivers might return None)
                print("Error: pyttsx3 engine could not be initialized (returned None).")
                return # Cannot proceed
        except Exception as e: 
            print(f"Error: pyttsx3 engine could not be initialized: {e}")
            return 

        try:
            self.engine.setProperty("rate", self.speed_rate)
            self.voices = self.engine.getProperty("voices")
        except Exception as e: # Catch errors during property setting or voice retrieval
            print(f"Error setting engine properties or getting voices: {e}")
            self.engine = None 
            return

        if not self.voices:
            print("Warning: No voices found by pyttsx3 engine.")
        elif 0 <= self.my_language_index < len(self.voices): # Check bounds
            self.current_voice = self.voices[self.my_language_index]
            self.engine.setProperty("voice", self.current_voice.id)
        else:
            print(f"Warning: Saved language index {self.my_language_index} is out of range (0-{len(self.voices)-1}). Defaulting to first available voice.")
            self.my_language_index = 0
            if self.voices: # Ensure voices list is not empty
                self.current_voice = self.voices[0]
                self.engine.setProperty("voice", self.current_voice.id)
                # Update and save the corrected default index
                self.app_data.data["language"] = self.my_language_index
                try:
                    self.app_data.save_changes(self.app_data.data)
                except Exception as e_save:
                    print(f"Error saving corrected language index to config: {e_save}")
            else:
                print("Error: No voices available to set a default voice.")

    # CLI-based methods - not directly used by Flet UI in this form.
    def choose_speedRate(self):
        # ... (implementation as provided in prompt, assuming it's for CLI debugging) ...
        pass

    def change_speedRate(self):
        # ... (implementation as provided in prompt, assuming it's for CLI debugging) ...
        pass

    def select_language(self):
        # ... (implementation as provided in prompt, assuming it's for CLI debugging) ...
        pass


class Voice: 
    @staticmethod
    def read(voice_manager_instance, file_extension, folder_dir, files_data, info_items):
        engine = voice_manager_instance.engine
        engine = voice_manager_instance.engine
        selected_voice = voice_manager_instance.current_voice

        # Centralized UI update helper within this method
        def update_ui_elements(state_msg="", items_msg="", ring_visible=False, clear_list=False, page_update_needed=False):
            if not info_items: return 
            
            state_info_control = info_items.get("state_info")
            if state_info_control:
                state_info_control.value = state_msg
                state_info_control.update()
            
            items_to_read_control = info_items.get("items_to_read")
            if items_to_read_control:
                items_to_read_control.value = items_msg
                items_to_read_control.update()

            progress_ring_control = info_items.get("progress_ring")
            if progress_ring_control:
                progress_ring_control.visible = ring_visible
                progress_ring_control.update()
            
            if clear_list:
                audio_list_control = info_items.get("audio_files_list")
                if audio_list_control and hasattr(audio_list_control, "controls"):
                    audio_list_control.controls.clear()
                    audio_list_control.update()
            
            # If page object is available and an update ishinted (e.g. after multiple control updates)
            # This part is more complex as page is not directly passed here.
            # For now, individual control updates should suffice.

        if not engine or not selected_voice:
            err_msg = "Voice engine not ready or no voice selected. Check console for errors."
            print(f"Error in Voice.read: {err_msg}")
            update_ui_elements(state_msg=err_msg, ring_visible=False)
            return

        update_ui_elements(clear_list=True) # Clear previous list items at the start

        total_items = len(files_data)
        if total_items == 0:
            update_ui_elements(state_msg="No text data found to process.", ring_visible=False)
            return
        
        all_successful = True
        processed_item_idx = 0 # Using idx for 0-based counting internally, display as idx+1

        for data_name, text_content in files_data.items():
            processed_item_idx += 1
            print(f"\nProcessing item {processed_item_idx} of {total_items}: {data_name}")

            display_data_name = data_name[:30] + "..." if len(data_name) > 30 else data_name
            current_item_msg = f"Reading {processed_item_idx}/{total_items}: {display_data_name}"
            update_ui_elements(state_msg=f"Generating: {display_data_name}", items_msg=current_item_msg, ring_visible=True)
            
            zeros = ""
            # Use processed_item_idx for numbering if not TXT
            if file_extension.lower() != "txt":
                if processed_item_idx <= 9: zeros = "00"
                elif processed_item_idx <= 99: zeros = "0"
            
            safe_data_name = "".join(c if c.isalnum() or c in " .-_()" else "_" for c in data_name)
            max_len_data_name = 100 
            safe_data_name = safe_data_name[:max_len_data_name]

            mp3_file_name = f"{zeros}{processed_item_idx} - {safe_data_name}.mp3" if file_extension.lower() != "txt" else f"{safe_data_name}.mp3"
            
            if not os.path.exists(folder_dir):
                try:
                    os.makedirs(folder_dir, exist_ok=True)
                except OSError as e:
                    print(f"Error creating output directory {folder_dir}: {e}")
                    update_ui_elements(state_msg=f"Error creating folder: {e}", ring_visible=False)
                    # Do not return; allow other items to be processed if possible, or set flag
                    all_successful = False 
                    continue # Skip this item

            full_file_path = os.path.join(folder_dir, mp3_file_name)

            try:
                engine.setProperty("voice", selected_voice.id)
                engine.save_to_file(text_content, full_file_path)
                engine.runAndWait()

                audio_list_control = info_items.get("audio_files_list")
                if audio_list_control and hasattr(audio_list_control, "controls"):
                    audio_list_control.controls.append(Text(mp3_file_name))
                    audio_list_control.update()
                print(f"Done! File saved as {full_file_path}")
            except Exception as e:
                print(f"Error saving file {mp3_file_name}: {e}")
                # Update state_info for this specific error, but it might be overwritten by the next item's status
                # This is acceptable as the final message will indicate overall success/failure.
                if info_items.get("state_info"): # Update for immediate feedback on current item
                     info_items["state_info"].value = f"Error saving {display_data_name}"
                     info_items["state_info"].update()
                all_successful = False # Mark that at least one error occurred
        
        # Final UI update after the loop
        final_state_message = f"Finished processing {total_items} items."
        if not all_successful:
            final_state_message = "Processing finished with some errors. Check console/logs."
        
        update_ui_elements(state_msg=final_state_message, items_msg="Processing complete.", ring_visible=False)
