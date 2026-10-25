# IDPaletteLauncher

Archicad Windows add-on that adds an **ID & Custom Properties Palette** menu item and launches **Archicad_ID_Palette.exe** when selected.

> This repository builds the Archicad launcher (.apx), not the palette application itself. The palette executable must be supplied separately.

## Current behavior

- Registers a palette menu item through the Archicad Add-On API.
- If a window titled "ID & Custom Properties" already exists, restores it when minimized and brings it to the foreground.
- Otherwise, launches the configured executable.
- Resolves the add-on directory at runtime instead of embedding a developer-specific absolute path.
- Reports a useful error if the executable is missing or Windows cannot launch it.

## Requirements

- Windows and Visual Studio C++ build tools (MSVC).
- CMake 3.16 or newer.
- A compatible Archicad API DevKit installed locally.
- Archicad_ID_Palette.exe built and tested separately.

The default AC_API_DEVKIT_DIR points to C:/API.Development.Kit.WIN.30.3000. Use the actual DevKit directory/version installed on your machine.

## Build

Run this as one command from a Developer PowerShell for Visual Studio or a terminal where MSVC is available:

~~~powershell
cmake -S . -B build -G "Visual Studio 17 2022" -A x64 -DAC_API_DEVKIT_DIR="C:/API.Development.Kit.WIN.30.3000"
cmake --build build --config Release
~~~

If you use a different Visual Studio version, change the generator accordingly. CMake stops with an explicit error if the configured DevKit resource compiler, headers, or import library cannot be found.

The expected add-on output is:

~~~text
build/out/IDPaletteLauncher.apx
~~~

The output has not been built or tested by CI in this repository. Use a DevKit version that matches the Archicad version you intend to support and validate the resulting .apx in that Archicad installation.

## Install and configure

1. Build the .apx.
2. Copy IDPaletteLauncher.apx to a directory that Archicad is configured to load add-ons from, or load it through Archicad's Add-On Manager.
3. Put Archicad_ID_Palette.exe next to the .apx, or configure its location in IDPaletteLauncher.ini.
4. Copy IDPaletteLauncher.ini.example to IDPaletteLauncher.ini in the same directory as the .apx, then adjust the values.
5. Restart/reload the add-on as required by the installed Archicad version.

Example configuration:

~~~ini
[Launcher]
ExecutablePath=Archicad_ID_Palette.exe
WindowTitle=ID & Custom Properties
~~~

ExecutablePath can be an absolute path or a path relative to the .apx directory. Use a trusted executable in a directory that ordinary users cannot replace unexpectedly. WindowTitle must match the palette's top-level window title exactly.

## Smoke-test checklist

- [ ] Archicad loads the .apx without reporting an add-on load error.
- [ ] The menu item appears.
- [ ] Selecting the menu opens the palette when it is not running.
- [ ] Selecting the menu restores/foregrounds an existing minimized palette.
- [ ] A missing executable produces a clear message rather than silently failing.
- [ ] A non-default configured executable path works.
- [ ] The palette's actual window title matches the configured value.
- [ ] Verify behavior on each Archicad version and Windows environment you plan to support.

## Security notes

- Do not commit credentials, API keys, or secrets into this repository.
- Only configure an executable obtained from a trusted build/release source.
- The add-on launcher does not implement user authentication. Any authentication in the palette executable is outside this repository's current scope.
- Window-title detection is a pragmatic integration mechanism, not a strong process identity check. If the palette app can expose a stable IPC or process handshake, prefer that for production deployments.

## Repository layout

- CMakeLists.txt: CMake configuration and SDK checks.
- Src/AddOnMain.cpp: add-on lifecycle, menu handler and launcher.
- Src/AddOn.grc: add-on metadata and menu resources.
- Src/ResourceIds.hpp: resource IDs.
- IDPaletteLauncher.ini.example: sample per-installation configuration.
