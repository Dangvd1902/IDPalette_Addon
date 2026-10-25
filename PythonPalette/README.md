# Python ID & Custom Properties Palette

This folder contains the Python/PyQt6 app launched by the C++ Archicad add-on.

The app connects to a running Archicad instance through Graphisoft's official `archicad` Python package. It displays selected built-in properties, optional Classification systems, and selected Custom Properties, and writes edits back through Archicad's JSON command interface.

## Requirements

- Windows.
- Archicad 30.3000 (or update the `archicad` package version to match your installed release).
- Anaconda or Miniforge/Miniconda with Conda available in the terminal.
- A project open in Archicad.

The `archicad` package is the official Python binding for Archicad's JSON command interface. The C++ launcher only starts the Python application.

The application currently connects explicitly to the local Archicad JSON API at port `19723`, verified on the development machine. If your Archicad instance is configured to use a different port, update `ARCHICAD_API_PORT` in `main.py` accordingly.

## Create the Conda environment

Open **Anaconda Prompt** or **Miniforge Prompt** in this folder, then run:

~~~cmd
conda env create -f environment.yml
conda activate idpalette
~~~

If the environment already exists and you want to refresh its packages:

~~~cmd
conda env update -f environment.yml --prune
conda activate idpalette
~~~

Verify that Python and the packages are available:

~~~cmd
python --version
python -m pip show archicad PyQt6 pyinstaller
~~~

## Run from source

Start Archicad and open a project first. In the same activated Conda environment, run:

~~~cmd
python main.py
~~~

When prompted that Archicad cannot be found, choose **Retry** after opening the project, or **Close** to exit.

## Build the Windows EXE

Build on Windows from the same activated Conda environment:

~~~cmd
python -m PyInstaller --noconfirm --clean --onefile --windowed --name Archicad_ID_Palette main.py
~~~

Expected output:

~~~text
dist\Archicad_ID_Palette.exe
~~~

The EXE is built locally and is not committed to Git. The Python package version must match the installed Archicad release. PyInstaller packages the interpreter and Python dependencies; it does not include Archicad itself.

Keep `Archicad_ID_Palette.exe` and its writable `config.json` in a folder where the current Windows user has write permission. If the EXE is placed next to the `.apx`, the launcher can use the default relative path. Otherwise, set the absolute `ExecutablePath` in `IDPaletteLauncher.ini`.

## Configuration

The app reads `config.json` from the folder containing `main.py` when running from source, or from the folder containing the EXE when packaged. You can start with the example file:

~~~cmd
copy config.json.example config.json
~~~

The app also uses a default empty configuration if no config file exists. Use **⚙ Mục hiển thị** to select Classification systems and Custom Properties, then choose **Lưu cấu hình**. The selection is saved to `config.json`.

Do not commit personal or sensitive project data.

## Operational notes

- Open a project in Archicad before using the palette.
- The palette reads the first currently selected element for display; edits are applied to all selected elements tracked by the app.
- Changing a value writes it to Archicad immediately. Test on a copy of the project before bulk-editing important data.
- The app's top-level title is exactly `ID & Custom Properties`; this must match the launcher's `WindowTitle`.
- The palette checks Archicad's top-level windows periodically. If Archicad is minimized or hidden, the palette hides itself; when Archicad becomes visible again, it restores if it was automatically hidden.
