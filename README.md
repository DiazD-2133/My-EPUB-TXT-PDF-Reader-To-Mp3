# Text-to-Speech Converter App

This application converts text from various file formats (TXT, EPUB, PDF) into MP3 audio files using system-installed text-to-speech (TTS) voices. It features a user-friendly interface built with Flet, allowing for easy file selection, output directory configuration, and voice customization.

## Features

*   **Multiple File Format Support**: Converts `.txt`, `.epub`, and `.pdf` files.
*   **Customizable Voice Output**:
    *   Select from available system TTS voices.
    *   Adjust the speech rate (speed).
    *   Settings are saved for future sessions.
*   **User-Friendly Interface**:
    *   Built with [Flet](https://flet.dev/), providing a clean and modern GUI.
    *   Easy selection of input files and output MP3 directory.
    *   Real-time feedback during the conversion process.
    *   Output folder automatically opens upon successful conversion.
    *   Supports UI language selection (English/Español).
*   **Organized Output**:
    *   TXT files are converted into single MP3 files.
    *   EPUB and PDF files are converted into multiple MP3 files, organized by chapters/parts within a dedicated subfolder for each book in your MP3 library.
*   **Configuration Persistence**: Remembers your MP3 directory, preferred voice, speed rate, and UI language.

## Setup and Usage

Follow these steps to set up and run the application:

1.  **Prerequisites**:
    *   Python 3.8+
    *   A text-to-speech engine installed on your system (e.g., Windows SAPI5, macOS Speech Synthesis, Linux eSpeak/Festival).

2.  **Clone the Repository (Optional)**:
    ```bash
    git clone <your-repository-url>
    cd <repository-folder>
    ```

3.  **Create and Activate a Virtual Environment**:
    Open a terminal or command prompt in the project's root directory.
    ```bash
    # Create virtual environment
    python -m venv venv
    ```
    Activate the virtual environment:
    *   Windows (Command Prompt): `venv\Scripts\activate`
    *   Windows (PowerShell): `venv\Scripts\Activate.ps1`
        *   (If you get an execution policy error on PowerShell, you might need to run: `Set-ExecutionPolicy Unrestricted -Scope Process` first, then try activating again. Be sure to understand the implications of changing execution policies.)
    *   macOS/Linux: `source venv/bin/activate`

4.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

5.  **Prepare Your Files (Optional but Recommended)**:
    *   Place your `.txt` files into the `my_txt_library` folder (it will be created on first run if it doesn't exist).
    *   Place your `.epub` and `.pdf` files into the `my_books_library` folder (will also be created if missing).
    *   The application will generate MP3s in `mp3_books_library` (for EPUB/PDF) and `single_file_mp3_library` (for TXT, though current Flet version uses the main configured MP3 directory for TXT directly). You can change the main output directory via the UI.

6.  **Run the Application**:
    ```bash
    python flet-main.py
    ```
    *   On the first run, necessary directories like `mp3_books_library` and `configs.json` will be created if they don't exist.

## How to Use the Interface

1.  **Text to Audio Tab**:
    *   **Change Audio Directory**: Set the main folder where your MP3s will be saved.
    *   **Select File**: Choose a `.txt`, `.epub`, or `.pdf` file to convert.
    *   **Generate Audio**: Start the conversion process.
    *   The list below will show the generated MP3 files for the current book.
    *   The output folder containing the generated MP3s will open automatically upon completion.

2.  **Voice Settings Tab**:
    *   **Select Voice**: Choose your preferred TTS voice from the system's available options.
    *   **Speed Rate**: Adjust the speaking speed.
    *   **Save Voice Settings**: Persist your voice and speed preferences.

3.  **UI Settings Tab**:
    *   **Select UI Language**: Choose between English and Español for the application interface.
    *   **Save UI Settings**: Save your language preference. A restart might be needed for all text elements to update if you change the language while the app is running.

## Troubleshooting

*   **No Voices Available**: Ensure your operating system has TTS voices installed and accessible to `pyttsx3`.
*   **Errors during PDF/EPUB processing**: Some complex or DRM-protected files might not process correctly.
*   **"Permission Denied" on PowerShell when activating venv**: Run `Set-ExecutionPolicy Unrestricted -Scope Process` in your PowerShell session and try activating again.
