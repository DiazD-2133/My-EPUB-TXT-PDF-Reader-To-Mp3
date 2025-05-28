import os
from abc import ABC, abstractmethod
from io import StringIO
from typing import List, Dict, Union, Tuple, Optional

from bs4 import BeautifulSoup, Tag

from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser

import ebooklib
from ebooklib import epub
from ebooklib.epub import EpubBook, EpubHtml

import files_dirs as file_system_manager # Renamed for clarity
from menumanager import MenuOption
from voicemanager import VoiceManager # Voice class removed


# --- Utility Functions ---
def clean_book_chapters(
    book_chapters: Dict[str, str]
) -> Dict[str, str]:
    """Removes chapters with content length less than a defined threshold."""
    MIN_CONTENT_LENGTH = 30
    chapters_to_remove: List[str] = [
        chapter_name
        for chapter_name, content in book_chapters.items()
        if len(content) < MIN_CONTENT_LENGTH
    ]
    for chapter_name in chapters_to_remove:
        book_chapters.pop(chapter_name)
    return book_chapters


# --- Base Reader Class ---
class AbstractReader(ABC): # Renamed from Read to AbstractReader
    """Abstract base class for reading different file formats."""

    def __init__(self, files_to_process: List[str], target_mp3_dir: str) -> None:
        self.files_to_process: List[str] = files_to_process
        # Stores content for a single book, chapter_name -> chapter_content
        self.current_book_content: Dict[str, str] = {}
        self.existing_mp3_files: List[str] = file_system_manager.get_files_names(
            target_mp3_dir
        )

    def _should_process_file(self, file_name_without_ext: str) -> bool:
        """Checks if a file should be processed (e.g., if it already exists as MP3)."""
        if file_system_manager.already_exists(
            file_name_without_ext, self.existing_mp3_files
        ):
            return False
        return True

    @abstractmethod
    def extract_book_content(
        self, input_folder: str
    ) -> Union[Dict[str, str], List[Tuple[str, Dict[str, str]]]]:
        """
        Extracts content from files.
        For single-file books (like TXT), returns Dict[original_filename, content].
        For multi-chapter books (like EPUB, PDF), returns List[Tuple[book_name, Dict[chapter_name, chapter_content]]].
        """
        pass


# --- Concrete Reader Implementations ---
class TextFileReader(AbstractReader):
    """Reads plain TXT files."""

    def extract_book_content(self, input_folder: str) -> Dict[str, str]:
        """Extracts content from TXT files."""
        processed_books: Dict[str, str] = {}
        for BCM_file_name in self.files_to_process: # BCM: Before Content Manipulation
            original_file_name_no_ext: str = BCM_file_name.split(".")[0]
            mp3_file_name: str = BCM_file_name.replace(".txt", ".mp3")

            if mp3_file_name in self.existing_mp3_files: # More direct check
                print(
                    "File named = {} already exists in the MP3 library!".format(
                        original_file_name_no_ext
                    )
                )
                continue # Skip to the next file

            full_file_path: str = os.path.join(input_folder, BCM_file_name)
            try:
                with open(full_file_path, "r", encoding="utf-8") as file_data:
                    text_content: str = file_data.read()
                    # For TXT, the book name is the file name, and content is the whole text
                    processed_books[original_file_name_no_ext] = text_content
            except FileNotFoundError:
                print("Error: File not found at {}".format(full_file_path))
            except IOError as e:
                print("Error reading file {}: {}".format(full_file_path, e))
        return processed_books


