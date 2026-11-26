//     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

// Windows splash screen rendering and feedback file handling.

#ifndef _WIN32
#error "OnefileSplashScreen.c is Windows only"
#else

#define CINTERFACE
#define COBJMACROS

// Note: Keep this separate line, must be included before other Windows headers.
#include <windows.h>

#include <wincodec.h>

#include <assert.h>
#ifndef __cplusplus
#include <stdbool.h>
#endif

#include "nuitka/hedley.h"
#define likely(x) HEDLEY_LIKELY(x)
#define unlikely(x) HEDLEY_UNLIKELY(x)
#ifdef __GNUC__
#define NUITKA_MAY_BE_UNUSED __attribute__((__unused__))
#else
#define NUITKA_MAY_BE_UNUSED
#endif

#include "nuitka/environment_variables_system.h"
#include "nuitka/filesystem_paths.h"
#include "nuitka/safe_string_ops.h"
#include "nuitka/tracing.h"

// Windows SDK guiddef.h defines REFGUID/REFIID/REFCLSID as C++ references under
// __cplusplus even when CINTERFACE is enabled, which matters when non-C11 mode
// compiles C files as C++.
#ifdef __cplusplus
#define NUITKA_REFGUID(x) (x)
#else
#define NUITKA_REFGUID(x) (&(x))
#endif

static IStream *createImageStream(void) {
    HRSRC res_handle = FindResource(NULL, MAKEINTRESOURCE(28), RT_RCDATA);
    if (res_handle == NULL) {
        return NULL;
    }
    DWORD resource_size = SizeofResource(NULL, res_handle);
    HGLOBAL image_handle = LoadResource(NULL, res_handle);
    if (image_handle == NULL) {
        return NULL;
    }
    LPVOID resource_data = LockResource(image_handle);
    if (resource_data == NULL) {
        return NULL;
    }

    HGLOBAL temp_data_handle = GlobalAlloc(GMEM_MOVEABLE, resource_size);
    if (temp_data_handle == NULL) {
        return NULL;
    }

    LPVOID temp_data = GlobalLock(temp_data_handle);
    if (temp_data == NULL) {
        GlobalFree(temp_data_handle);
        return NULL;
    }

    CopyMemory(temp_data, resource_data, resource_size);
    GlobalUnlock(temp_data_handle);

    IStream *result = NULL;
    if (SUCCEEDED(CreateStreamOnHGlobal(temp_data_handle, TRUE, &result))) {
        return result;
    }

    GlobalFree(temp_data_handle);

    return NULL;
}

static IWICBitmapSource *getBitmapFromImageStream(IStream *image_stream) {
    IWICBitmapDecoder *ipDecoder = NULL;
    if (FAILED(CoCreateInstance(NUITKA_REFGUID(CLSID_WICPngDecoder), NULL, CLSCTX_INPROC_SERVER,
                                NUITKA_REFGUID(IID_IWICBitmapDecoder), (void **)(&ipDecoder)))) {
        return NULL;
    }
    if (FAILED(IWICBitmapDecoder_Initialize(ipDecoder, image_stream, WICDecodeMetadataCacheOnLoad))) {
        IWICBitmapDecoder_Release(ipDecoder);
        return NULL;
    }
    UINT frame_count = 0;
    if (FAILED(IWICBitmapDecoder_GetFrameCount(ipDecoder, &frame_count)) || frame_count != 1) {
        IWICBitmapDecoder_Release(ipDecoder);
        return NULL;
    }
    IWICBitmapFrameDecode *ipFrame = NULL;
    if (FAILED(IWICBitmapDecoder_GetFrame(ipDecoder, 0, &ipFrame))) {
        IWICBitmapDecoder_Release(ipDecoder);
        return NULL;
    }

    // UpdateLayeredWindow with ULW_ALPHA requires premultiplied 32bpp BGRA.
    IWICBitmapSource *ipBitmap = NULL;
    WICConvertBitmapSource(NUITKA_REFGUID(GUID_WICPixelFormat32bppPBGRA), (IWICBitmapSource *)ipFrame, &ipBitmap);

    IWICBitmapFrameDecode_Release(ipFrame);
    IWICBitmapDecoder_Release(ipDecoder);

    return ipBitmap;
}

