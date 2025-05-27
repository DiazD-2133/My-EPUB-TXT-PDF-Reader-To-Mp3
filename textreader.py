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


def clean_book_content(book):
    empty_chapters = []
    for chapter_title, chapter_content in book.items():
        if len(chapter_content) < 30:
            empty_chapters.append(chapter_title)
    for chapter_title in empty_chapters:
        book.pop(chapter_title)
    return book


class ReadTxt:
    def __init__(self, file_path, file_name, mp3_dir):
        self.name = file_name
        self.path = file_path
        self.files_dict = {}
        try:
            self.mp3_files = files_dirs_manager.get_files_names(mp3_dir)
        except FileNotFoundError:
            print(f"Warning: MP3 directory '{mp3_dir}' not found for ReadTxt. Assuming no existing MP3s.")
            self.mp3_files = []


    def create_temporal_book(self):
        mp3_file_name_check = self.name.replace(".txt", ".mp3")
        if mp3_file_name_check in self.mp3_files:
            print(f"File named = {mp3_file_name_check.split('.')[0]} already exists")
            # Return empty or indicate skipped for UI consistency if needed
            return {} 
        else:
            try:
                with open(self.path, "r", encoding='utf-8') as data:
                    text = data.read()
                    file_name_base = self.name.split(".")[0]
                    self.files_dict[file_name_base] = text
            except FileNotFoundError:
                print(f"Error: TXT file not found at {self.path}")
                return {}
            except Exception as e:
                print(f"Error reading TXT file {self.path}: {e}")
                return {}
        return self.files_dict


class ReadEPUB:
    def __init__(self, file_path, file_name, mp3_dir):
        self.name = file_name
        self.path = file_path
        self.book = {} # Stores chapter_key: chapter_text for the current EPUB
        try:
            self.mp3_files = files_dirs_manager.get_files_names(mp3_dir)
        except FileNotFoundError:
            print(f"Warning: MP3 directory '{mp3_dir}' not found for ReadEPUB. Assuming no existing MP3s.")
            self.mp3_files = []

        self.blacklist = ['[document]', 'noscript', 'header', 'html', 'meta', 'head', 'input', 'script']

    def clean_text(self, chap_content):
        output = ''
        try:
            soup = BeautifulSoup(chap_content, 'html.parser')
            text_elements = soup.find_all(text=True)
            for t_elem in text_elements:
                if t_elem.parent.name not in self.blacklist:
                    output += '{} '.format(t_elem)
        except Exception as e:
            print(f"Error cleaning EPUB chapter HTML: {e}")
        return output.strip()

    @staticmethod
    def get_epub_index(file_dir_path):
        opf_soup = files_dirs_manager.get_opf(file_dir_path)
        if not opf_soup:
            print(f"Could not get OPF data for {file_dir_path}")
            return {}
            
        itemref_tags = opf_soup.find_all(name="itemref")
        ordered_chapter_keys = []
        
        manifest_items = {item.get("id"): item.get("href") for item in opf_soup.find_all("item", href=True, id=True)}

        for itemref_tag in itemref_tags:
            idref = itemref_tag.get("idref")
            if idref in manifest_items:
                href = manifest_items[idref]
                chapter_key = files_dirs_manager.get_item_name(href)
                ordered_chapter_keys.append(chapter_key)
            else:
                print(f"Warning: idref '{idref}' found in spine but not in manifest for {file_dir_path}.")
        
        book_index = {key: "" for key in ordered_chapter_keys}
        return book_index

    def create_temporal_book(self): # 'folder' param removed, uses self.path
        books_list = []
        book_name_base = self.name.split(".")[0]

        if files_dirs_manager.already_exists(book_name_base, self.mp3_files):
            # already_exists (presumably) prints, so just return
            return books_list 

        try:
            epub_book_obj = epub.read_epub(self.path)
            self.book = self.get_epub_index(self.path) # Get ordered chapter structure

            if not self.book:
                 print(f"Could not determine chapter order for {self.name}, skipping.")
                 return books_list

            for item in epub_book_obj.get_items_of_type(ebooklib.ITEM_DOCUMENT):
                item_key = files_dirs_manager.get_item_name(item.get_name())
                if item_key in self.book: 
                    self.book[item_key] = self.clean_text(item.get_content())
                # else: item not in spine, ignore.
            
            # Filter out chapters that ended up empty after cleaning
            # The self.book from get_epub_index has all spine items as keys.
            # We only want to include chapters that actually yielded text.
            contentful_chapters = {k: v for k, v in self.book.items() if v}

            if contentful_chapters:
                temporal_book_tuple = (book_name_base, contentful_chapters)
                books_list.append(temporal_book_tuple)
            else:
                print(f"No text content extracted from EPUB {self.name} after cleaning.")
        
        except FileNotFoundError:
            print(f"Error: EPUB file not found at {self.path}")
            return [] # Return empty list on error
        except epub.EpubException as e:
            print(f"Error processing EPUB file {self.path}: {e}")
            return []
        except Exception as e:
            print(f"An unexpected error occurred with EPUB {self.path}: {e}")
            return []
            
        return books_list


