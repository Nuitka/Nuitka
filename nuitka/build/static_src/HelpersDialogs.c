//     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file

// This file is included from another C file, help IDEs to still parse it on
// its own.
#ifdef __IDE_ONLY__
#include "nuitka/prelude.h"
#endif

#if defined(_WIN32)

// Define control IDs and custom messages
#define ID_EDIT_INPUT 101
#define ID_STATIC_PROMPT 102
#define NUITKA_INPUT_DIALOG_CLASS L"NuitkaInputDialogClass"
#define WM_USER_INTERRUPT (WM_APP + 1)

// Global handle to the dialog, so the console handler can find it.
static HWND our_input_dialog = NULL;

// spell-checker: ignore AUTOHSCROLL,WNDPROC,HMENU,GWLP_USERDATA
// spell-checker: ignore IDOK,LOWORD,WNDCLASSW,lpfnWndProc,COLOR_BTNFACE
// spell-checker: ignore lpszClassName,WS_EX_DLGMODALFRAME,GWLP_WNDPROC

// Structure to hold all necessary data for the dialog window
struct DialogState {
    HWND hDlg;
    HWND hPrompt;
    HWND hEdit;
    wchar_t *result_buffer;
    int result_buffer_size;
    BOOL success;
    WNDPROC old_edit_proc; // To store the original edit control procedure
};

// Console control handler to catch CTRL-C from the terminal.
static BOOL WINAPI ourDialogCtrlCHandler(DWORD dwCtrlType) {
    if (dwCtrlType == CTRL_C_EVENT) {
        // If our dialog is active, just post a message to it to close.
        // The main thread will handle the Python-specific parts.
        if (our_input_dialog != NULL) {
            PostMessage(our_input_dialog, WM_USER_INTERRUPT, 0, 0);
        }

        // Return TRUE to indicate that we have handled the event.
        return TRUE;
    }

    // Return FALSE for other events to allow default processing.
    return FALSE;
}

// This is a custom window procedure for the Edit control to capture the Enter key.
static LRESULT CALLBACK dialogEditSubclassProc(HWND hWnd, UINT message, WPARAM wParam, LPARAM lParam) {
    struct DialogState *state = (struct DialogState *)GetWindowLongPtrW(GetParent(hWnd), GWLP_USERDATA);

    if (message == WM_KEYDOWN && wParam == VK_RETURN) {
        // User pressed Enter. Post an OK command to the parent dialog.
        PostMessage(GetParent(hWnd), WM_COMMAND, IDOK, 0);
        return 0; // We handled the message.
    }

    // For all other messages, pass them to the original Edit control procedure.
    return CallWindowProc(state->old_edit_proc, hWnd, message, wParam, lParam);
}

// This is the window procedure that handles messages for our custom dialog.
static LRESULT CALLBACK ourDialogManualInputDialogProc(HWND hWnd, UINT message, WPARAM wParam, LPARAM lParam) {
    struct DialogState *state = (struct DialogState *)GetWindowLongPtrW(hWnd, GWLP_USERDATA);

    switch (message) {
    case WM_CREATE:
        // Store the state pointer passed from CreateWindowEx
        SetWindowLongPtrW(hWnd, GWLP_USERDATA, (LONG_PTR)((CREATESTRUCT *)lParam)->lpCreateParams);
        return 0;

    case WM_COMMAND:
        // This is triggered by the Enter key in the subclassed edit control.
        if (LOWORD(wParam) == IDOK) {
            GetWindowTextW(state->hEdit, state->result_buffer, state->result_buffer_size);
            state->success = TRUE;
            DestroyWindow(hWnd); // This will cause the message loop to exit
            return 0;
        }
        break;

    case WM_USER_INTERRUPT:
        state->success = FALSE;
        DestroyWindow(hWnd);
        return 0;

    case WM_CLOSE:
        // Treat closing the dialog ('X' button) the same as pressing Enter.
        GetWindowTextW(state->hEdit, state->result_buffer, state->result_buffer_size);
        state->success = TRUE;
        DestroyWindow(hWnd);
        return 0;

    case WM_DESTROY:
        // Signal the message loop to terminate.
        PostQuitMessage(0);
        return 0;
    }
    return DefWindowProcW(hWnd, message, wParam, lParam);
}

