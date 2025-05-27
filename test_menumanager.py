import unittest
from unittest import mock

# Assuming menumanager.py is in the same directory or accessible in PYTHONPATH
from menumanager import MenuManager, MenuOption

class TestMenuManager(unittest.TestCase):

    def setUp(self):
        """Set up a MenuManager instance before each test."""
        self.menu_manager = MenuManager()

    @mock.patch('builtins.input', side_effect=['1'])
    def test_show_menu_select_txt(self, mock_input):
        """Test selecting the TXT option."""
        with mock.patch('builtins.print') as mock_print: # Suppress print output
            result = self.menu_manager.show_menu()
        self.assertEqual(result, MenuOption.TXT)
        mock_input.assert_called_once_with("Make a selection: ")

    @mock.patch('builtins.input', side_effect=['2'])
    def test_show_menu_select_epub(self, mock_input):
        """Test selecting the EPUB option."""
        with mock.patch('builtins.print') as mock_print:
            result = self.menu_manager.show_menu()
        self.assertEqual(result, MenuOption.EPUB)

    @mock.patch('builtins.input', side_effect=['3'])
    def test_show_menu_select_pdf(self, mock_input):
        """Test selecting the PDF option."""
        with mock.patch('builtins.print') as mock_print:
            result = self.menu_manager.show_menu()
        self.assertEqual(result, MenuOption.PDF)

    @mock.patch('builtins.input', side_effect=['4'])
    def test_show_menu_select_language(self, mock_input):
        """Test selecting the LANGUAGE option."""
        with mock.patch('builtins.print') as mock_print:
            result = self.menu_manager.show_menu()
        self.assertEqual(result, MenuOption.LANGUAGE)

    @mock.patch('builtins.input', side_effect=['5'])
    def test_show_menu_select_speedrate(self, mock_input):
        """Test selecting the SPEEDRATE option."""
        with mock.patch('builtins.print') as mock_print:
            result = self.menu_manager.show_menu()
        self.assertEqual(result, MenuOption.SPEEDRATE)

    @mock.patch('builtins.input', side_effect=['6'])
    def test_show_menu_select_close(self, mock_input):
        """Test selecting the CLOSE option."""
        with mock.patch('builtins.print') as mock_print:
            result = self.menu_manager.show_menu()
        self.assertEqual(result, MenuOption.CLOSE)

    @mock.patch('builtins.input', side_effect=['invalid', '1']) # First invalid, then valid
    @mock.patch('builtins.print')
    def test_show_menu_invalid_then_valid_input(self, mock_print, mock_input):
        """Test invalid input followed by a valid one."""
        result = self.menu_manager.show_menu()
        
        self.assertEqual(result, MenuOption.TXT)
        self.assertEqual(mock_input.call_count, 2)
        # Check if the error message was printed for invalid input
        mock_print.assert_any_call("Invalid option. Please try again.")
        # Check if welcome message and menu options were printed (can be more specific)
        mock_print.assert_any_call("\nWelcome to Text-Reader By - Deiker Diaz\n")
        mock_print.assert_any_call("{}. {}".format("1", self.menu_manager.menu_options["1"][0]))


    @mock.patch('builtins.input', side_effect=['0', '7', '', '2']) # Multiple invalid, then valid
    @mock.patch('builtins.print')
    def test_show_menu_multiple_invalid_inputs(self, mock_print, mock_input):
        """Test multiple invalid inputs before a valid one."""
        result = self.menu_manager.show_menu()
        
        self.assertEqual(result, MenuOption.EPUB)
        self.assertEqual(mock_input.call_count, 4)
        # Ensure "Invalid option" was printed for each invalid attempt
        self.assertEqual(mock_print.call_args_list.count(mock.call("Invalid option. Please try again.")), 3)

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
