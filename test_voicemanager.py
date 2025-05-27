import unittest
from unittest import mock
import json
import os # For os.path.join in generate_speech_audio tests

# Assuming voicemanager.py is in the same directory or accessible in PYTHONPATH
import voicemanager 
from voicemanager import VoiceManager, load_voice_config, save_voice_config, VOICE_CONFIG_FILE, DEFAULT_LANGUAGE_INDEX, DEFAULT_SPEED_RATE

class TestVoiceConfig(unittest.TestCase):

    def tearDown(self):
        """Clean up by removing the config file if it was created."""
        if os.path.exists(VOICE_CONFIG_FILE):
            os.remove(VOICE_CONFIG_FILE)

    @mock.patch('builtins.open', new_callable=mock.mock_open)
    @mock.patch('json.dump')
    def test_save_voice_config_success(self, mock_json_dump, mock_open):
        """Test successful saving of voice configuration."""
        lang_idx, speed = 1, 180
        save_voice_config(lang_idx, speed)

        mock_open.assert_called_once_with(VOICE_CONFIG_FILE, "w")
        mock_json_dump.assert_called_once_with(
            {"language_index": lang_idx, "speed_rate": speed},
            mock_open.return_value, # The file handle
            indent=4
        )

    @mock.patch('builtins.open', side_effect=IOError("Failed to write"))
    @mock.patch('builtins.print') # To capture error messages
    def test_save_voice_config_io_error(self, mock_print, mock_open):
        """Test save_voice_config when an IOError occurs."""
        save_voice_config(0, 150)
        mock_open.assert_called_once_with(VOICE_CONFIG_FILE, "w")
        mock_print.assert_called_with(
            "Error saving voice configuration to {}: {}".format(VOICE_CONFIG_FILE, IOError("Failed to write"))
        )

    @mock.patch('builtins.open', new_callable=mock.mock_open, read_data='{"language_index": 1, "speed_rate": 175}')
    @mock.patch('json.load')
    def test_load_voice_config_success(self, mock_json_load, mock_open):
        """Test successful loading of voice configuration."""
        mock_json_load.return_value = {"language_index": 1, "speed_rate": 175}
        
        lang_idx, speed = load_voice_config()
        
        mock_open.assert_called_once_with(VOICE_CONFIG_FILE, "r")
        mock_json_load.assert_called_once_with(mock_open.return_value)
        self.assertEqual(lang_idx, 1)
        self.assertEqual(speed, 175)

    @mock.patch('builtins.open', side_effect=FileNotFoundError)
    @mock.patch('voicemanager.save_voice_config') # Mock save_voice_config to check if it's called
    @mock.patch('builtins.print')
    def test_load_voice_config_file_not_found(self, mock_print, mock_save_config, mock_open):
        """Test load_voice_config when the config file is not found."""
        lang_idx, speed = load_voice_config()
        
        mock_open.assert_called_once_with(VOICE_CONFIG_FILE, "r")
        self.assertEqual(lang_idx, DEFAULT_LANGUAGE_INDEX)
        self.assertEqual(speed, DEFAULT_SPEED_RATE)
        mock_print.assert_any_call( # Use any_call if other prints might occur
            "Warning: {} not found. Using default voice settings and creating file.".format(VOICE_CONFIG_FILE)
        )
        mock_save_config.assert_called_once_with(DEFAULT_LANGUAGE_INDEX, DEFAULT_SPEED_RATE)

    @mock.patch('builtins.open', new_callable=mock.mock_open, read_data='{"invalid_json": true')
    @mock.patch('json.load', side_effect=json.JSONDecodeError("Error", "doc", 0))
    @mock.patch('voicemanager.save_voice_config')
    @mock.patch('builtins.print')
    def test_load_voice_config_json_decode_error(self, mock_print, mock_save_config, mock_json_load, mock_open):
        """Test load_voice_config with corrupted JSON data."""
        lang_idx, speed = load_voice_config()
        
        self.assertEqual(lang_idx, DEFAULT_LANGUAGE_INDEX)
        self.assertEqual(speed, DEFAULT_SPEED_RATE)
        mock_print.assert_any_call(
            "Warning: Invalid data in {}: {}. Using defaults and recreating file.".format(
                VOICE_CONFIG_FILE, json.JSONDecodeError("Error", "doc", 0)
            )
        )
        mock_save_config.assert_called_once_with(DEFAULT_LANGUAGE_INDEX, DEFAULT_SPEED_RATE)

    @mock.patch('builtins.open', new_callable=mock.mock_open, read_data='{"language_index": "not_an_int", "speed_rate": 150}')
    @mock.patch('json.load') # Mock json.load to return the problematic data
    @mock.patch('voicemanager.save_voice_config')
    @mock.patch('builtins.print')
    def test_load_voice_config_value_error(self, mock_print, mock_save_config, mock_json_load_actual, mock_open):
        """Test load_voice_config when data types are incorrect (ValueError during int conversion)."""
        # Configure the mock for json.load to return the specific problematic dictionary
        mock_json_load_actual.return_value = {"language_index": "not_an_int", "speed_rate": 150}

        lang_idx, speed = load_voice_config()

        self.assertEqual(lang_idx, DEFAULT_LANGUAGE_INDEX)
        self.assertEqual(speed, DEFAULT_SPEED_RATE)
        # The print message will show the specific ValueError
        # We can check if 'Warning: Invalid data' was part of the print
        self.assertTrue(any("Warning: Invalid data" in call_args[0][0] for call_args in mock_print.call_args_list))
        mock_save_config.assert_called_once_with(DEFAULT_LANGUAGE_INDEX, DEFAULT_SPEED_RATE)


