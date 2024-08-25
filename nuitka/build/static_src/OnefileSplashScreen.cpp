//     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

// Creates a stream object initialized with the data from an executable resource.

#include <shlwapi.h>
#include <wincodec.h>
#include <windows.h>

#include <assert.h>

// Some handy macro definitions, e.g. unlikely and NUITKA_MAY_BE_UNUSED
#include "nuitka/hedley.h"
#define likely(x) HEDLEY_LIKELY(x)
#define unlikely(x) HEDLEY_UNLIKELY(x)
#ifdef __GNUC__
#define NUITKA_MAY_BE_UNUSED __attribute__((__unused__))
#else
#define NUITKA_MAY_BE_UNUSED
#endif

#ifndef _NUITKA_NON_C11_MODE
extern "C" {
#endif
#include "nuitka/filesystem_paths.h"
#include "nuitka/safe_string_ops.h"
#include "nuitka/tracing.h"
#ifndef _NUITKA_NON_C11_MODE
};
#endif
IStream *createImageStream(void) {

    // Load the resource with image data
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
        return NULL;
    }

    // Copy the data from the resource to the new memory block
    CopyMemory(temp_data, resource_data, resource_size);
    GlobalUnlock(temp_data_handle);

    // Create stream on the HGLOBAL containing the data
    IStream *result = NULL;
    if (SUCCEEDED(CreateStreamOnHGlobal(temp_data_handle, TRUE, &result))) {
        return result;
    }

    GlobalFree(temp_data_handle);

    return NULL;
}

IWICBitmapSource *getBitmapFromImageStream(IStream *image_stream) {
    // Load the PNG
    IWICBitmapDecoder *ipDecoder = NULL;
    if (FAILED(CoCreateInstance(CLSID_WICPngDecoder, NULL, CLSCTX_INPROC_SERVER, __uuidof(ipDecoder),
                                (void **)(&ipDecoder)))) {
        return NULL;
    }
    if (FAILED(ipDecoder->Initialize(image_stream, WICDecodeMetadataCacheOnLoad))) {
        return NULL;
    }
    UINT frame_count = 0;
    if (FAILED(ipDecoder->GetFrameCount(&frame_count)) || frame_count != 1) {
        return NULL;
    }
    IWICBitmapFrameDecode *ipFrame = NULL;
    if (FAILED(ipDecoder->GetFrame(0, &ipFrame))) {
        return NULL;
    }

    // Convert the image to 32bpp BGRA with alpha channel
    IWICBitmapSource *ipBitmap = NULL;

    WICConvertBitmapSource(GUID_WICPixelFormat32bppPBGRA, ipFrame, &ipBitmap);

    ipFrame->Release();
    ipDecoder->Release();

    return ipBitmap;
}

HBITMAP CreateHBITMAP(IWICBitmapSource *ipBitmap) {
    // Get image dimensions.
    UINT width = 0;
    UINT height = 0;
    if (FAILED(ipBitmap->GetSize(&width, &height)) || width == 0 || height == 0) {
        return NULL;
    }

    // Prepare structure for bitmap information
    BITMAPINFO bitmap_info;
    memset(&bitmap_info, 0, sizeof(bitmap_info));
    bitmap_info.bmiHeader.biSize = sizeof(BITMAPINFOHEADER);
    bitmap_info.bmiHeader.biWidth = width;
    bitmap_info.bmiHeader.biHeight = -((LONG)height); // top-down DIB mode
    bitmap_info.bmiHeader.biPlanes = 1;
    bitmap_info.bmiHeader.biBitCount = 32;
    bitmap_info.bmiHeader.biCompression = BI_RGB;

    // Create the DIB section for the image
    HDC handle_screen = GetDC(NULL);
    void *image_data = NULL;
    HBITMAP handle_bmp = CreateDIBSection(handle_screen, &bitmap_info, DIB_RGB_COLORS, &image_data, NULL, 0);
    ReleaseDC(NULL, handle_screen);
    if (handle_bmp == NULL) {
        return NULL;
    }
    // Copy the image into the HBITMAP
    const UINT stride = width * 4;
    const UINT size = stride * height;
    if (FAILED(ipBitmap->CopyPixels(NULL, stride, size, (BYTE *)(image_data)))) {
        return NULL;
    }

    return handle_bmp;
}

