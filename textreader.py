from io import StringIO
from bs4 import BeautifulSoup

from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser

import ebooklib
from ebooklib import epub

import files_dirs as files_dirs_manager
import os

from voicemanager import VoiceManager


def clean_book_content(book_chapters_dict):
    MIN_CONTENT_LENGTH = 50
    empty_chapters_keys = [
        key for key, content in book_chapters_dict.items() if len(content) < MIN_CONTENT_LENGTH
    ]
    for key in empty_chapters_keys:
        print(f"Info: Removing short/empty chapter '{key}' from book.")
        book_chapters_dict.pop(key)
    return book_chapters_dict


class ReadTxt:
    def __init__(self, file_path, file_name, mp3_dir):
        self.name = file_name
        self.path = file_path
        self.files_dict = {}
        try:
            self.mp3_files_in_library = files_dirs_manager.get_files_names(mp3_dir)
        except FileNotFoundError:
            print(f"Warning: MP3 directory '{mp3_dir}' not found for ReadTxt. Assuming no existing MP3s.")
            self.mp3_files_in_library = []

    def create_temporal_book(self):
        book_name_base = self.name.split(".")[0]
        mp3_file_name_check = f"{book_name_base}.mp3"

        if mp3_file_name_check in self.mp3_files_in_library:
            print(f"File named = {book_name_base} (as {mp3_file_name_check}) already exists in MP3 library.")
            return {}
        else:
            try:
                with open(self.path, "r", encoding='utf-8') as data:
                    text = data.read()
                    if not text.strip():
                        print(f"Warning: TXT file {self.name} is empty or contains only whitespace.")
                        return {}
                    self.files_dict[book_name_base] = text
            except FileNotFoundError:
                print(f"Error: TXT file not found at {self.path}")
                return {}
            except Exception as e:
                print(f"Error reading TXT file {self.path}: {e}")
                return {}
        return self.files_dict


class ReadEPUB:
    def __init__(self, file_path, file_name, mp3_dir_base):
        self.name = file_name
        self.path = file_path
        self.mp3_dir_base = mp3_dir_base
        try:
            self.items_in_mp3_library_base = files_dirs_manager.get_files_names(self.mp3_dir_base)
        except FileNotFoundError:
            print(
                f"Warning: Base MP3 directory '{self.mp3_dir_base}' not found for ReadEPUB. Assuming book not processed.")
            self.items_in_mp3_library_base = []

        self.html_text_blacklist = ['[document]', 'noscript', 'header', 'html', 'meta', 'head', 'input', 'script',
                                    'style', 'title', 'link']

    def _clean_html_chapter_text(self, chapter_html_content):
        output_text = ''
        try:
            soup = BeautifulSoup(chapter_html_content, 'html.parser')
            text_elements = soup.find_all(text=True)
            for t_elem in text_elements:
                if t_elem.parent.name not in self.html_text_blacklist:
                    output_text += '{} '.format(t_elem)
        except Exception as e:
            print(f"Error cleaning EPUB chapter HTML: {e}")
        output_text = " ".join(output_text.split())
        return output_text.strip()

    @staticmethod
    def _get_epub_spine_and_manifest(epub_file_path):
        opf_soup = files_dirs_manager.get_opf(epub_file_path)
        if not opf_soup:
            print(f"Could not get OPF data for {epub_file_path}")
            return {}, {}

        itemref_tags = opf_soup.find_all(name="itemref")
        spine_idrefs_ordered = [itemref.get("idref") for itemref in itemref_tags if itemref.get("idref")]

        manifest_id_to_href = {
            item.get("id"): item.get("href")
            for item in opf_soup.find_all("item", href=True, id=True)
        }
        return spine_idrefs_ordered, manifest_id_to_href

    def create_temporal_book(self):
        temporal_book_list = []
        book_name_base = self.name.split(".")[0]

        if files_dirs_manager.already_exists(book_name_base, self.items_in_mp3_library_base):
            return temporal_book_list

        current_book_chapters_dict = {}
        try:
            epub_obj = epub.read_epub(self.path)
            spine_idrefs_ordered, manifest_id_to_href = self._get_epub_spine_and_manifest(self.path)

            if not spine_idrefs_ordered:
                print(f"Could not determine chapter order (spine) for {self.name}, skipping.")
                return temporal_book_list

            for idref in spine_idrefs_ordered:
                if idref in manifest_id_to_href:
                    chapter_href = manifest_id_to_href[idref]
                    epub_item = epub_obj.get_item_with_href(chapter_href)

                    if epub_item and epub_item.get_type() == ebooklib.ITEM_DOCUMENT:
                        raw_html_content = epub_item.get_content()
                        cleaned_text = self._clean_html_chapter_text(raw_html_content)
                        if cleaned_text:
                            chapter_key = files_dirs_manager.get_item_name(chapter_href)
                            current_book_chapters_dict[chapter_key] = cleaned_text
                else:
                    print(f"Warning: Spine item idref '{idref}' not found in manifest for {self.name}.")

            if current_book_chapters_dict:
                temporal_book_list.append((book_name_base, current_book_chapters_dict))
            else:
                print(f"No text content extracted from EPUB {self.name} after processing spine and cleaning.")

        except FileNotFoundError:
            print(f"Error: EPUB file not found at {self.path}")
        except epub.EpubException as e:
            print(f"Error processing EPUB file {self.path}: {e}")
        except Exception as e:
            print(f"An unexpected error occurred with EPUB {self.name}: {e}")

        return temporal_book_list