class TestVoiceManager(unittest.TestCase):

    @mock.patch('voicemanager.load_voice_config')
    @mock.patch('pyttsx3.init')
    def setUp(self, mock_pyttsx3_init, mock_load_config):
        """Set up a VoiceManager instance with mocked dependencies."""
        # Mock load_voice_config to return default values
        mock_load_config.return_value = (DEFAULT_LANGUAGE_INDEX, DEFAULT_SPEED_RATE)

        # Mock pyttsx3.init()
        self.mock_engine_instance = mock.MagicMock()
        mock_pyttsx3_init.return_value = self.mock_engine_instance

        # Mock voices
        self.mock_voice_en = mock.MagicMock()
        self.mock_voice_en.name = "EnglishVoice-EN"
        self.mock_voice_en.id = "en_id"
        
        self.mock_voice_es = mock.MagicMock()
        self.mock_voice_es.name = "SpanishVoice-ES"
        self.mock_voice_es.id = "es_id"

        self.mock_engine_instance.getProperty.return_value = [self.mock_voice_en, self.mock_voice_es]
        
        self.vm = VoiceManager()
        # Ensure load_config was called during VoiceManager init
        mock_load_config.assert_called_once() 
        mock_pyttsx3_init.assert_called_once()

    def test_initialization_success(self):
        """Test successful initialization of VoiceManager."""
        self.assertIsNotNone(self.vm.engine)
        self.assertEqual(self.vm.language_index, DEFAULT_LANGUAGE_INDEX)
        self.assertEqual(self.vm.speed_rate, DEFAULT_SPEED_RATE)
        self.assertEqual(len(self.vm.voices), 2)
        self.assertEqual(self.vm.current_voice, self.mock_voice_en)
        self.mock_engine_instance.setProperty.assert_any_call("rate", DEFAULT_SPEED_RATE)
        self.mock_engine_instance.setProperty.assert_any_call("voice", self.mock_voice_en.id)

    @mock.patch('voicemanager.load_voice_config', return_value=(1, 180)) # Saved index 1
    @mock.patch('pyttsx3.init')
    def test_initialization_with_saved_valid_config(self, mock_pyttsx3_init_custom, mock_load_config_custom):
        """Test initialization with a valid saved non-default language index."""
        mock_engine = mock.MagicMock()
        mock_pyttsx3_init_custom.return_value = mock_engine
        mock_voice1 = mock.MagicMock(id='v1', name='Voice1-Lang1')
        mock_voice2 = mock.MagicMock(id='v2', name='Voice2-Lang2')
        mock_engine.getProperty.return_value = [mock_voice1, mock_voice2]

        vm = VoiceManager()
        self.assertEqual(vm.language_index, 1)
        self.assertEqual(vm.speed_rate, 180)
        self.assertEqual(vm.current_voice, mock_voice2) # Index 1
        mock_engine.setProperty.assert_any_call("voice", mock_voice2.id)
        mock_engine.setProperty.assert_any_call("rate", 180)

    @mock.patch('voicemanager.load_voice_config', return_value=(99, 180)) # Invalid index
    @mock.patch('pyttsx3.init')
    @mock.patch('voicemanager.save_voice_config') # To check if it corrects and saves
    @mock.patch('builtins.print')
    def test_initialization_with_invalid_saved_language_index(self, mock_print, mock_save_conf, mock_pyttsx3_init_invalid, mock_load_conf_invalid):
        """Test initialization with an out-of-bounds saved language index."""
        mock_engine = mock.MagicMock()
        mock_pyttsx3_init_invalid.return_value = mock_engine
        mock_voice1 = mock.MagicMock(id='v1', name='Voice1-Lang1')
        mock_engine.getProperty.return_value = [mock_voice1] # Only one voice

        vm = VoiceManager()
        self.assertEqual(vm.language_index, DEFAULT_LANGUAGE_INDEX) # Should reset to 0
        self.assertEqual(vm.current_voice, mock_voice1)
        mock_save_conf.assert_called_once_with(DEFAULT_LANGUAGE_INDEX, 180) # Saves corrected index
        mock_print.assert_any_call(
            "Warning: Saved language index 99 is invalid. Resetting to default {}.".format(DEFAULT_LANGUAGE_INDEX)
        )

    @mock.patch('pyttsx3.init', return_value=None) # Engine init fails
    @mock.patch('voicemanager.load_voice_config', return_value=(0,150))
    @mock.patch('builtins.print')
    def test_initialization_engine_init_fails(self, mock_print, mock_load_config, mock_init_fail):
        """Test initialization when pyttsx3.init() returns None."""
        vm = VoiceManager()
        self.assertIsNone(vm.engine)
        self.assertEqual(vm.voices, [])
        self.assertIsNone(vm.current_voice)
        mock_print.assert_any_call("Error: pyttsx3 engine could not be initialized.")

    @mock.patch('pyttsx3.init')
    @mock.patch('voicemanager.load_voice_config', return_value=(0,150))
    @mock.patch('builtins.print')
    def test_initialization_no_voices_available(self, mock_print, mock_load_config, mock_init_no_voices):
        """Test initialization when engine has no voices."""
        mock_engine = mock.MagicMock()
        mock_init_no_voices.return_value = mock_engine
        mock_engine.getProperty.return_value = [] # No voices

        vm = VoiceManager()
        self.assertIsNone(vm.engine) # Engine should be disabled
        self.assertEqual(vm.voices, [])
        self.assertIsNone(vm.current_voice)
        mock_print.assert_any_call("Error: No voices available on the system.")

    @mock.patch('pyttsx3.init', side_effect=RuntimeError("TTS Engine crashed"))
    @mock.patch('voicemanager.load_voice_config', return_value=(0,150))
    @mock.patch('builtins.print')
    def test_initialization_runtime_error(self, mock_print, mock_load_config, mock_init_runtime_error):
        """Test initialization when pyttsx3.init() raises RuntimeError."""
        vm = VoiceManager()
        self.assertIsNone(vm.engine)
        mock_print.assert_any_call("RuntimeError initializing text-to-speech engine: TTS Engine crashed")

    @mock.patch('builtins.input', side_effect=['y', '120'])
    @mock.patch('voicemanager.save_voice_config')
    def test_change_speed_rate_success(self, mock_save_config, mock_input):
        """Test successful change of speed rate."""
        initial_speed = self.vm.speed_rate
        self.vm.change_speed_rate()
        
        self.assertEqual(self.vm.speed_rate, 120)
        self.mock_engine_instance.setProperty.assert_called_with("rate", 120)
        mock_save_config.assert_called_once_with(self.vm.language_index, 120)
        self.assertNotEqual(self.vm.speed_rate, initial_speed)

    @mock.patch('builtins.input', side_effect=['y', 'abc', 'y', '10', 'y', '133']) # Covers all prompts
    @mock.patch('voicemanager.save_voice_config')
    @mock.patch('builtins.print')
    def test_change_speed_rate_invalid_inputs_then_valid(self, mock_print, mock_save_config, mock_input):
        """Test change_speed_rate with various invalid inputs before a valid one."""
        # Initial prompts:
        # 1. Change speed? (y/n) -> 'y'
        # 2. Enter speed: -> 'abc' (invalid)
        # 3. Try again? (y/n) -> 'y'
        # 4. Enter speed: -> '10' (out of range)
        # 5. Try again? (y/n) -> 'y'
        # 6. Enter speed: -> '133' (valid)
        
        self.vm.change_speed_rate()

        self.assertEqual(self.vm.speed_rate, 133)
        mock_save_config.assert_called_once_with(self.vm.language_index, 133)
        self.assertIn(mock.call("Invalid input. Please enter a number for the speed rate."), mock_print.call_args_list)
        self.assertIn(mock.call("Speed rate seems too low or high. Please choose a value between 50 and 500."), mock_print.call_args_list)
        self.assertEqual(mock_input.call_count, 6) # Ensure all inputs were consumed


    @mock.patch('builtins.input', side_effect=['n'])
    @mock.patch('voicemanager.save_voice_config')
    def test_change_speed_rate_decline(self, mock_save_config, mock_input):
        """Test declining to change speed rate."""
        initial_speed = self.vm.speed_rate
        self.vm.change_speed_rate()
        self.assertEqual(self.vm.speed_rate, initial_speed)
        mock_save_config.assert_not_called()

    @mock.patch('builtins.input', side_effect=['y', '2']) # Yes, then choose 2nd voice (Spanish)
    @mock.patch('voicemanager.save_voice_config')
    def test_select_language_success(self, mock_save_config, mock_input):
        """Test successful language selection."""
        self.vm.select_language()
        self.assertEqual(self.vm.language_index, 1) # Index 1 for Spanish
        self.assertEqual(self.vm.current_voice, self.mock_voice_es)
        self.mock_engine_instance.setProperty.assert_called_with("voice", self.mock_voice_es.id)
        mock_save_config.assert_called_once_with(1, self.vm.speed_rate)

    @mock.patch('builtins.input', side_effect=['n']) # Decline to change
    @mock.patch('voicemanager.save_voice_config')
    def test_select_language_decline(self, mock_save_config, mock_input):
        """Test declining to change language."""
        initial_lang_idx = self.vm.language_index
        self.vm.select_language()
        self.assertEqual(self.vm.language_index, initial_lang_idx)
        mock_save_config.assert_not_called()
    
    @mock.patch('builtins.input', side_effect=['y', '0']) # Yes, then cancel with 0
    @mock.patch('voicemanager.save_voice_config')
    def test_select_language_cancel_selection(self, mock_save_config, mock_input):
        """Test cancelling language selection after agreeing to change."""
        initial_lang_idx = self.vm.language_index
        self.vm.select_language()
        self.assertEqual(self.vm.language_index, initial_lang_idx) # Should not change
        mock_save_config.assert_not_called()


    @mock.patch('builtins.input', side_effect=['y', '99', 'y', '1']) # Invalid choice, then retry, then valid
    @mock.patch('voicemanager.save_voice_config')
    @mock.patch('builtins.print')
    def test_select_language_invalid_then_valid(self, mock_print, mock_save_config, mock_input):
        """Test selecting an invalid language number then a valid one."""
        # Original setup has lang_index 0 (English)
        self.vm.select_language() 
        self.assertEqual(self.vm.language_index, 0) # Stays English (index 0) after valid choice 1
        self.assertEqual(self.vm.current_voice, self.mock_voice_en)
        mock_save_config.assert_called_with(0, self.vm.speed_rate)
        mock_print.assert_any_call("Invalid choice. Please select a number from the list.")


    @mock.patch('os.path.exists') # Mock os.path.exists
    @mock.patch('os.makedirs') 
    def test_generate_speech_audio_txt_file(self, mock_makedirs, mock_exists):
        """Test generate_speech_audio for a TXT file type."""
        mock_exists.return_value = True # Assume output folder exists for this specific test part

        test_content = {"mybook": "This is a test."}
        output_folder = "single_mp3_folder/"
        file_type = "TXT"

        self.vm.generate_speech_audio(test_content, output_folder, file_type)

        # generate_speech_audio now calls os.path.exists(output_folder_path)
        mock_exists.assert_called_once_with(output_folder)
        mock_makedirs.assert_not_called() # Not called because mock_exists is True
        
        expected_path = os.path.join(output_folder, "mybook.mp3")
        self.mock_engine_instance.save_to_file.assert_called_once_with("This is a test.", expected_path)
        self.mock_engine_instance.runAndWait.assert_called_once()

    @mock.patch('os.path.exists', return_value=False)
    @mock.patch('os.makedirs')
    def test_generate_speech_audio_epub_file_creates_dir(self, mock_makedirs, mock_exists):
        """Test generate_speech_audio for EPUB, creating output directory."""
        test_content = {"chapter1": "Content chapter 1.", "chapter2": "Content chapter 2."}
        output_folder = "epub_mp3s/MyEPUB/" # This is the book-specific subfolder
        file_type = "EPUB"

        self.vm.generate_speech_audio(test_content, output_folder, file_type)

        mock_exists.assert_called_once_with(output_folder)
        mock_makedirs.assert_called_once_with(output_folder, exist_ok=True)
        
        expected_path1 = os.path.join(output_folder, "001 - chapter1.mp3")
        expected_path2 = os.path.join(output_folder, "002 - chapter2.mp3")
        
        calls = [
            mock.call("Content chapter 1.", expected_path1),
            mock.call("Content chapter 2.", expected_path2)
        ]
        self.mock_engine_instance.save_to_file.assert_has_calls(calls, any_order=False)
        self.assertEqual(self.mock_engine_instance.runAndWait.call_count, 2)

    def test_generate_speech_audio_engine_not_available(self):
        """Test generate_speech_audio when the engine is None."""
        self.vm.engine = None # Simulate engine failure
        with mock.patch('builtins.print') as mock_print:
            self.vm.generate_speech_audio({"t": "t"}, "out", "TXT")
        mock_print.assert_any_call("Text-to-speech engine is not available. Cannot generate audio.")
        self.mock_engine_instance.save_to_file.assert_not_called()
    
    @mock.patch('os.makedirs', side_effect=OSError("Cannot make dir"))
    @mock.patch('os.path.exists', return_value=False) # Ensure makedirs is tried
    @mock.patch('builtins.print')
    def test_generate_speech_audio_makedirs_oserror(self, mock_print, mock_exists, mock_makedirs):
        """Test generate_speech_audio when os.makedirs fails."""
        self.vm.generate_speech_audio({"t": "t"}, "out_dir", "PDF")
        mock_print.assert_any_call("Error creating output directory {}: {}".format("out_dir", OSError("Cannot make dir")))
        self.mock_engine_instance.save_to_file.assert_not_called()

    @mock.patch('os.path.exists', return_value=True)
    def test_generate_speech_audio_runtime_error_on_save(self, mock_path_exists):
        """Test generate_speech_audio handling RuntimeError from engine."""
        self.mock_engine_instance.save_to_file.side_effect = RuntimeError("TTS save error")
        with mock.patch('builtins.print') as mock_print:
            self.vm.generate_speech_audio({"test_item": "text"}, "output", "TXT")
        
        expected_path = os.path.join("output", "test_item.mp3")
        self.mock_engine_instance.save_to_file.assert_called_once_with("text", expected_path)
        mock_print.assert_any_call("RuntimeError generating audio for {}: {}".format("test_item", RuntimeError("TTS save error")))
        self.mock_engine_instance.runAndWait.assert_not_called() # Should not be called if save_to_file fails.
                                                                 # Note: pyttsx3 might call runAndWait internally
                                                                 # before save_to_file fully returns or raises.
                                                                 # If test fails here, it implies runAndWait was called.
                                                                 # The current mock setup for engine would make this pass.

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