static HBITMAP createSplashBitmap(IWICBitmapSource *ipBitmap) {
    UINT width = 0;
    UINT height = 0;
    if (FAILED(IWICBitmapSource_GetSize(ipBitmap, &width, &height)) || width == 0 || height == 0) {
        return NULL;
    }

    BITMAPINFO bitmap_info;
    memset(&bitmap_info, 0, sizeof(bitmap_info));
    bitmap_info.bmiHeader.biSize = sizeof(BITMAPINFOHEADER);
    bitmap_info.bmiHeader.biWidth = width;
    bitmap_info.bmiHeader.biHeight = -((LONG)height); // Negative height selects a top-down DIB.
    bitmap_info.bmiHeader.biPlanes = 1;
    bitmap_info.bmiHeader.biBitCount = 32;
    bitmap_info.bmiHeader.biCompression = BI_RGB;

    HDC handle_screen = GetDC(NULL);
    void *image_data = NULL;
    HBITMAP handle_bmp = CreateDIBSection(handle_screen, &bitmap_info, DIB_RGB_COLORS, &image_data, NULL, 0);
    ReleaseDC(NULL, handle_screen);
    if (handle_bmp == NULL) {
        return NULL;
    }

    const UINT stride = width * 4;
    const UINT size = stride * height;
    if (FAILED(IWICBitmapSource_CopyPixels(ipBitmap, NULL, stride, size, (BYTE *)(image_data)))) {
        DeleteObject(handle_bmp);
        return NULL;
    }

    return handle_bmp;
}

static HWND createSplashWindow(HBITMAP splash_bitmap) {
    WNDCLASSA wc = {0};
    wc.lpfnWndProc = DefWindowProc;
    wc.hCursor = LoadCursor(NULL, IDC_ARROW);
    wc.lpszClassName = "Splash";
    RegisterClassA(&wc);

    HWND splash_window = CreateWindowExA(WS_EX_LAYERED, wc.lpszClassName, NULL,
                                         WS_POPUP | WS_VISIBLE | WS_EX_TOOLWINDOW, 0, 0, 0, 0, 0, NULL, 0, NULL);
    assert(splash_window != NULL);

    BITMAP bitmap;
    GetObject(splash_bitmap, sizeof(bitmap), &bitmap);
    SIZE sizeSplash = {bitmap.bmWidth, bitmap.bmHeight};

    // spell-checker: ignore HMONITOR,MONITORINFO,MONITOR_DEFAULTTOPRIMARY
    POINT zero = {0};
    HMONITOR handle_monitor = MonitorFromPoint(zero, MONITOR_DEFAULTTOPRIMARY);
    MONITORINFO monitorinfo = {0};
    monitorinfo.cbSize = sizeof(monitorinfo);
    GetMonitorInfo(handle_monitor, &monitorinfo);

    POINT ptOrigin;
    ptOrigin.x = monitorinfo.rcWork.left + (monitorinfo.rcWork.right - monitorinfo.rcWork.left - sizeSplash.cx) / 2;
    ptOrigin.y = monitorinfo.rcWork.top + (monitorinfo.rcWork.bottom - monitorinfo.rcWork.top - sizeSplash.cy) / 2;

#if _NUITKA_TRACE
    printf("Onefile: Splash screen origin %ld %ld for sizes %ld %ld\n", ptOrigin.x, ptOrigin.y, sizeSplash.cx,
           sizeSplash.cy);
#endif
    HDC handle_screen = GetDC(NULL);
    HDC handle_memory = CreateCompatibleDC(handle_screen);
    HBITMAP handle_old_bitmap = (HBITMAP)SelectObject(handle_memory, splash_bitmap);

    // spell-checker: ignore BLENDFUNCTION
    BLENDFUNCTION blend = {0};
    blend.BlendOp = AC_SRC_OVER;
    blend.SourceConstantAlpha = 255;
    blend.AlphaFormat = AC_SRC_ALPHA;

    UpdateLayeredWindow(splash_window, handle_screen, &ptOrigin, &sizeSplash, handle_memory, &zero, RGB(0, 0, 0),
                        &blend, ULW_ALPHA);

    SelectObject(handle_memory, handle_old_bitmap);
    DeleteDC(handle_memory);
    ReleaseDC(NULL, handle_screen);

    return splash_window;
}