class ReadPDF:
    def __init__(self, file_path, file_name, mp3_dir):
        self.name = file_name
        self.path = file_path
        self.book_chapters = {}
        try:
            self.mp3_files = files_dirs_manager.get_files_names(mp3_dir)
        except FileNotFoundError:
            print(f"Warning: MP3 directory '{mp3_dir}' not found for ReadPDF. Assuming no existing MP3s.")
            self.mp3_files = []
        
        # Components are initialized here but managed per create_temporal_book call for safety
        self.pdf_resource_manager = None
        self.output_string_io = None
        self.text_converter = None
        self.page_interpreter = None

    def _initialize_pdf_components(self):
        """Initializes pdfminer components for a new processing session or chunk."""
        self._close_pdf_components() # Close any existing ones first
        self.pdf_resource_manager = PDFResourceManager()
        self.output_string_io = StringIO()
        self.text_converter = TextConverter(self.pdf_resource_manager, self.output_string_io, laparams=LAParams())
        self.page_interpreter = PDFPageInterpreter(self.pdf_resource_manager, self.text_converter)

    def _close_pdf_components(self):
        """Safely closes pdfminer components."""
        if hasattr(self, 'output_string_io') and self.output_string_io:
            try:
                self.output_string_io.close()
            except Exception as e:
                print(f"Error closing StringIO: {e}")
            self.output_string_io = None
        if hasattr(self, 'text_converter') and self.text_converter:
            try:
                self.text_converter.close()
            except Exception as e:
                print(f"Error closing TextConverter: {e}")
            self.text_converter = None
        # PDFResourceManager and PDFPageInterpreter do not have explicit close methods in typical usage.

    def _clean_page_text(self):
        if not self.output_string_io: return ""
        extracted_text = self.output_string_io.getvalue()
        extracted_text = extracted_text.replace("+", "") # Form feed (often \x0c)
        extracted_text = extracted_text.replace("\n", " ")
        extracted_text = " ".join(extracted_text.split()) 
        return extracted_text.strip()

    def _reset_string_io_for_next_chunk(self):
        # Re-initialize all components for a new chunk to ensure clean state
        self._initialize_pdf_components()

    def create_temporal_book(self): # 'folder' param removed
        processed_books_list = []
        pages_processed_in_chunk = 0
        chapter_idx = 0
        book_name_base = self.name.split(".")[0]
        self.book_chapters = {} # Reset for current book

        if files_dirs_manager.already_exists(book_name_base, self.mp3_files):
            return processed_books_list

        try:
            self._initialize_pdf_components() # Initialize for the first time for this file

            with open(self.path, 'rb') as in_file:
                pdf_parser = PDFParser(in_file)
                pdf_doc = PDFDocument(pdf_parser)

                for pdf_page in PDFPage.create_pages(pdf_doc):
                    if not self.page_interpreter: # Should have been initialized
                        print("PDFPageInterpreter not available.")
                        break 
                    self.page_interpreter.process_page(pdf_page)
                    pages_processed_in_chunk += 1
                    
                    if pages_processed_in_chunk >= 8:
                        page_text = self._clean_page_text()
                        if page_text: 
                            chapter_idx += 1
                            self.book_chapters[str(chapter_idx)] = page_text
                        self._reset_string_io_for_next_chunk() # Re-initializes components
                        pages_processed_in_chunk = 0 

                if pages_processed_in_chunk > 0: # Process remaining pages
                    page_text = self._clean_page_text()
                    if page_text: 
                       chapter_idx += 1
                       self.book_chapters[str(chapter_idx)] = page_text
            
            if self.book_chapters: 
                temporal_book_tuple = (book_name_base, self.book_chapters)
                processed_books_list.append(temporal_book_tuple)
            else:
                print(f"No text content extracted from PDF {self.name}.")

        except FileNotFoundError:
            print(f"Error: PDF file not found at {self.path}")
        except Exception as e:
            print(f"Error processing PDF file {self.path}: {e}")
        finally:
            self._close_pdf_components() # Ensure cleanup
                
        return processed_books_list