class ReadPDF:
    def __init__(self, file_path, file_name, mp3_dir_base):
        self.name = file_name
        self.path = file_path
        self.mp3_dir_base = mp3_dir_base
        try:
            self.items_in_mp3_library_base = files_dirs_manager.get_files_names(self.mp3_dir_base)
        except FileNotFoundError:
            print(f"Warning: Base MP3 directory '{self.mp3_dir_base}' not found for ReadPDF.")
            self.items_in_mp3_library_base = []

        self.pdf_resource_manager = None
        self.output_string_io = None
        self.text_converter_device = None
        self.page_interpreter = None

    def _initialize_pdf_processing_tools(self):
        self._close_pdf_processing_tools()
        self.pdf_resource_manager = PDFResourceManager()
        self.output_string_io = StringIO()
        self.text_converter_device = TextConverter(self.pdf_resource_manager, self.output_string_io,
                                                   laparams=LAParams())
        self.page_interpreter = PDFPageInterpreter(self.pdf_resource_manager, self.text_converter_device)

    def _close_pdf_processing_tools(self):
        if hasattr(self, 'output_string_io') and self.output_string_io:
            try:
                self.output_string_io.close()
            except Exception:
                pass
            self.output_string_io = None
        if hasattr(self, 'text_converter_device') and self.text_converter_device:
            try:
                self.text_converter_device.close()
            except Exception:
                pass
            self.text_converter_device = None

    def _get_cleaned_pdf_text_from_stream(self) -> str:
        if not self.output_string_io: return ""
        extracted_text = self.output_string_io.getvalue()
        extracted_text = extracted_text.replace("", "")
        extracted_text = extracted_text.replace("\r\n", "\n").replace("\r", "\n")
        extracted_text = " ".join(extracted_text.split())
        return extracted_text.strip()

    def create_temporal_book(self):
        temporal_book_list = []
        book_name_base = self.name.split(".")[0]
        current_book_chapters_dict = {}

        if files_dirs_manager.already_exists(book_name_base, self.items_in_mp3_library_base):
            return temporal_book_list

        PAGES_PER_CHUNK = 8
        pages_processed_in_current_chunk = 0
        chapter_index = 0

        try:
            self._initialize_pdf_processing_tools()

            with open(self.path, 'rb') as in_file:
                pdf_parser = PDFParser(in_file)
                pdf_doc = PDFDocument(pdf_parser)

                if not pdf_doc.is_extractable:
                    print(f"Warning: PDF file {self.name} does not allow text extraction.")
                    self._close_pdf_processing_tools()
                    return temporal_book_list

                for pdf_page_num, pdf_page in enumerate(PDFPage.create_pages(pdf_doc)):
                    if not self.page_interpreter:
                        print("Error: PDFPageInterpreter not available. Cannot process PDF page.")
                        break
                    try:
                        self.page_interpreter.process_page(pdf_page)
                        pages_processed_in_current_chunk += 1
                    except Exception as page_proc_error:
                        print(f"Error processing page {pdf_page_num + 1} of {self.name}: {page_proc_error}")
                        self._initialize_pdf_processing_tools()
                        pages_processed_in_current_chunk = 0
                        continue

                    if pages_processed_in_current_chunk >= PAGES_PER_CHUNK:
                        page_chunk_text = self._get_cleaned_pdf_text_from_stream()
                        if page_chunk_text:
                            chapter_index += 1
                            current_book_chapters_dict[f"part_{chapter_index:03d}"] = page_chunk_text

                        self._initialize_pdf_processing_tools()
                        pages_processed_in_current_chunk = 0

                if pages_processed_in_current_chunk > 0:
                    page_chunk_text = self._get_cleaned_pdf_text_from_stream()
                    if page_chunk_text:
                        chapter_index += 1
                        current_book_chapters_dict[f"part_{chapter_index:03d}"] = page_chunk_text

            if current_book_chapters_dict:
                temporal_book_list.append((book_name_base, current_book_chapters_dict))
            else:
                print(f"No text content extracted from PDF {self.name}.")

        except FileNotFoundError:
            print(f"Error: PDF file not found at {self.path}")
        except Exception as e:
            print(f"Error processing PDF file {self.path}: {e}")
        finally:
            self._close_pdf_processing_tools()

        return temporal_book_list