static HWND splash_window = 0;
static wchar_t splash_indicator_path[4096] = {0};
static bool splash_active = false;

static bool isSplashScreenShown(void) {
    environment_char_t const *splash_screen_setting = getEnvironmentVariable("NUITKA_SPLASH_SCREEN");

    if (splash_screen_setting == NULL) {
        return true;
    }

    return _wcsicmp(splash_screen_setting, L"0") != 0 && _wcsicmp(splash_screen_setting, L"off") != 0;
}

#ifdef __cplusplus
extern "C"
#endif
    void initSplashScreen(void) {
    NUITKA_PRINT_TIMING("ONEFILE: Initialize splash screen.");

    if (isSplashScreenShown()) {
        CoInitialize(NULL);
        IStream *image_stream = createImageStream();
        if (unlikely(image_stream == NULL)) {
            NUITKA_PRINT_TIMING("ONEFILE: Failed to create image stream.");
            return;
        }
        IWICBitmapSource *image_source = getBitmapFromImageStream(image_stream);
        IStream_Release(image_stream);
        if (unlikely(image_source == NULL)) {
            NUITKA_PRINT_TIMING("ONEFILE: Failed to get image source from image stream.");
            return;
        }
        HBITMAP splash_bitmap = createSplashBitmap(image_source);
        IWICBitmapSource_Release(image_source);
        if (unlikely(splash_bitmap == NULL)) {
            NUITKA_PRINT_TIMING("ONEFILE: Failed to get bitmap.");
            return;
        }

        splash_window = createSplashWindow(splash_bitmap);
    }

    // Even when not displaying a splash screen, the feedback file is created,
    // so that application code deleting it to dismiss the splash screen keeps
    // working, and the splash screen protocol remains tested.
    // TODO: This probably should be user provided.
    wchar_t const *pattern = L"{TEMP}\\onefile_{PID}_splash_feedback.tmp";
    bool bool_res =
        expandTemplatePathW(splash_indicator_path, pattern, sizeof(splash_indicator_path) / sizeof(wchar_t));
    if (unlikely(bool_res == false)) {
        NUITKA_PRINT_TIMING("Failed expand indicator path.");
        return;
    }

    HANDLE handle_splash_file =
        CreateFileW(splash_indicator_path, GENERIC_WRITE, FILE_SHARE_WRITE, NULL, CREATE_ALWAYS, 0, NULL);
    CloseHandle(handle_splash_file);

    splash_active = true;

    NUITKA_PRINT_TIMING("ONEFILE: Done with splash screen.");
}

static void closeSplashScreen(void) {
    NUITKA_PRINT_TIMING("ONEFILE: Check splash screen indicator file.");

    if (splash_window) {
        DestroyWindow(splash_window);
        splash_window = 0;
    }
}

#ifdef __cplusplus
extern "C"
#endif
    bool checkSplashScreen(void) {
    if (splash_active) {
        NUITKA_PRINT_TIMING("ONEFILE: Check splash screen indicator file.");

        if (GetFileAttributesW(splash_indicator_path) == INVALID_FILE_ATTRIBUTES) {
            closeSplashScreen();
            splash_active = false;
        }
    }

    return splash_active == false;
}

#endif

//     Part of "Nuitka", an optimizing Python compiler that is compatible and
//     integrates with CPython, but also works on its own.
//
//     Licensed under the GNU Affero General Public License, Version 3 (the "License");
//     you may not use this file except in compliance with the License.
//     You may obtain a copy of the License at
//
//        https://www.gnu.org/licenses/agpl-3.0.txt
//
//     See also: "Nuitka Runtime Library Exception, Version 1.0" in file
//     "LICENSE-RUNTIME.txt" for additional permissions granted under Section 7.
//
//     Unless required by applicable law or agreed to in writing, software
//     distributed under the License is distributed on an "AS IS" BASIS,
//     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//     See the License for the specific language governing permissions and
//     limitations under the License.
