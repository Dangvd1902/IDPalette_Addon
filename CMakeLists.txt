cmake_minimum_required (VERSION 3.16)
project (IDPaletteLauncher LANGUAGES CXX RC)

if (NOT WIN32 OR NOT MSVC)
    message (FATAL_ERROR "IDPaletteLauncher is a Windows/MSVC Archicad add-on. Configure with a Visual Studio generator.")
endif ()

set (CMAKE_CXX_STANDARD 20)
set (CMAKE_CXX_STANDARD_REQUIRED ON)
set (CMAKE_CXX_EXTENSIONS OFF)

set (AC_API_DEVKIT_DIR "C:/API.Development.Kit.WIN.30.3000" CACHE PATH
    "Path to the installed Archicad API DevKit")
set (SUPPORT_DIR "${AC_API_DEVKIT_DIR}/Support")
set (RESCONV_EXE "${SUPPORT_DIR}/Tools/Win/ResConv.exe")

if (NOT EXISTS "${RESCONV_EXE}")
    message (FATAL_ERROR
        "Archicad API DevKit resource compiler was not found: ${RESCONV_EXE}\n"
        "Set AC_API_DEVKIT_DIR to the root of your installed Archicad API DevKit.")
endif ()

if (NOT EXISTS "${SUPPORT_DIR}/Inc/ACAPinc.h")
    message (FATAL_ERROR
        "Archicad API headers were not found under ${SUPPORT_DIR}/Inc.\n"
        "Check AC_API_DEVKIT_DIR and make sure the matching DevKit is installed.")
endif ()

if (NOT EXISTS "${SUPPORT_DIR}/Lib/Win/ACAP_STAT.lib")
    message (FATAL_ERROR
        "Archicad API library was not found: ${SUPPORT_DIR}/Lib/Win/ACAP_STAT.lib")
endif ()

file (MAKE_DIRECTORY "${CMAKE_BINARY_DIR}/RO")
file (MAKE_DIRECTORY "${CMAKE_BINARY_DIR}/out")
file (MAKE_DIRECTORY "${CMAKE_BINARY_DIR}/lib")

add_custom_command (
    OUTPUT "${CMAKE_BINARY_DIR}/RO/AddOn.grc.rc2"
    COMMAND "${RESCONV_EXE}"
        -m r -D WINDOWS -T W -q utf8 1252
        -i "${CMAKE_CURRENT_SOURCE_DIR}/Src/AddOn.grc"
        -p "${CMAKE_CURRENT_SOURCE_DIR}/Src"
        -o "${CMAKE_BINARY_DIR}/RO/AddOn.grc.rc2"
    DEPENDS
        "${CMAKE_CURRENT_SOURCE_DIR}/Src/AddOn.grc"
        "${CMAKE_CURRENT_SOURCE_DIR}/Src/ResourceIds.hpp"
    COMMENT "Compiling Archicad add-on resources"
    VERBATIM
)

file (WRITE "${CMAKE_BINARY_DIR}/RO/AddOnMain.rc"
    "#include <windows.h>\n"
    "#include \"${CMAKE_BINARY_DIR}/RO/AddOn.grc.rc2\"\n"
)

add_library (${PROJECT_NAME} SHARED
    Src/AddOnMain.cpp
    Src/ResourceIds.hpp
    "${CMAKE_BINARY_DIR}/RO/AddOnMain.rc"
    "${CMAKE_BINARY_DIR}/RO/AddOn.grc.rc2"
)

set_target_properties (${PROJECT_NAME} PROPERTIES
    SUFFIX ".apx"
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/out"
    ARCHIVE_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/lib"
)

# Keep the output paths stable for Visual Studio's multi-configuration generator.
foreach (CONFIG_NAME DEBUG RELEASE RELWITHDEBINFO MINSIZEREL)
    set_target_properties (${PROJECT_NAME} PROPERTIES
        "RUNTIME_OUTPUT_DIRECTORY_${CONFIG_NAME}" "${CMAKE_BINARY_DIR}/out"
        "ARCHIVE_OUTPUT_DIRECTORY_${CONFIG_NAME}" "${CMAKE_BINARY_DIR}/lib"
    )
endforeach ()

target_compile_definitions (${PROJECT_NAME} PRIVATE WINDOWS _USRDLL UNICODE _UNICODE)
target_compile_options (${PROJECT_NAME} PRIVATE /W3 /EHsc /utf-8 /Zc:wchar_t-)

file (GLOB MODULE_INC_DIRS CONFIGURE_DEPENDS
    "${SUPPORT_DIR}/Modules/*")
target_include_directories (${PROJECT_NAME} PRIVATE
    "${CMAKE_CURRENT_SOURCE_DIR}/Src"
    "${SUPPORT_DIR}/Inc"
    ${MODULE_INC_DIRS}
)

file (GLOB MODULE_LIB_FILES CONFIGURE_DEPENDS
    "${SUPPORT_DIR}/Modules/*/*.lib"
    "${SUPPORT_DIR}/Modules/*/Win/*.lib")
target_link_libraries (${PROJECT_NAME} PRIVATE
    "${SUPPORT_DIR}/Lib/Win/ACAP_STAT.lib"
    ${MODULE_LIB_FILES}
    user32.lib
    shell32.lib
)
