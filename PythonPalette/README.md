# Python ID & Custom Properties Palette — Archicad 29

This folder contains the Python/PyQt6 palette launched by the C++ Archicad add-on. This branch targets **Archicad 29** and uses Graphisoft's official Python package `archicad==29.3000`.

The application reads and updates selected element properties and classifications through Archicad's local JSON command interface. It is separate from the C++ `.apx` launcher.

## Keep Archicad 29 separate from Archicad 30

Use a dedicated checkout at `C:\Users\Admin\IDPalette_Addon_AC29`. Keep the existing Archicad 30 checkout at `C:\Users\Admin\IDPalette_Addon`. This branch uses its own Conda environment and unique build output names.

## Requirements

- Windows.
- Archicad 29 with a project open.
- Anaconda or Miniforge/Miniconda.
- Visual Studio 2022 / MSVC v143 for building the C++ add-on.

## Create the dedicated Conda environment

Open Anaconda Prompt or Miniforge Prompt in this folder:

~~~cmd
conda env create -f environment.yml
conda activate idpalette-ac29
python --version
python -m pip show archicad PyQt6 pyinstaller
~~~

This environment pins the official Python package to `archicad==29.3000`. Keep the Archicad 30 environment separate; do not reuse the `idpalette` environment used by the Archicad 30 branch.

If `idpalette-ac29` already exists:

~~~cmd
conda env update -f environment.yml --prune
conda activate idpalette-ac29
~~~

## Run from source

Open Archicad 29 and a project first, then:

~~~cmd
python main.py
~~~

The app tries Graphisoft's port discovery and falls back to scanning the local JSON API port range `19723–19743`. It connects to a local Archicad instance, not a remote computer over the network.

## Build the EXE without overwriting the Archicad 30 output

Run from the activated `idpalette-ac29` environment:

~~~cmd
python -m PyInstaller --noconfirm --clean --onefile --windowed --name Archicad_ID_Palette --distpath dist-archicad29 --workpath build-pyinstaller-archicad29 main.py
~~~

Expected output:

~~~text
dist-archicad29\\Archicad_ID_Palette_AC29.exe
~~~

The EXE is built locally and is not committed to Git. Keep its writable `config.json` next to the EXE. When using the launcher, either place the EXE beside `IDPaletteLauncher_AC29.apx` or set the real path in `IDPaletteLauncher.ini`.

## Install and test

1. Build the C++ add-on using the Archicad 29 API DevKit as documented in the repository root README.
2. Build this EXE with the `idpalette-ac29` Conda environment.
3. Configure `IDPaletteLauncher.ini` to point to this EXE.
4. Load the resulting `.apx` in Archicad 29 and test on a copy of the project.
5. Verify element selection, property reads/writes, classifications, palette hide/restore, and multiple-selection behavior before using it on production files.

## Important behavior

- Values are displayed from the first selected element. Edits are applied to the selected element IDs tracked by the app; verify multiple-selection behavior before bulk edits.
- Values are written immediately. Use a test copy of the project.
- The app's window title is `ID & Custom Properties`, which must match `WindowTitle` in the launcher INI.
- The palette hides when Archicad is hidden/minimized and restores when Archicad becomes visible again.