// Main function to create and show the input dialog.
PyObject *Nuitka_Win32_InputDialog(PyThreadState *tstate, PyObject *prompt) {
    // Convert Python prompt to wide C string
    PyObject *prompt_str = BUILTIN_UNICODE1(prompt);
    if (prompt_str == NULL) {
        return NULL;
    }

    PRINT_ITEM(prompt);
    PRINT_STRING(" (use dialog just opened, not this terminal) ");
    FLUSH_STDOUT();

    const wchar_t *prompt_text = PyUnicode_AsWideCharString(prompt_str, NULL);
    Py_DECREF(prompt_str);
    if (unlikely(prompt_text == NULL)) {
        return NULL;
    }

    // Allocate buffer for the result
    const int buffer_size = 2048;
    wchar_t *result_buffer = (wchar_t *)calloc(buffer_size, sizeof(wchar_t));
    if (result_buffer == NULL) {
        PyMem_Free((void *)prompt_text);
        return PyErr_NoMemory();
    }

    HINSTANCE hInstance = GetModuleHandle(NULL);

    // --- Register the Window Class (if not already done) ---
    WNDCLASSW wc = {0};
    wc.lpfnWndProc = ourDialogManualInputDialogProc;
    wc.hInstance = hInstance;
    wc.hCursor = LoadCursor(NULL, IDC_ARROW);
    wc.hbrBackground = (HBRUSH)(COLOR_BTNFACE + 1);
    wc.lpszClassName = NUITKA_INPUT_DIALOG_CLASS;
    RegisterClassW(&wc);

    // --- Create the Dialog Window ---
    struct DialogState state = {0};
    state.result_buffer = result_buffer;
    state.result_buffer_size = buffer_size;
    state.success = FALSE;

    int dialog_width = 250;
    int dialog_height = 100;
    RECT desktopRect;
    GetWindowRect(GetDesktopWindow(), &desktopRect);
    int x = (desktopRect.right - dialog_width) / 2;
    int y = (desktopRect.bottom - dialog_height) / 2;

    state.hDlg = CreateWindowExW(WS_EX_DLGMODALFRAME, NUITKA_INPUT_DIALOG_CLASS, L"Input Required",
                                 WS_CAPTION | WS_SYSMENU | WS_VISIBLE, x, y, dialog_width, dialog_height, NULL, NULL,
                                 hInstance, &state);

    if (state.hDlg == NULL) {
        // Handle window creation failure
        PyMem_Free((void *)prompt_text);
        free(result_buffer);

        SET_CURRENT_EXCEPTION_TYPE0_STR(tstate, PyExc_RuntimeError, "Failed to create Win32 dialog window.");
        return NULL;
    }

    // --- Setup for CTRL-C handling ---
    our_input_dialog = state.hDlg;
    SetConsoleCtrlHandler(ourDialogCtrlCHandler, TRUE);

    // --- Create Controls as Child Windows ---
    state.hPrompt = CreateWindowW(L"STATIC", prompt_text, WS_CHILD | WS_VISIBLE, 10, 10, 220, 20, state.hDlg,
                                  (HMENU)ID_STATIC_PROMPT, hInstance, NULL);
    state.hEdit = CreateWindowW(L"EDIT", L"", WS_CHILD | WS_VISIBLE | WS_BORDER | ES_AUTOHSCROLL, 10, 35, 220, 20,
                                state.hDlg, (HMENU)ID_EDIT_INPUT, hInstance, NULL);

    // --- Subclass the Edit control to capture Enter key ---
    state.old_edit_proc = (WNDPROC)SetWindowLongPtrW(state.hEdit, GWLP_WNDPROC, (LONG_PTR)dialogEditSubclassProc);
    SetFocus(state.hEdit);

    // --- Run a Modal Message Loop ---
    MSG msg;
    while (GetMessageW(&msg, NULL, 0, 0)) {
        TranslateMessage(&msg);
        DispatchMessageW(&msg);
    }

    // --- Process the Result ---
    PyObject *result_obj = NULL;
    if (state.success) {
        result_obj = PyUnicode_FromWideChar(result_buffer, wcslen(result_buffer));

        PRINT_ITEM_LINE(result_obj);
        FLUSH_STDOUT();
    } else {
        // CTRL-C happened.
        PyErr_SetNone(PyExc_KeyboardInterrupt);
        result_obj = NULL;
    }

    // Cleanup for exit.
    our_input_dialog = NULL;
    SetConsoleCtrlHandler(ourDialogCtrlCHandler, FALSE);
    UnregisterClassW(NUITKA_INPUT_DIALOG_CLASS, hInstance);

    PyMem_Free((void *)prompt_text);
    free(result_buffer);

    return result_obj;
}

#endif

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