class EpubFileReader(AbstractReader):
    """Reads EPUB files."""

    _HTML_BLACKLIST_TAGS: List[str] = [
        "[document]", "noscript", "header", "html", "meta", "head", "input", "script",
    ]

    def _clean_html_content(self, html_chapter_content: bytes) -> str:
        """Cleans HTML content from an EPUB chapter, extracting text."""
        plain_text_output: str = ""
        try:
            soup: BeautifulSoup = BeautifulSoup(html_chapter_content, "html.parser")
            text_elements: List[Tag] = soup.find_all(text=True)
            for text_element in text_elements:
                if text_element.parent.name not in self._HTML_BLACKLIST_TAGS:
                    plain_text_output += "{} ".format(text_element)
        except Exception as e:
            print("Error cleaning EPUB chapter text: {}".format(e))
        return plain_text_output.strip()

    @staticmethod
    def _extract_epub_chapter_order(epub_opf_file_path: str) -> Dict[str, str]:
        """
        Gets the ordered chapter names (as keys with empty strings as values initially)
        from an EPUB's OPF file.
        """
        ordered_chapters: Dict[str, str] = {}
        try:
            opf_soup: Optional[BeautifulSoup] = file_system_manager.get_opf(epub_opf_file_path)
            if not opf_soup:
                print("Could not parse OPF file for {}".format(epub_opf_file_path))
                return ordered_chapters

            # Find all <itemref idref="..."> elements in the <spine>
            # These define the linear reading order of the EPUB.
            itemref_tags: List[Tag] = opf_soup.find_all("itemref")
            manifest_items: Dict[str, str] = {
                item.get("id"): item.get("href") for item in opf_soup.find_all("item", id=True, href=True)
            }

            for itemref in itemref_tags:
                idref = itemref.get("idref")
                if idref in manifest_items:
                    # The href from the manifest is the actual chapter file path
                    chapter_file_path: str = manifest_items[idref]
                    # Use the filename (without extension) from the href as the chapter key
                    chapter_key: str = file_system_manager.get_item_name(chapter_file_path)
                    ordered_chapters[chapter_key] = "" # Initialize with empty content
                else:
                    print("Warning: idref {} not found in manifest of {}.".format(idref,epub_opf_file_path))

        except Exception as e:
            print("Error getting EPUB chapter order for {}: {}".format(epub_opf_file_path, e))
        return ordered_chapters


    def extract_book_content(
        self, input_folder: str
    ) -> List[Tuple[str, Dict[str, str]]]:
        """Extracts content from EPUB files, maintaining chapter structure."""
        processed_epub_books: List[Tuple[str, Dict[str, str]]] = []
        for BCM_file_name in self.files_to_process:
            book_name_no_ext: str = BCM_file_name.split(".")[0]

            if not self._should_process_file(book_name_no_ext):
                continue

            full_file_path: str = os.path.join(input_folder, BCM_file_name)
            file_extension: str = BCM_file_name.split(".")[-1].lower()

            if file_extension == "epub":
                try:
                    # Initialize current_book_content for this EPUB
                    self.current_book_content = self._extract_epub_chapter_order(full_file_path)
                    if not self.current_book_content:
                        print("Could not determine chapter order for {}, skipping.".format(book_name_no_ext))
                        continue

                    epub_book_obj: EpubBook = epub.read_epub(full_file_path)
                    for item in epub_book_obj.get_items_of_type(ebooklib.ITEM_DOCUMENT):
                        # item.get_name() often includes path like 'OEBPS/chapter1.xhtml'
                        # get_item_name extracts 'chapter1'
                        item_file_name_key: str = file_system_manager.get_item_name(
                            item.get_name()
                        )
                        # Only process items that are part of the defined chapter order
                        if item_file_name_key in self.current_book_content:
                            self.current_book_content[item_file_name_key] = self._clean_html_content(
                                item.get_content()
                            )
                        # else:
                        #    print(f"Debug: Item '{item_file_name_key}' from EPUB not in ordered chapter list. Content type: {item.get_type()}")


                    if any(self.current_book_content.values()): # Check if any content was actually extracted
                        processed_epub_books.append(
                            (book_name_no_ext, self.current_book_content.copy())
                        )
                    else:
                        print("No content extracted for EPUB: {}".format(book_name_no_ext))
                    self.current_book_content.clear() # Clear for the next book

                except FileNotFoundError:
                    print("Error: EPUB file not found at {}".format(full_file_path))
                except epub.EpubException as e: # More specific exception
                    print("Error processing EPUB file {}: {}".format(full_file_path, e))
                except Exception as e:
                    print("An unexpected error occurred with EPUB {}: {}".format(full_file_path, e))
        return processed_epub_books


