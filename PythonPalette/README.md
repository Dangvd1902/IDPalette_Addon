# Python ID & Custom Properties Palette

This folder contains the Python/PyQt6 application launched by the C++ Archicad add-on in the repository.

The app connects to a running Archicad instance through Graphisoft's official `archicad` Python package. It displays selected built-in properties, optional Classification systems, and selected Custom Properties, and writes edits back through the Archicad JSON command interface.

## Requirements

- Windows.
- Archicad 30.3000 (or adjust the `archicad` package version to match the installed release).
- Python 3.10 or another Python version supported by the installed PyQt6 and Archicad package.
- A project open in Archicad.

The `archicad` package communicates with Archicad through its JSON interface; the C++ launcher only starts this application.

## Run from source

Open PowerShell in this folder:

~~~powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main.py
~~~

If PowerShell blocks virtual-environment activation, use Command Prompt and run:

~~~cmd
.venv\Scripts\activate.bat
python -m pip install -r requirements.txt
python main.py
~~~

Start Archicad and open a project before launching the palette. When prompted that Archicad cannot be found, choose Retry after opening the project, or Close to exit.

## Build the EXE

From this folder, with the virtual environment active:

~~~powershell
pyinstaller --noconfirm --clean --onefile --windowed --name Archicad_ID_Palette main.py
~~~

Expected output:

~~~text
dist\Archicad_ID_Palette.exe
~~~

The EXE is built locally and is not committed to Git. Keep `Archicad_ID_Palette.exe` and its writable `config.json` in a folder where the current Windows user has write permission. If the EXE is placed beside the add-on, the launcher can use the default relative path. Otherwise, set the absolute `ExecutablePath` in `IDPaletteLauncher.ini`.

## Configuration

The application reads `config.json` from the folder containing `main.py` when running from source, or from the folder containing the EXE when packaged. You can start with `config.json.example`:

~~~powershell
Copy-Item config.json.example config.json
~~~

The app also creates the default configuration in memory if the file does not yet exist. Use **⚙ Mục hiển thị** to select Classification systems and Custom Properties, then choose **Lưu cấu hình**. The selection is saved to `config.json`.

Do not put personal or sensitive project data in the example configuration committed to Git.

## Operational notes

- Open a project in Archicad before using the palette.
- The palette reads the first currently selected element for displayed values; edits are applied to all selected elements tracked by the app.
- Changing a value writes it to Archicad immediately. Test on a copy of the project before bulk editing important data.
- The application uses the exact top-level window title `ID & Custom Properties`; this must match the launcher INI's `WindowTitle`.
- The palette checks Archicad's top-level windows periodically. If Archicad is minimized or hidden, the palette hides itself; when Archicad becomes visible again, the palette is restored if it was hidden automatically. The palette remains topmost while Archicad is visible.
