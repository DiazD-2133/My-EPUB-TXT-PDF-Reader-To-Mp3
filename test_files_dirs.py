import unittest
from unittest import mock
import os
import zipfile
from bs4 import BeautifulSoup

# Assuming files_dirs.py is in the same directory or accessible in PYTHONPATH
import files_dirs

class TestFilesDirs(unittest.TestCase):

    @mock.patch('os.listdir')
    def test_get_files_names_default_path(self, mock_listdir):
        """Test get_files_names with default path (current directory)."""
        expected_files = ["file1.txt", "dir1"]
        mock_listdir.return_value = expected_files
        
        result = files_dirs.get_files_names()
        
        mock_listdir.assert_called_once_with() # Called with no arguments
        self.assertEqual(result, expected_files)

    @mock.patch('os.listdir')
    def test_get_files_names_specific_path(self, mock_listdir):
        """Test get_files_names with a specific directory path."""
        test_path = "some/directory"
        expected_files = ["fileA.py", "fileB.py"]
        mock_listdir.return_value = expected_files
        
        result = files_dirs.get_files_names(test_path)
        
        mock_listdir.assert_called_once_with(test_path)
        self.assertEqual(result, expected_files)

    @mock.patch('os.listdir', side_effect=FileNotFoundError("Directory not found"))
    def test_get_files_names_directory_not_found(self, mock_listdir):
        """Test get_files_names when the directory does not exist."""
        test_path = "non_existent/directory"
        # We also need to capture the print output to verify the error message
        with mock.patch('builtins.print') as mock_print:
            result = files_dirs.get_files_names(test_path)
        
        mock_listdir.assert_called_once_with(test_path)
        self.assertEqual(result, []) # Should return an empty list
        mock_print.assert_called_with("Error: Directory not found at {}".format(test_path))

    @mock.patch('os.listdir', side_effect=OSError("Permission denied"))
    def test_get_files_names_os_error(self, mock_listdir):
        """Test get_files_names with a generic OSError."""
        test_path = "restricted/directory"
        with mock.patch('builtins.print') as mock_print:
            result = files_dirs.get_files_names(test_path)
            
        mock_listdir.assert_called_once_with(test_path)
        self.assertEqual(result, [])
        mock_print.assert_called_with("Error listing directory {}: {}".format(test_path, OSError("Permission denied")))

    def test_get_item_name_with_path(self):
        """Test get_item_name with a full path."""
        self.assertEqual(files_dirs.get_item_name("some/path/to/file.txt"), "file")
        self.assertEqual(files_dirs.get_item_name("another/file.epub"), "file")

    def test_get_item_name_without_path(self):
        """Test get_item_name with just a filename."""
        self.assertEqual(files_dirs.get_item_name("filename.pdf"), "filename")

    def test_get_item_name_no_extension(self):
        """Test get_item_name with no extension."""
        self.assertEqual(files_dirs.get_item_name("item"), "item")
        self.assertEqual(files_dirs.get_item_name("some/path/item_no_ext"), "item_no_ext")
        
    def test_get_item_name_multiple_dots(self):
        """Test get_item_name with multiple dots in filename."""
        self.assertEqual(files_dirs.get_item_name("archive.tar.gz"), "archive")
        self.assertEqual(files_dirs.get_item_name("my.document.v1.docx"), "my")

    @mock.patch('os.path.exists')
    @mock.patch('os.mkdir')
    def test_create_mp3_directory_not_exists(self, mock_mkdir, mock_exists):
        """Test create_mp3_directory when the directory does not exist."""
        base_dir = "mp3_library/"
        folder_name = "new_book"
        full_path = os.path.join(base_dir, folder_name)
        
        mock_exists.return_value = False
        
        result_path = files_dirs.create_mp3_directory(base_dir, folder_name)
        
        mock_exists.assert_called_once_with(full_path)
        mock_mkdir.assert_called_once_with(full_path)
        self.assertEqual(result_path, os.path.join(full_path, "")) # Ensure trailing slash

    @mock.patch('os.path.exists')
    @mock.patch('os.mkdir')
    def test_create_mp3_directory_exists(self, mock_mkdir, mock_exists):
        """Test create_mp3_directory when the directory already exists."""
        base_dir = "mp3_library/"
        folder_name = "existing_book"
        full_path = os.path.join(base_dir, folder_name)
        
        mock_exists.return_value = True
        
        result_path = files_dirs.create_mp3_directory(base_dir, folder_name)
        
        mock_exists.assert_called_once_with(full_path)
        mock_mkdir.assert_not_called() # mkdir should not be called
        self.assertEqual(result_path, os.path.join(full_path, ""))

    @mock.patch('os.path.exists', return_value=False) # Does not exist
    @mock.patch('os.mkdir', side_effect=OSError("Cannot create directory"))
    @mock.patch('builtins.print')
    def test_create_mp3_directory_os_error_on_create(self, mock_print, mock_mkdir, mock_exists):
        """Test create_mp3_directory when os.mkdir raises an OSError."""
        base_dir = "mp3_library/"
        folder_name = "problem_book"
        full_path = os.path.join(base_dir, folder_name)
        
        result_path = files_dirs.create_mp3_directory(base_dir, folder_name)
        
        mock_exists.assert_called_once_with(full_path)
        mock_mkdir.assert_called_once_with(full_path)
        mock_print.assert_called_with("Error creating directory {}: {}".format(full_path, OSError("Cannot create directory")))
        self.assertEqual(result_path, os.path.join(base_dir, "")) # Should return base path on error

    def test_already_exists_true(self):
        """Test already_exists when the book name is in the library list."""
        book_name = "GreatExpectations"
        mp3_library = ["GreatExpectations", "MobyDick", "WarAndPeace"]
        with mock.patch('builtins.print') as mock_print:
            self.assertTrue(files_dirs.already_exists(book_name, mp3_library))
            mock_print.assert_called_with(
                "Book named = {} already exists in my_mp3_books_library!".format(book_name)
            )

    def test_already_exists_false(self):
        """Test already_exists when the book name is not in the library list."""
        book_name = "NewBook"
        mp3_library = ["GreatExpectations", "MobyDick"]
        with mock.patch('builtins.print') as mock_print:
            self.assertFalse(files_dirs.already_exists(book_name, mp3_library))
            mock_print.assert_not_called()

    @mock.patch('zipfile.ZipFile')
    def test_get_opf_standard_path(self, mock_zipfile):
        """Test get_opf with standard 'OEBPS/content.opf' path."""
        mock_archive_instance = mock.MagicMock()
        mock_zipfile.return_value.__enter__.return_value = mock_archive_instance
        
        opf_content_bytes = b"<?xml version='1.0'?><package><metadata>Test OPF</metadata></package>"
        mock_archive_instance.read.return_value = opf_content_bytes
        
        result_soup = files_dirs.get_opf("dummy.epub")
        
        mock_zipfile.assert_called_once_with("dummy.epub", "r")
        mock_archive_instance.read.assert_called_once_with("OEBPS/content.opf")
        self.assertIsInstance(result_soup, BeautifulSoup)
        self.assertIn("Test OPF", result_soup.text)

    @mock.patch('zipfile.ZipFile')
    def test_get_opf_fallback_path(self, mock_zipfile):
        """Test get_opf with fallback 'content.opf' path."""
        mock_archive_instance = mock.MagicMock()
        mock_zipfile.return_value.__enter__.return_value = mock_archive_instance
        
        # Simulate KeyError for the first path, then success for the second
        opf_content_bytes = b"<package><metadata>Fallback OPF</metadata></package>"
        mock_archive_instance.read.side_effect = [
            KeyError("OEBPS/content.opf not found"),
            opf_content_bytes 
        ]
        
        result_soup = files_dirs.get_opf("dummy.epub")
        
        mock_zipfile.assert_called_once_with("dummy.epub", "r")
        calls = [mock.call("OEBPS/content.opf"), mock.call("content.opf")]
        mock_archive_instance.read.assert_has_calls(calls)
        self.assertIsInstance(result_soup, BeautifulSoup)
        self.assertIn("Fallback OPF", result_soup.text)

    @mock.patch('zipfile.ZipFile')
    @mock.patch('builtins.print')
    def test_get_opf_not_found(self, mock_print, mock_zipfile):
        """Test get_opf when neither OPF path is found."""
        mock_archive_instance = mock.MagicMock()
        mock_zipfile.return_value.__enter__.return_value = mock_archive_instance
        
        mock_archive_instance.read.side_effect = KeyError("File not found")
        
        result_soup = files_dirs.get_opf("dummy.epub")
        
        self.assertIsNone(result_soup)
        mock_print.assert_called_with("Error: OPF file not found in EPUB: {}".format("dummy.epub"))

    @mock.patch('zipfile.ZipFile', side_effect=FileNotFoundError("EPUB not found"))
    @mock.patch('builtins.print')
    def test_get_opf_epub_not_found(self, mock_print, mock_zipfile):
        """Test get_opf when the EPUB file itself is not found."""
        result_soup = files_dirs.get_opf("non_existent.epub")
        self.assertIsNone(result_soup)
        mock_print.assert_called_with("Error: EPUB file not found at {}".format("non_existent.epub"))

    @mock.patch('zipfile.ZipFile', side_effect=zipfile.BadZipFile("Bad EPUB file"))
    @mock.patch('builtins.print')
    def test_get_opf_bad_zipfile(self, mock_print, mock_zipfile):
        """Test get_opf with a corrupted EPUB file."""
        result_soup = files_dirs.get_opf("corrupted.epub")
        self.assertIsNone(result_soup)
        mock_print.assert_called_with("Error: Invalid or corrupted EPUB file: {}".format("corrupted.epub"))

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
