#include "ACAPinc.h"
#include "ResourceIds.hpp"

#include <windows.h>
#include <shellapi.h>

#include <array>
#include <filesystem>
#include <string>

namespace {

constexpr wchar_t DefaultExecutableName[] = L"Archicad_ID_Palette.exe";
constexpr wchar_t DefaultWindowTitle[] = L"ID & Custom Properties";
constexpr wchar_t ConfigFileName[] = L"IDPaletteLauncher.ini";
constexpr DWORD MaxConfigCharacters = 32768;

std::filesystem::path GetAddonDirectory ()
{
    HMODULE module = nullptr;
    const auto address = reinterpret_cast<LPCWSTR> (&GetAddonDirectory);

    if (!GetModuleHandleExW (
            GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS |
                GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
            address,
            &module)) {
        return {};
    }

    std::wstring modulePath (MaxConfigCharacters, L'\0');
    const DWORD length = GetModuleFileNameW (
        module,
        modulePath.data (),
        static_cast<DWORD> (modulePath.size ()));

    if (length == 0 || static_cast<std::size_t> (length) >= modulePath.size ()) {
        return {};
    }

    modulePath.resize (length);
    return std::filesystem::path (modulePath).parent_path ();
}

std::wstring ReadConfigValue (
    const std::filesystem::path& configPath,
    const wchar_t* key,
    const wchar_t* defaultValue)
{
    std::array<wchar_t, MaxConfigCharacters> value {};
    const DWORD length = GetPrivateProfileStringW (
        L"Launcher",
        key,
        defaultValue,
        value.data (),
        static_cast<DWORD> (value.size ()),
        configPath.c_str ());

    return std::wstring (value.data (), length);
}

std::filesystem::path GetExecutablePath (const std::filesystem::path& addonDirectory)
{
    const auto configPath = addonDirectory / ConfigFileName;
    const auto configuredPath = ReadConfigValue (
        configPath,
        L"ExecutablePath",
        DefaultExecutableName);

    if (configuredPath.empty ()) {
        return {};
    }

    std::filesystem::path executablePath (configuredPath);
    if (executablePath.is_relative ()) {
        executablePath = addonDirectory / executablePath;
    }

    return executablePath.lexically_normal ();
}

std::wstring GetPaletteWindowTitle (const std::filesystem::path& addonDirectory)
{
    return ReadConfigValue (
        addonDirectory / ConfigFileName,
        L"WindowTitle",
        DefaultWindowTitle);
}

bool IsExecutableFile (const std::filesystem::path& path)
{
    if (path.empty ()) {
        return false;
    }

    const auto extension = path.extension ().native ();
    if (CompareStringOrdinal (
            extension.c_str (),
            static_cast<int> (extension.size ()),
            L".exe",
            4,
            TRUE) != CSTR_EQUAL) {
        return false;
    }

    const DWORD attributes = GetFileAttributesW (path.c_str ());
    return attributes != INVALID_FILE_ATTRIBUTES &&
           (attributes & FILE_ATTRIBUTE_DIRECTORY) == 0;
}

void ReportLaunchError (const char* message)
{
    ACAPI_WriteReport (message, true);
}

GSErrCode MenuCommandHandler (const API_MenuParams* menuParams)
{
    if (menuParams == nullptr ||
        menuParams->menuItemRef.menuResID != ID_ADDON_MENU ||
        (menuParams->menuItemRef.itemIndex != 0 &&
         menuParams->menuItemRef.itemIndex != 1)) {
        return NoError;
    }

    const auto addonDirectory = GetAddonDirectory ();
    if (addonDirectory.empty ()) {
        ReportLaunchError (
            "Khong xac dinh duoc thu muc add-on. Hay kiem tra lai cai dat IDPaletteLauncher.");
        return NoError;
    }

    const auto windowTitle = GetPaletteWindowTitle (addonDirectory);
    const HWND existingWindow = FindWindowW (nullptr, windowTitle.c_str ());

    if (existingWindow != nullptr) {
        if (IsIconic (existingWindow)) {
            ShowWindow (existingWindow, SW_RESTORE);
        }

        SetForegroundWindow (existingWindow);
        return NoError;
    }

    const auto executablePath = GetExecutablePath (addonDirectory);
    if (!IsExecutableFile (executablePath)) {
        OutputDebugStringW (
            (L"IDPaletteLauncher: executable not found or invalid: " +
             executablePath.native () + L"\n").c_str ());
        ReportLaunchError (
            "Khong tim thay Archicad_ID_Palette.exe. Hay dat file canh add-on "
            "hoac cau hinh ExecutablePath trong IDPaletteLauncher.ini.");
        return NoError;
    }

    const auto workingDirectory = executablePath.parent_path ();
    const HINSTANCE result = ShellExecuteW (
        nullptr,
        L"open",
        executablePath.c_str (),
        nullptr,
        workingDirectory.c_str (),
        SW_SHOWNORMAL);

    if (reinterpret_cast<INT_PTR> (result) <= 32) {
        const auto errorCode = reinterpret_cast<INT_PTR> (result);
        const std::string message =
            "Khong the khoi chay ID & Custom Properties Palette. ShellExecute code: " +
            std::to_string (errorCode) + ".";
        ReportLaunchError (message.c_str ());
        return NoError;
    }

    return NoError;
}

} // namespace

API_AddonType CheckEnvironment (API_EnvirParams* envir)
{
    RSGetIndString (
        &envir->addOnInfo.name,
        ID_ADDON_INFO,
        1,
        ACAPI::GetOwnResModule ());
    RSGetIndString (
        &envir->addOnInfo.description,
        ID_ADDON_INFO,
        2,
        ACAPI::GetOwnResModule ());

    return APIAddon_Normal;
}

GSErrCode RegisterInterface (void)
{
    return ACAPI::MenuItem_RegisterMenu (
        ID_ADDON_MENU,
        0,
        MenuCode_Palettes,
        MenuFlag_Default);
}

GSErrCode Initialize (void)
{
    return ACAPI::MenuItem_InstallMenuHandler (
        ID_ADDON_MENU,
        MenuCommandHandler);
}

GSErrCode FreeData (void)
{
    return NoError;
}