class PdfFileReader(AbstractReader):
    """Reads PDF files using pdfminer."""

    # Max pages to process before creating a new "chapter" for the audiobook
    _MAX_PAGES_PER_CHUNK: int = 8

    def __init__(self, files_to_process: List[str], target_mp3_dir: str) -> None:
        super().__init__(files_to_process, target_mp3_dir)
        # These are initialized per PDF file (or chunk), not once per instance
        self.pdf_resource_manager: Optional[PDFResourceManager] = None
        self.text_converter_device: Optional[TextConverter] = None
        self.page_interpreter: Optional[PDFPageInterpreter] = None
        self.current_output_stream: Optional[StringIO] = None
        self._initialize_pdf_processing_tools()

    def _initialize_pdf_processing_tools(self) -> None:
        """Initializes or re-initializes PDF processing components for a new PDF or chunk."""
        if self.current_output_stream:
            self.current_output_stream.close() # Ensure previous stream is closed

        self.current_output_stream = StringIO()
        self.pdf_resource_manager = PDFResourceManager()
        self.text_converter_device = TextConverter(
            self.pdf_resource_manager,
            self.current_output_stream,
            laparams=LAParams(),
        )
        self.page_interpreter = PDFPageInterpreter(
            self.pdf_resource_manager, self.text_converter_device
        )

    def _get_cleaned_pdf_text_from_stream(self) -> str:
        """Cleans text extracted from the current PDF output stream."""
        if not self.current_output_stream:
            return ""
        extracted_text: str = self.current_output_stream.getvalue()
        extracted_text = extracted_text.replace("\x0c", "")  # Form feed
        extracted_text = extracted_text.replace("\n", " ").replace("  ", " ")
        # Example: extracted_text = extracted_text.replace("www.useless_text.com", "")
        return extracted_text.strip()


    def extract_book_content(
        self, input_folder: str
    ) -> List[Tuple[str, Dict[str, str]]]:
        """
        Extracts content from PDF files. Each PDF is treated as a book,
        and its content is split into "chapters" based on page count.
        """
        processed_pdf_books: List[Tuple[str, Dict[str, str]]] = []

        for BCM_file_name in self.files_to_process:
            book_name_no_ext: str = BCM_file_name.split(".")[0]

            if not self._should_process_file(book_name_no_ext):
                continue

            full_file_path: str = os.path.join(input_folder, BCM_file_name)
            file_extension: str = BCM_file_name.split(".")[-1].lower()

            if file_extension == "pdf":
                # current_book_content will store chapters for the current PDF
                self.current_book_content.clear()
                pages_in_current_chunk: int = 0
                chapter_index: int = 0

                try:
                    with open(full_file_path, "rb") as pdf_file:
                        pdf_parser: PDFParser = PDFParser(pdf_file)
                        pdf_document: PDFDocument = PDFDocument(pdf_parser)

                        if not self.page_interpreter or not self.text_converter_device:
                            print("PDF processing tools not initialized for {}".format(book_name_no_ext))
                            continue

                        # Initialize tools for the first chunk of this PDF
                        self._initialize_pdf_processing_tools()

                        for pdf_page in PDFPage.create_pages(pdf_document):
                            self.page_interpreter.process_page(pdf_page)
                            pages_in_current_chunk += 1

                            if pages_in_current_chunk >= self._MAX_PAGES_PER_CHUNK:
                                chapter_index += 1
                                chapter_text: str = self._get_cleaned_pdf_text_from_stream()
                                self.current_book_content[
                                    str(chapter_index)
                                ] = chapter_text
                                # Reset for the next chunk
                                self._initialize_pdf_processing_tools()
                                pages_in_current_chunk = 0

                        # Process any remaining pages as the last chapter
                        if pages_in_current_chunk > 0:
                            chapter_index += 1
                            chapter_text: str = self._get_cleaned_pdf_text_from_stream()
                            self.current_book_content[
                                str(chapter_index)
                            ] = chapter_text

                    if self.current_book_content:
                        processed_pdf_books.append(
                            (book_name_no_ext, self.current_book_content.copy())
                        )
                    self.current_book_content.clear()

                except FileNotFoundError:
                    print("Error: PDF file not found at {}".format(full_file_path))
                except Exception as e: # Catch other pdfminer or general errors
                    print("Error processing PDF file {}: {}".format(full_file_path, e))
                finally:
                    # Ensure the last set of tools/stream is closed after processing a PDF
                    if self.current_output_stream:
                        self.current_output_stream.close()
                        self.current_output_stream = None
                    if self.text_converter_device:
                        self.text_converter_device.close()
                        self.text_converter_device = None
        return processed_pdf_books