HWND createSplashWindow(HBITMAP splash_bitmap) {
    WNDCLASSA wc = {0};
    wc.lpfnWndProc = DefWindowProc;
    wc.hCursor = LoadCursor(NULL, IDC_ARROW);
    wc.lpszClassName = "Splash";
    RegisterClassA(&wc);

    HWND splash_window = CreateWindowExA(WS_EX_LAYERED, wc.lpszClassName, NULL,
                                         WS_POPUP | WS_VISIBLE | WS_EX_TOOLWINDOW, 0, 0, 0, 0, 0, NULL, 0, NULL);
    assert(splash_window != NULL);

    // get the size of the bitmap

    BITMAP bitmap;
    GetObject(splash_bitmap, sizeof(bitmap), &bitmap);
    SIZE sizeSplash = {bitmap.bmWidth, bitmap.bmHeight};

    // Monitor selection and dimensions.
    // spell-checker: ignore HMONITOR,MONITORINFO,MONITOR_DEFAULTTOPRIMARY
    POINT zero = {0};
    HMONITOR handle_monitor = MonitorFromPoint(zero, MONITOR_DEFAULTTOPRIMARY);
    MONITORINFO monitorinfo = {0};
    monitorinfo.cbSize = sizeof(monitorinfo);
    GetMonitorInfo(handle_monitor, &monitorinfo);

    // Centered splash screen in the middle of main monitor.
    POINT ptOrigin;
    ptOrigin.x = monitorinfo.rcWork.left + (monitorinfo.rcWork.right - monitorinfo.rcWork.left - sizeSplash.cx) / 2;
    ptOrigin.y = monitorinfo.rcWork.top + (monitorinfo.rcWork.bottom - monitorinfo.rcWork.top - sizeSplash.cy) / 2;

#if _NUITKA_TRACE
    printf("Onefile: Splash screen origin %d %d for sizes %d %d\n", ptOrigin.x, ptOrigin.y, sizeSplash.cx,
           sizeSplash.cy);
#endif
    // Create a DC with splash bitmap
    HDC handle_screen = GetDC(NULL);
    HDC handle_memory = CreateCompatibleDC(handle_screen);
    HBITMAP handle_old_bitmap = (HBITMAP)SelectObject(handle_memory, splash_bitmap);

    // Set image alpha channel for blending.
    // spell-checker: ignore BLENDFUNCTION
    BLENDFUNCTION blend = {0};
    blend.BlendOp = AC_SRC_OVER;
    blend.SourceConstantAlpha = 255;
    blend.AlphaFormat = AC_SRC_ALPHA;

    // Set window for display.
    UpdateLayeredWindow(splash_window, handle_screen, &ptOrigin, &sizeSplash, handle_memory, &zero, RGB(0, 0, 0),
                        &blend, ULW_ALPHA);

    SelectObject(handle_memory, handle_old_bitmap);
    DeleteDC(handle_memory);
    ReleaseDC(NULL, handle_screen);

    return splash_window;
}

HWND splash_window = 0;
static wchar_t splash_indicator_path[4096] = {0};
bool splash_active = false;

extern "C" void initSplashScreen(void) {
    NUITKA_PRINT_TIMING("ONEFILE: Initialize splash screen.");

    CoInitialize(NULL);
    IStream *image_stream = createImageStream();
    if (unlikely(image_stream == NULL)) {
        NUITKA_PRINT_TIMING("ONEFILE: Failed to create image stream.");
        return;
    }
    IWICBitmapSource *image_source = getBitmapFromImageStream(image_stream);
    image_stream->Release();
    if (unlikely(image_source == NULL)) {
        NUITKA_PRINT_TIMING("ONEFILE: Failed to get image source from stream.");
        return;
    }
    HBITMAP splash_bitmap = CreateHBITMAP(image_source);
    image_source->Release();
    if (unlikely(splash_bitmap == NULL)) {
        NUITKA_PRINT_TIMING("ONEFILE: Failed to get bitmap.");
        return;
    }

    splash_window = createSplashWindow(splash_bitmap);

    // TODO: This probably should be user provided.
    wchar_t const *pattern = L"{TEMP}\\onefile_{PID}_splash_feedback.tmp";
    BOOL bool_res =
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

extern "C" bool checkSplashScreen(void) {
    if (splash_active) {
        NUITKA_PRINT_TIMING("ONEFILE: Check splash screen indicator file.");

        if (!PathFileExistsW(splash_indicator_path)) {
            closeSplashScreen();
            splash_active = false;
        }
    }

    return splash_active == false;
}
//     Part of "Nuitka", an optimizing Python compiler that is compatible and
//     integrates with CPython, but also works on its own.
//
//     Licensed under the Apache License, Version 2.0 (the "License");
//     you may not use this file except in compliance with the License.
//     You may obtain a copy of the License at
//
//        http://www.apache.org/licenses/LICENSE-2.0
//
//     Unless required by applicable law or agreed to in writing, software
//     distributed under the License is distributed on an "AS IS" BASIS,
//     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//     See the License for the specific language governing permissions and
//     limitations under the License.