def get_temporal_books(file_path: str, file_name_with_ext: str, mp3_library_dir: str):
    file_ext_lower = file_name_with_ext.split(".")[-1].lower()
    reader_instance = None

    if file_ext_lower == "txt":
        reader_instance = ReadTxt(file_path, file_name_with_ext, mp3_library_dir)
    elif file_ext_lower == "epub":
        reader_instance = ReadEPUB(file_path, file_name_with_ext, mp3_library_dir)
    elif file_ext_lower == "pdf":
        reader_instance = ReadPDF(file_path, file_name_with_ext, mp3_library_dir)
    else:
        print(f"Unsupported file extension: {file_ext_lower} for file {file_name_with_ext}")
        return None

    if reader_instance:
        try:
            return reader_instance.create_temporal_book()
        except Exception as e_create:
            print(
                f"Error during create_temporal_book for {file_name_with_ext} with {file_ext_lower} reader: {e_create}")
            return None
    return None


def start_reading(
        voice_manager: VoiceManager,
        extracted_book_data,
        mp3_output_dir_base: str,
        book_file_name_with_ext: str,
        ui_info_items: dict
) -> str | None:  # Returns the path to the generated audio folder/file or None
    """
    Processes the extracted book data and generates audio.
    Returns the path to the main output folder for the generated audio files,
    or None if processing failed or no audio was generated.
    """
    final_output_path_for_this_book = None  # To store the path for "Open Folder"

    if not voice_manager or not voice_manager.engine:
        print("VoiceManager not initialized or engine not available. Cannot start reading.")
        if ui_info_items and ui_info_items.get("state_info"):
            ui_info_items["state_info"].value = "Voice engine error. Check logs."
            ui_info_items["state_info"].update()
        if ui_info_items and ui_info_items.get("progress_ring"):
            ui_info_items["progress_ring"].visible = False
            ui_info_items["progress_ring"].update()
        return None

    if not extracted_book_data:
        print(f"No content to read for {book_file_name_with_ext}.")
        if ui_info_items and ui_info_items.get("state_info"):
            ui_info_items["state_info"].value = f"No content in {book_file_name_with_ext} or file empty/unsupported."
            ui_info_items["state_info"].update()
        if ui_info_items and ui_info_items.get("progress_ring"):
            ui_info_items["progress_ring"].visible = False
            ui_info_items["progress_ring"].update()
        if ui_info_items and ui_info_items.get("items_to_read"):
            ui_info_items["items_to_read"].value = ""
            ui_info_items["items_to_read"].update()
        return None

    file_extension_lower = book_file_name_with_ext.split(".")[-1].lower()

    if file_extension_lower == "txt":
        voice_manager.generate_audio(
            file_extension_lower,
            mp3_output_dir_base,
            extracted_book_data,
            ui_info_items
        )
        # For TXT, the output is directly in mp3_output_dir_base.
        # We can refine this if we want to point to the specific MP3 file later.
        # For now, just the base directory.
        if any(extracted_book_data.values()):  # If any content was processed
            final_output_path_for_this_book = mp3_output_dir_base

    elif file_extension_lower in ["epub", "pdf"]:
        for book_name_base, book_chapters_dict_raw in extracted_book_data:
            cleaned_chapters_dict = clean_book_content(book_chapters_dict_raw.copy())

            if cleaned_chapters_dict:
                specific_book_mp3_subdir = files_dirs_manager.create_mp3_directory(mp3_output_dir_base, book_name_base)

                expected_subdir_path = os.path.join(mp3_output_dir_base, book_name_base, "")
                if not specific_book_mp3_subdir or not specific_book_mp3_subdir.replace("\\", "/").startswith(
                        expected_subdir_path.replace("\\", "/")):
                    error_msg = f"Could not create/access MP3 directory for {book_name_base}"
                    print(f"Error: {error_msg} at {specific_book_mp3_subdir}")
                    if ui_info_items.get("state_info"):
                        ui_info_items["state_info"].value = error_msg
                        ui_info_items["state_info"].update()
                    continue

                voice_manager.generate_audio(
                    file_extension_lower,
                    specific_book_mp3_subdir,
                    cleaned_chapters_dict,
                    ui_info_items
                )
                final_output_path_for_this_book = specific_book_mp3_subdir  # Store the path to this book's MP3s
            else:
                message = f"Book '{book_name_base}' (from {book_file_name_with_ext}) has no content after cleaning."
                print(message)
                if ui_info_items.get("state_info"):
                    ui_info_items["state_info"].value = message
                    ui_info_items["state_info"].update()
    else:
        message = f"Unsupported file format or empty content for: {book_file_name_with_ext}"
        print(message)
        if ui_info_items.get("state_info"):
            ui_info_items["state_info"].value = message
            ui_info_items["state_info"].update()

    if ui_info_items and ui_info_items.get("progress_ring") and ui_info_items["progress_ring"].visible:
        ui_info_items["progress_ring"].visible = False
        ui_info_items["progress_ring"].update()
    if ui_info_items and ui_info_items.get("items_to_read") and not ui_info_items["items_to_read"].value.endswith(
            "complete."):
        if not ui_info_items["items_to_read"].value:
            ui_info_items["items_to_read"].value = ""
            ui_info_items["items_to_read"].update()

    return final_output_path_for_this_book