# --- Factory and Orchestration Functions ---
def get_temporal_books_from_files( # Renamed from get_temporal_books
    selected_option: MenuOption,
) -> Union[Dict[str, str], List[Tuple[str, Dict[str, str]]], None]:
    """
    Factory function to get a reader instance and extract book content
    based on the user's menu selection.
    """
    file_extension_type: str = selected_option.name
    input_directory: str = selected_option.value[0]
    target_mp3_directory: str = selected_option.value[1]

    try:
        files_in_directory: List[str] = file_system_manager.get_files_names(
            input_directory
        )
        if not files_in_directory:
            print("No files found in directory: {}".format(input_directory))
            return None

        reader: Optional[AbstractReader] = None
        if file_extension_type == "TXT":
            reader = TextFileReader(files_in_directory, target_mp3_directory)
        elif file_extension_type == "EPUB":
            reader = EpubFileReader(files_in_directory, target_mp3_directory)
        elif file_extension_type == "PDF":
            reader = PdfFileReader(files_in_directory, target_mp3_directory)
        else:
            print("Unsupported file extension type: {}".format(file_extension_type))
            return None

        return reader.extract_book_content(input_directory)

    except Exception as e:
        print("Error getting temporal books: {}".format(e))
        return None


def process_and_read_books( # Renamed from start_reading
    voice_manager: VoiceManager, # voice_synthesizer (Voice) and voice_manager_settings (VoiceManager) combined
    extracted_books_data: Union[
        Dict[str, str], List[Tuple[str, Dict[str, str]]]
    ],
    selected_option: MenuOption,
) -> None:
    """Processes extracted book data and initiates text-to-speech reading."""
    file_type_for_reading: str = selected_option.name
    # For TXT, this is the single_file_mp3_library. For EPUB/PDF, it's my_mp3_books_library.
    base_mp3_output_dir: str = selected_option.value[1]

    try:
        if not extracted_books_data:
            print("No book data to process for reading.")
            return

        # Case 1: Single file content (e.g., TXT files)
        if isinstance(extracted_books_data, dict):
            # Here, extracted_books_data is Dict[original_filename, content]
            # The base_mp3_output_dir is already the final destination for TXT.
            # The method 'read' in Voice class is now 'generate_speech_audio' in VoiceManager
            voice_manager.generate_speech_audio(
                text_content_map=extracted_books_data, # Pass the whole dict
                output_folder_path=base_mp3_output_dir, # This is 'single_file_mp3_library/'
                file_type=file_type_for_reading,
            )
        # Case 2: Multi-chapter books (e.g., EPUB, PDF)
        elif isinstance(extracted_books_data, list):
            # Here, extracted_books_data is List[Tuple[book_name, Dict[chapter_name, chapter_content]]]
            for book_tuple in extracted_books_data:
                book_main_name: str = book_tuple[0]
                book_chapters_content: Dict[str, str] = book_tuple[1]

                cleaned_chapters: Dict[str, str] = clean_book_chapters(
                    book_chapters_content
                )
                if cleaned_chapters:
                    # For EPUB/PDF, a subdirectory is created for each book's MP3s
                    specific_book_mp3_dir: str = file_system_manager.create_mp3_directory(
                        base_mp3_output_dir, book_main_name # e.g., my_mp3_books_library/MyAwesomeBook/
                    )
                    voice_manager.generate_speech_audio(
                        text_content_map=cleaned_chapters,
                        output_folder_path=specific_book_mp3_dir,
                        file_type=file_type_for_reading, # This will be 'EPUB' or 'PDF'
                    )
        else:
            print(
                "Invalid extracted_books_data type: {}".format(
                    type(extracted_books_data)
                )
            )
    except Exception as e:
        print("Error during process_and_read_books: {}".format(e))

# Ensure old function names are not exposed if other modules import *
__all__ = ['get_temporal_books_from_files', 'process_and_read_books', 'clean_book_chapters',
           'AbstractReader', 'TextFileReader', 'EpubFileReader', 'PdfFileReader']
