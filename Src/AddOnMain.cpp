#include "ACAPinc.h"
#include "ResourceIds.hpp"
#include <windows.h>
#include <shellapi.h>

static const wchar_t* EXE_PATH = L"C:\\Users\\Admin\\Desktop\\PR1\\Infobox\\dist\\Archicad_ID_Palette.exe";
static const wchar_t* WORK_DIR = L"C:\\Users\\Admin\\Desktop\\PR1\\Infobox\\dist";
static const wchar_t* PALETTE_WINDOW_TITLE = L"ID & Custom Properties";

static GSErrCode MenuCommandHandler (const API_MenuParams* menuParams)
{
    if (menuParams == nullptr) {
        return NoError;
    }

    if (menuParams->menuItemRef.menuResID == ID_ADDON_MENU &&
        (menuParams->menuItemRef.itemIndex == 0 || menuParams->menuItemRef.itemIndex == 1))
    {
        HWND existingHwnd = FindWindowW (nullptr, PALETTE_WINDOW_TITLE);
        if (existingHwnd != nullptr) {
            if (IsIconic (existingHwnd)) {
                ShowWindow (existingHwnd, SW_RESTORE);
            }
            SetForegroundWindow (existingHwnd);
            return NoError;
        }

        HINSTANCE res = ShellExecuteW (
            nullptr, L"open", EXE_PATH, nullptr, WORK_DIR, SW_SHOWNORMAL
        );

        if ((INT_PTR)res <= 32) {
            ACAPI_WriteReport ("Không tìm thấy file Archicad_ID_Palette.exe!", true);
        }
    }
    return NoError;
}

API_AddonType CheckEnvironment (API_EnvirParams* envir)
{
    RSGetIndString (&envir->addOnInfo.name, ID_ADDON_INFO, 1, ACAPI::GetOwnResModule ());
    RSGetIndString (&envir->addOnInfo.description, ID_ADDON_INFO, 2, ACAPI::GetOwnResModule ());
    return APIAddon_Normal;
}

GSErrCode RegisterInterface (void)
{
    return ACAPI::MenuItem_RegisterMenu (ID_ADDON_MENU, 0, MenuCode_Palettes, MenuFlag_Default);
}

GSErrCode Initialize (void)
{
    return ACAPI::MenuItem_InstallMenuHandler (ID_ADDON_MENU, MenuCommandHandler);
}

GSErrCode FreeData (void)
{
    return NoError;
}