# IDPalette Add-on

This repository contains two related components:

1. **C++ Archicad launcher add-on** — registers a menu command in Archicad and opens the palette application.
2. **Python ID & Custom Properties palette** — the source for `Archicad_ID_Palette.exe`, a PyQt6 app that uses Graphisoft's `archicad` Python package to read and write selected element properties and classifications.

The launcher and Python application are separate deliverables. Building the `.apx` does not build the Python EXE automatically.

## Repository layout

- `CMakeLists.txt`: CMake configuration for the C++ Archicad add-on.
- `Src/AddOnMain.cpp`: add-on lifecycle, menu handler and EXE launcher.
- `Src/APIEnvir.h`: project-local Windows/API environment header.
- `Src/AddOn.grc`: add-on menu and metadata resources.
- `Src/ResourceIds.hpp`: resource IDs used by the resource compiler.
- `IDPaletteLauncher.ini.example`: sample launcher configuration.
- `PythonPalette/main.py`: Python/PyQt6 application source.
- `PythonPalette/requirements.txt`: Python runtime and packaging dependencies.
- `PythonPalette/config.json.example`: starter configuration.
- `PythonPalette/README.md`: Python setup, run and EXE packaging instructions.

## Build the C++ launcher (.apx)

### Requirements

- Windows and Visual Studio C++ build tools (MSVC).
- CMake 3.16 or newer.
- An Archicad API DevKit compatible with the Archicad version you intend to use.

The default `AC_API_DEVKIT_DIR` is `C:/API.Development.Kit.WIN.30.3000`; change this to the actual DevKit location on your machine.

From a Developer PowerShell for Visual Studio or a terminal where CMake and MSBuild are available:

~~~powershell
cmake -S . -B build -G "Visual Studio 17 2022" -A x64 -T v143 -DAC_API_DEVKIT_DIR="C:/API.Development.Kit.WIN.30.3000"
cmake --build build --config Release
~~~

Expected output:

~~~text
build/out/IDPaletteLauncher.apx
~~~

The `.apx` has not been build-tested by CI. Build and validate it against the target Archicad installation before distribution. Add-on loading may also depend on valid Graphisoft-issued MDID values and the applicable Archicad licensing/development mode.

## Build the Python palette EXE with Conda

Follow [PythonPalette/README.md](PythonPalette/README.md). Make sure Anaconda/Miniforge is installed, then open Anaconda Prompt or Miniforge Prompt:

~~~cmd
cd PythonPalette
conda env create -f environment.yml
conda activate idpalette
python -m PyInstaller --noconfirm --clean --onefile --windowed --name Archicad_ID_Palette main.py
~~~

Expected output:

~~~text
PythonPalette\\dist\\Archicad_ID_Palette.exe
~~~

If the `idpalette` environment already exists, use `conda env update -f environment.yml --prune` instead of `conda env create`. The EXE is built locally and is not committed to Git. The `archicad` package version must match your installed Archicad release.

## Install and configure

1. Build `IDPaletteLauncher.apx` and `Archicad_ID_Palette.exe` separately.
2. Copy the `.apx` to a folder Archicad can load add-ons from, or add it through Archicad's Add-On Manager.
3. Either place `Archicad_ID_Palette.exe` next to the `.apx`, or configure its full path in `IDPaletteLauncher.ini`.
4. Copy `IDPaletteLauncher.ini.example` to `IDPaletteLauncher.ini` in the same folder as the `.apx`, then adjust the values.
5. Restart/reload the add-on as needed.

Example `IDPaletteLauncher.ini`:

~~~ini
[Launcher]
ExecutablePath=Archicad_ID_Palette.exe
WindowTitle=ID & Custom Properties
~~~

`ExecutablePath` can be an absolute path or a path relative to the `.apx` directory. If the EXE is stored elsewhere, use its real full path. `WindowTitle` must match the palette's top-level window title exactly.

The Python application reads/writes `config.json` next to `main.py` when running from source, or next to the EXE when packaged. Copy `PythonPalette/config.json.example` to `config.json` in the application folder if you want to start with an explicit empty configuration. The palette also creates a default in memory when no config file exists.

## Smoke-test checklist

- [ ] CMake configures with the matching Archicad DevKit.
- [ ] The C++ add-on builds to an `.apx`.
- [ ] The Python app starts with Archicad open and a project loaded.
- [ ] The menu item appears and launches the EXE.
- [ ] Selecting an element updates the palette display.
- [ ] A test edit updates the intended property/classification in a test project.
- [ ] Selecting multiple elements and editing values behaves as expected.
- [ ] A missing executable produces a useful error.
- [ ] The palette can be brought to the foreground without opening duplicates.
- [ ] Verify behavior on each Archicad version and Windows environment you plan to support.

## Security and data safety

- Do not commit credentials, API keys, or sensitive project data.
- Only launch an EXE built from a trusted source and stored in a directory with appropriate write permissions.
- Test bulk property changes on a copy of the project before production use.
- Window-title detection is a pragmatic launcher mechanism, not a strong process identity check. If a stable IPC or process handshake becomes available, consider it for production deployment.
