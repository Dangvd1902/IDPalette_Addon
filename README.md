# IDPalette Add-on — Archicad 29 branch

This branch, `support/archicad-29`, targets Archicad 29. The `master` branch remains the primary branch for Archicad 30. Keep build directories, Conda environments and generated executables separate so this branch does not overwrite Archicad 30 artifacts.

The project has two components:

1. **C++ launcher add-on** — registers the Archicad menu command and starts the Python palette EXE.
2. **Python ID & Custom Properties palette** — reads and updates selected element properties and classifications through Graphisoft's Python binding for the local JSON API.

Building the `.apx` and building the EXE are separate steps.

## Versions for this branch

- Archicad target: **29**.
- C++ API DevKit: use the official [Graphisoft Archicad 29 DevKit](https://github.com/GRAPHISOFT/archicad-api-devkit/releases); the latest published Archicad 29 DevKit found during setup is **29.3100**. Confirm the extracted directory name and pass the actual path to CMake.
- Windows C++ toolset: Visual Studio 2022 / MSVC **v143**.
- Python API package: Graphisoft `archicad==29.3000` from [PyPI](https://pypi.org/project/archicad/29.3000/).

The C++ DevKit build version and Python package version do not have to share identical build numbers; use the official version intended for Archicad 29 for each component.

## Build the C++ launcher (.apx)

Install the Archicad 29 DevKit and Visual Studio 2022 Build Tools with MSVC v143, Windows SDK and CMake tools. Open Developer PowerShell for VS 2022 or a terminal where CMake and MSBuild are available.

~~~powershell
git switch support/archicad-29
cmake -S . -B build-ac29 -G "Visual Studio 17 2022" -A x64 -T v143 -DAC_API_DEVKIT_DIR="C:/API.Development.Kit.WIN.29.3100"
cmake --build build-ac29 --config Release
~~~

If your extracted DevKit folder is named differently, replace `C:/API.Development.Kit.WIN.29.3100` with its actual path. Do not point the Archicad 29 build at the Archicad 30 DevKit.

Expected output:

~~~text
build-ac29/out/IDPaletteLauncher.apx
~~~

The C++ target uses `CMakeLists.txt`; its DevKit default is set to the Archicad 29 path on this branch. Use the explicit `-DAC_API_DEVKIT_DIR=...` argument to avoid ambiguity.

## Build the Python palette EXE with Conda

Open Anaconda Prompt or Miniforge Prompt:

~~~cmd
cd PythonPalette
conda env create -f environment.yml
conda activate idpalette-ac29
python -m PyInstaller --noconfirm --clean --onefile --windowed --name Archicad_ID_Palette --distpath dist-ac29 --workpath build-pyinstaller-ac29 main.py
~~~

Expected output:

~~~text
PythonPalette\\dist-ac29\\Archicad_ID_Palette.exe
~~~

If the Conda environment already exists, run `conda env update -f environment.yml --prune` instead of creating it again. The generated EXE is a local build output and is not committed to Git.

## Install and configure

1. Build both `.apx` and EXE using the Archicad 29 settings above.
2. Load the `.apx` through Archicad 29 Add-On Manager.
3. Place the EXE next to the `.apx` or set its full path in `IDPaletteLauncher.ini`.
4. Ensure `WindowTitle=ID & Custom Properties`.
5. Preserve `config.json` next to the EXE so the palette configuration remains available.

## Test before use

- [ ] CMake locates the Archicad 29 DevKit resource compiler, headers and import libraries.
- [ ] The add-on builds and loads in Archicad 29.
- [ ] The palette EXE connects to Archicad 29.
- [ ] Properties and classifications can be read and written in a test project.
- [ ] Multiple selection behaves as intended before bulk edits.
- [ ] The palette hides when Archicad is minimized and restores when it becomes visible.
- [ ] The Archicad 29 build does not overwrite the Archicad 30 build artifacts.

No Windows/Archicad build or end-to-end test is performed by this documentation update. Test on a copy of the project and validate the resulting files in the target Archicad 29 installation before production use. The registered MDID in `Src/AddOn.grc` is retained from the master's registered add-on.