def get_temporal_books(file_path, file_name, mp3_directory):
    file_ext = file_name.split(".")[-1].lower() 
    reader_instance = None
    if file_ext == "txt":
        reader_instance = ReadTxt(file_path, file_name, mp3_directory)
    elif file_ext == "epub":
        reader_instance = ReadEPUB(file_path, file_name, mp3_directory)
    elif file_ext == "pdf":
        reader_instance = ReadPDF(file_path, file_name, mp3_directory)
    else:
        print(f"Unsupported file extension: {file_ext}")
        return None 

    if reader_instance:
        return reader_instance.create_temporal_book()
    return None


def start_reading(voice_instance, voice_manager_instance, temporal_book_data, mp3_dir_output, book_file_name_with_ext, ui_info_items):
    if not temporal_book_data or (isinstance(temporal_book_data, list) and not temporal_book_data) or \
       (isinstance(temporal_book_data, dict) and not any(temporal_book_data.values())):
        print(f"No content to read for {book_file_name_with_ext}.")
        if ui_info_items and ui_info_items.get("state_info"):
            ui_info_items["state_info"].value = f"No content found in {book_file_name_with_ext} or file is empty."
            ui_info_items["state_info"].update()
        if ui_info_items and ui_info_items.get("progress_ring"):
            ui_info_items["progress_ring"].visible = False
            ui_info_items["progress_ring"].update()
        if ui_info_items and ui_info_items.get("items_to_read"):
             ui_info_items["items_to_read"].value = ""
             ui_info_items["items_to_read"].update()
        return

    file_extension = book_file_name_with_ext.split(".")[-1].lower()

    if file_extension == "txt": 
        voice_instance.read(voice_manager_instance, file_extension, mp3_dir_output, temporal_book_data, ui_info_items)
    
    elif file_extension in ["epub", "pdf"]: 
        # temporal_book_data is a list: [(book_name_base, {chapter_key: chapter_text})]
        for book_item_tuple in temporal_book_data: # Should be only one item for single file picker
            book_title_base, book_chapters_dict = book_item_tuple
            cleaned_chapters_dict = clean_book_content(book_chapters_dict) # Clean chapters from this book
            
            if cleaned_chapters_dict:
                # For EPUB/PDF, create a subdirectory for this book's chapters within mp3_dir_output
                specific_book_output_dir = files_dirs_manager.create_mp3_directory(mp3_dir_output, book_title_base)
                if not os.path.exists(specific_book_output_dir): 
                    print(f"Error: Could not create/access directory {specific_book_output_dir} for {book_title_base}")
                    if ui_info_items.get("state_info"):
                        ui_info_items["state_info"].value = f"Error with output folder for {book_title_base}."
                        ui_info_items["state_info"].update()
                    continue 

                voice_instance.read(voice_manager_instance, file_extension, specific_book_output_dir, cleaned_chapters_dict, ui_info_items)
            else:
                message = f"Book '{book_title_base}' in {book_file_name_with_ext} has no content after cleaning."
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
    
    # General UI cleanup after processing (or if no content was found initially)
    if ui_info_items and ui_info_items.get("progress_ring"):
        ui_info_items["progress_ring"].visible = False
        ui_info_items["progress_ring"].update()
    if ui_info_items and ui_info_items.get("items_to_read") and not ui_info_items["items_to_read"].value: # If not set by loop
         ui_info_items["items_to_read"].value = "" # Or "Processing complete."
         ui_info_items["items_to_read"].update()
