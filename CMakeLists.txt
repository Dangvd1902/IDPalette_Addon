cmake_minimum_required (VERSION 3.16)
project (IDPaletteLauncher)

# Bắt buộc ép CMake biên dịch theo chuẩn C++20 cho toàn bộ dự án
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set (AC_API_DEVKIT_DIR "C:/API.Development.Kit.WIN.30.3000" CACHE PATH "Path to Archicad API DevKit")
set (SUPPORT_DIR "${AC_API_DEVKIT_DIR}/Support")
set (RESCONV_EXE "${SUPPORT_DIR}/Tools/Win/ResConv.exe")

file (MAKE_DIRECTORY "${CMAKE_BINARY_DIR}/RO")

add_custom_command (
    OUTPUT "${CMAKE_BINARY_DIR}/RO/AddOn.grc.rc2"
    COMMAND "${RESCONV_EXE}"
        -m r -D WINDOWS -T W -q utf8 1252
        -i "${CMAKE_CURRENT_SOURCE_DIR}/Src/AddOn.grc"
        -p "${CMAKE_CURRENT_SOURCE_DIR}/Src"
        -o "${CMAKE_BINARY_DIR}/RO/AddOn.grc.rc2"
    DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/Src/AddOn.grc" "${CMAKE_CURRENT_SOURCE_DIR}/Src/ResourceIds.hpp"
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

set_target_properties (${PROJECT_NAME} PROPERTIES SUFFIX ".apx")
target_compile_definitions (${PROJECT_NAME} PRIVATE WINDOWS _USRDLL UNICODE _UNICODE)
target_compile_options (${PROJECT_NAME} PRIVATE /W3 /EHsc /utf-8 /Zc:wchar_t-)

file (GLOB MODULE_INC_DIRS "${SUPPORT_DIR}/Modules/*")
target_include_directories (${PROJECT_NAME} PRIVATE
    "${CMAKE_CURRENT_SOURCE_DIR}/Src"
    "${SUPPORT_DIR}/Inc"
    ${MODULE_INC_DIRS}
)

file (GLOB MODULE_LIB_FILES "${SUPPORT_DIR}/Modules/*/*.lib" "${SUPPORT_DIR}/Modules/*/Win/*.lib")
target_link_libraries (${PROJECT_NAME} PRIVATE
    "${SUPPORT_DIR}/Lib/Win/ACAP_STAT.lib"
    ${MODULE_LIB_FILES}
    user32.lib
    shell32.lib
)