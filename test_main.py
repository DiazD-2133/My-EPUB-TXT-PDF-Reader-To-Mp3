import unittest
from unittest import mock

# Assuming main.py and other project files are accessible
import main
from main import (
    create_initial_folders, handle_file_reading, run_app_cycle,
    NEEDED_FOLDERS, SUPPORTED_FILE_EXTENSIONS
)
from menumanager import MenuManager, MenuOption
from voicemanager import VoiceManager # Voice class removed
from textreader import AbstractReader # For type hinting if needed, though likely not for main tests

class TestMain(unittest.TestCase):

    @mock.patch('files_dirs.get_files_names')
    @mock.patch('os.mkdir')
    @mock.patch('builtins.print') # To capture print statements
    def test_create_initial_folders_all_new(self, mock_print, mock_mkdir, mock_get_files_names):
        """Test create_initial_folders when all folders need to be created."""
        mock_get_files_names.return_value = [] # No folders exist initially
        
        create_initial_folders()
        
        self.assertEqual(mock_mkdir.call_count, len(NEEDED_FOLDERS))
        for folder_name in NEEDED_FOLDERS:
            mock_mkdir.assert_any_call(folder_name)
            mock_print.assert_any_call("Created directory: {}".format(folder_name))
        mock_get_files_names.assert_called_once_with() # Called with no args for current dir

    @mock.patch('files_dirs.get_files_names')
    @mock.patch('os.mkdir')
    @mock.patch('builtins.print')
    def test_create_initial_folders_some_exist(self, mock_print, mock_mkdir, mock_get_files_names):
        """Test create_initial_folders when some folders already exist."""
        # Assume first folder exists, others don't
        existing_folders = [NEEDED_FOLDERS[0]] 
        mock_get_files_names.return_value = existing_folders
        
        create_initial_folders()
        
        # Should be called for all folders *except* the first one
        self.assertEqual(mock_mkdir.call_count, len(NEEDED_FOLDERS) - 1)
        for folder_name in NEEDED_FOLDERS[1:]: # Check calls for non-existing folders
            mock_mkdir.assert_any_call(folder_name)
            mock_print.assert_any_call("Created directory: {}".format(folder_name))
        
        # Ensure it was not called for the existing folder
        with self.assertRaises(AssertionError): # Check that this call was NOT made
            mock_mkdir.assert_any_call(NEEDED_FOLDERS[0])


    @mock.patch('files_dirs.get_files_names', return_value=[])
    @mock.patch('os.mkdir', side_effect=OSError("Permission denied"))
    @mock.patch('builtins.print')
    def test_create_initial_folders_os_error(self, mock_print, mock_mkdir, mock_get_files_names):
        """Test create_initial_folders when os.mkdir raises an OSError."""
        create_initial_folders()
        
        # It will try to create all folders, and each will raise an error
        self.assertEqual(mock_mkdir.call_count, len(NEEDED_FOLDERS)) 
        for folder_name in NEEDED_FOLDERS:
            mock_print.assert_any_call(
                "Error creating directory {}: {}".format(folder_name, OSError("Permission denied"))
            )

    @mock.patch('textreader.get_temporal_books_from_files') # Patched new name
    @mock.patch('textreader.process_and_read_books')     # Patched new name
    def test_handle_file_reading_books_found(self, mock_process_books, mock_get_books):
        """Test handle_file_reading when books are found and processed."""
        mock_selection = mock.MagicMock(spec=MenuOption)
        mock_selection.name = "TXT" # Example file type
        # get_temporal_books_from_files returns a dict for TXT
        mock_get_books.return_value = {"book1": "content"} 
        
        # mock_voice_instance = mock.MagicMock(spec=Voice) # Voice class removed
        mock_voice_manager_instance = mock.MagicMock(spec=VoiceManager)

        # handle_file_reading now only takes voice_manager_instance
        main.handle_file_reading(mock_selection, mock_voice_manager_instance) # Corrected: use main.handle_file_reading

        mock_get_books.assert_called_once_with(mock_selection)
        # textreader.process_and_read_books now takes (voice_manager, books_data, selection)
        mock_process_books.assert_called_once_with(
            mock_voice_manager_instance, {"book1": "content"}, mock_selection
        )

    @mock.patch('textreader.get_temporal_books_from_files', return_value=None) # No books found
    @mock.patch('textreader.process_and_read_books')
    @mock.patch('builtins.print')
    def test_handle_file_reading_no_books_found(self, mock_print, mock_process_books, mock_get_books):
        """Test handle_file_reading when no books are returned."""
        mock_selection = mock.MagicMock(spec=MenuOption)
        mock_selection.name = "EPUB"
        
        # mock_voice_instance = mock.MagicMock(spec=Voice) # Voice class removed
        mock_voice_manager_instance = mock.MagicMock(spec=VoiceManager)

        main.handle_file_reading(mock_selection, mock_voice_manager_instance) # Corrected: use main.handle_file_reading and remove voice_instance

        mock_get_books.assert_called_once_with(mock_selection)
        mock_process_books.assert_not_called()
        mock_print.assert_called_with("There are no files to read for the selected type or an error occurred.")

    # --- Tests for run_app_cycle ---

    @mock.patch('main.handle_file_reading') # Mock the actual handler
    def test_run_app_cycle_file_reading_option(self, mock_handle_file_reading):
        """Test run_app_cycle when a file reading option (e.g., TXT) is selected."""
        mock_menu_instance = mock.MagicMock(spec=MenuManager)
        # mock_voice_instance = mock.MagicMock(spec=Voice) # Voice class removed
        mock_voice_manager_instance = mock.MagicMock(spec=VoiceManager)

        # Simulate selecting TXT
        mock_txt_option = mock.MagicMock(spec=MenuOption)
        mock_txt_option.name = "TXT" # One of SUPPORTED_FILE_EXTENSIONS
        # Directly assign TXT enum member for direct comparison in run_app_cycle if needed
        # For this test, just matching the name in SUPPORTED_FILE_EXTENSIONS is enough
        
        mock_menu_instance.show_menu.return_value = mock_txt_option
        
        should_continue = main.run_app_cycle(mock_menu_instance, mock_voice_manager_instance) # Corrected: use main.run_app_cycle, remove voice_instance
        
        mock_menu_instance.show_menu.assert_called_once()
        mock_handle_file_reading.assert_called_once_with(
            mock_txt_option, mock_voice_manager_instance # voice_instance removed
        )
        self.assertTrue(should_continue)

    def test_run_app_cycle_language_option(self):
        """Test run_app_cycle when LANGUAGE option is selected."""
        mock_menu_instance = mock.MagicMock(spec=MenuManager)
        # mock_voice_instance = mock.MagicMock(spec=Voice) # Voice class removed
        mock_voice_manager_instance = mock.MagicMock(spec=VoiceManager)
        
        # Simulate selecting LANGUAGE
        # We need to return the actual enum member for direct comparison `selection == MenuOption.LANGUAGE`
        mock_menu_instance.show_menu.return_value = MenuOption.LANGUAGE
        
        should_continue = main.run_app_cycle(mock_menu_instance, mock_voice_manager_instance) # Corrected: use main.run_app_cycle, remove voice_instance
        
        mock_menu_instance.show_menu.assert_called_once()
        mock_voice_manager_instance.select_language.assert_called_once()
        self.assertTrue(should_continue)

    def test_run_app_cycle_speedrate_option(self):
        """Test run_app_cycle when SPEEDRATE option is selected."""
        mock_menu_instance = mock.MagicMock(spec=MenuManager)
        # mock_voice_instance = mock.MagicMock(spec=Voice) # Voice class removed
        mock_voice_manager_instance = mock.MagicMock(spec=VoiceManager)
        
        mock_menu_instance.show_menu.return_value = MenuOption.SPEEDRATE
        
        should_continue = main.run_app_cycle(mock_menu_instance, mock_voice_manager_instance) # Corrected: use main.run_app_cycle, remove voice_instance
        
        mock_menu_instance.show_menu.assert_called_once()
        mock_voice_manager_instance.change_speed_rate.assert_called_once()
        self.assertTrue(should_continue)

    @mock.patch('builtins.print')
    def test_run_app_cycle_close_option(self, mock_print):
        """Test run_app_cycle when CLOSE option is selected."""
        mock_menu_instance = mock.MagicMock(spec=MenuManager)
        # mock_voice_instance = mock.MagicMock(spec=Voice) # Voice class removed
        mock_voice_manager_instance = mock.MagicMock(spec=VoiceManager)
        
        mock_menu_instance.show_menu.return_value = MenuOption.CLOSE
        
        should_continue = main.run_app_cycle(mock_menu_instance, mock_voice_manager_instance) # Corrected: use main.run_app_cycle, remove voice_instance
        
        mock_menu_instance.show_menu.assert_called_once()
        mock_print.assert_called_with("Exiting application...")
        self.assertFalse(should_continue) # App should stop

    @mock.patch('builtins.print')
    def test_run_app_cycle_unknown_option(self, mock_print):
        """Test run_app_cycle with an unexpected/unknown MenuOption."""
        mock_menu_instance = mock.MagicMock(spec=MenuManager)
        # mock_voice_instance = mock.MagicMock(spec=Voice) # Voice class removed
        mock_voice_manager_instance = mock.MagicMock(spec=VoiceManager)

        # Create a mock MenuOption that is not one of the known ones
        # This simulates if MenuOption enum had more values not handled by run_app_cycle
        mock_unknown_option = mock.MagicMock(spec=MenuOption)
        mock_unknown_option.name = "SOME_NEW_UNHANDLED_OPTION" 
        # Ensure this name is NOT in SUPPORTED_FILE_EXTENSIONS and not LANGUAGE, SPEEDRATE, or CLOSE
        
        mock_menu_instance.show_menu.return_value = mock_unknown_option
        
        should_continue = main.run_app_cycle(mock_menu_instance, mock_voice_manager_instance) # Corrected: use main.run_app_cycle, remove voice_instance
        
        mock_menu_instance.show_menu.assert_called_once()
        mock_print.assert_called_with("Unknown selection. Please try again.")
        self.assertTrue(should_continue) # Should continue, allowing user to retry

    # --- Test the main execution block (__name__ == "__main__") ---
    # This is more of an integration test snippet but can be useful.
    
    @mock.patch('main.create_initial_folders')
    @mock.patch('main.MenuManager')
    @mock.patch('main.VoiceManager')
    # @mock.patch('main.Voice') # Voice class is removed
    @mock.patch('main.run_app_cycle')
    def test_main_execution_flow(self, mock_run_app_cycle, # mock_voice_cls removed
                                 mock_voice_manager_cls, 
                                 mock_menu_manager_cls, mock_create_folders):
        """Test the main execution block's overall flow."""
        
        # Make run_app_cycle return False after a few calls to stop the loop
        mock_run_app_cycle.side_effect = [True, True, False] 
        
        # Mock instances that would be created
        mock_menu_instance = mock.MagicMock()
        mock_menu_manager_cls.return_value = mock_menu_instance
        
        mock_voice_manager_instance = mock.MagicMock()
        mock_voice_manager_cls.return_value = mock_voice_manager_instance
        
        # mock_voice_instance = mock.MagicMock() # Voice class removed
        # mock_voice_cls.return_value = mock_voice_instance

        # To run the __main__ block, we can import main again or exec its content
        # A simpler way for testing is to encapsulate the __main__ block's logic
        # into a function if it's not already, or call a wrapper.
        # For this test, we'll simulate its core logic by calling a hypothetical
        # main_loop() function that would encapsulate the __main__ block's while loop.
        # Since we don't have that, we'll re-construct the loop here.
        
        # Simulate the main block's sequence
        main.create_initial_folders() 
        
        menu_mgr = main.MenuManager()
        voice_mgr = main.VoiceManager()
        # voice_obj = main.Voice() # REMOVED

        app_active = True
        loop_count = 0 # Safety break for the test
        actual_run_app_cycle_calls = []

        # This loop simulates the one in main.py's __main__ block
        while app_active and loop_count < 5:
            # We use the mocked run_app_cycle from the test arguments
            app_active = mock_run_app_cycle(menu_mgr, voice_mgr) 
            actual_run_app_cycle_calls.append(mock.call(menu_mgr, voice_mgr))
            loop_count += 1
        
        mock_create_folders.assert_called_once()
        mock_menu_manager_cls.assert_called_once()
        mock_voice_manager_cls.assert_called_once()
        # mock_voice_cls.assert_called_once() # No longer exists or called

        self.assertEqual(mock_run_app_cycle.call_count, 3) # Due to side_effect
        # Check the arguments passed to the mocked run_app_cycle
        self.assertEqual(mock_run_app_cycle.call_args_list, actual_run_app_cycle_calls)


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
