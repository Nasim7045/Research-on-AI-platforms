#include <windows.h>
#include <shlobj.h>
#include <stdio.h>
#include <string.h>

#pragma comment(lib, "shell32.lib")

// ─── CONFIG ───────────────────────────────────────────────────────────────────
#define EXE_NAME     "startup_agent.exe"   // name in startup folder
#define REG_KEY_NAME "StartupAgent"        // registry key name
// ──────────────────────────────────────────────────────────────────────────────

void get_exe_path(char *buf, size_t size) {
    GetModuleFileName(NULL, buf, (DWORD)size);
}

void get_startup_folder(char *buf, size_t size) {
    SHGetFolderPath(NULL, CSIDL_STARTUP, NULL, 0, buf);
}

int is_installed() {
    char exe_path[MAX_PATH]  = {0};
    char startup[MAX_PATH]   = {0};
    char installed[MAX_PATH] = {0};

    get_exe_path(exe_path, sizeof(exe_path));
    get_startup_folder(startup, sizeof(startup));
    snprintf(installed, sizeof(installed), "%s\\%s", startup, EXE_NAME);

    return (_stricmp(exe_path, installed) == 0);
}

void install() {
    char exe_src[MAX_PATH] = {0};
    char exe_dst[MAX_PATH] = {0};
    char startup[MAX_PATH] = {0};

    get_exe_path(exe_src, sizeof(exe_src));
    get_startup_folder(startup, sizeof(startup));
    snprintf(exe_dst, sizeof(exe_dst), "%s\\%s", startup, EXE_NAME);

    CopyFile(exe_src, exe_dst, FALSE);

    // Registry run key — visible in Task Manager startup tab, can be disabled
    HKEY hkey;
    if (RegOpenKeyEx(HKEY_CURRENT_USER,
                     "Software\\Microsoft\\Windows\\CurrentVersion\\Run",
                     0, KEY_SET_VALUE, &hkey) == ERROR_SUCCESS) {
        RegSetValueEx(hkey, REG_KEY_NAME, 0, REG_SZ,
                      (BYTE*)exe_dst, (DWORD)(strlen(exe_dst) + 1));
        RegCloseKey(hkey);
    }

    // Relaunch from startup location
    ShellExecute(NULL, "open", exe_dst, NULL, startup, SW_HIDE);
    ExitProcess(0);
}

// ── Add any future task here — runs every loop ────────────────────────────────
void do_work() {
    // placeholder — add your IT management logic here
    // e.g. check for updates, sync config, launch another tool, etc.
}

int WINAPI WinMain(HINSTANCE hInst, HINSTANCE hPrev, LPSTR lpCmd, int nShow) {

    if (!is_installed()) {
        install();
        return 0;
    }

    // Running from startup — loop and do work
    while (1) {
        do_work();
        Sleep(60000); // check every 60 seconds
    }

    return 0;
}
