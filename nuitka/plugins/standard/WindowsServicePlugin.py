#     Copyright 2020, Kay Hayen, mailto:kay.hayen@gmail.com
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
#
""" Standard plug-in to make a binary work as a Windows service.

This produces a binary that has an "install" argument or could be
registered manually as a service.
"""

from nuitka.plugins.PluginBase import NuitkaPluginBase


class NuitkaPluginWindowsService(NuitkaPluginBase):
    """ This is to make a binary work as a Windows service.

    """

    plugin_name = "windows-service"

    def __init__(self, windows_service_name):
        self.windows_service_name = windows_service_name

    @classmethod
    def addPluginCommandLineOptions(cls, group):
        group.add_option(
            "--windows-service-name",
            action="store",
            dest="windows_service_name",
            default=None,
            help="""[REQUIRED] The Windows service name.""",
        )

    @staticmethod
    def getExtraLinkLibraries():
        return "advapi32"

    @staticmethod
    def getPreprocessorSymbols():
        return {"_NUITKA_PLUGIN_WINDOWS_SERVICE_ENABLED": "1"}

    def getExtraCodeFiles(self):
        return {
            "WindowsService.c": extra_code
            % {"windows_service_name": self.windows_service_name}
        }


extra_code = r"""
#include <windows.h>
#include <tchar.h>
#include <strsafe.h>

#define SVCNAME L"%(windows_service_name)s"

#define SVC_ERROR                        ((DWORD)0xC0020001L)

SERVICE_STATUS          gSvcStatus;
SERVICE_STATUS_HANDLE   gSvcStatusHandle;
HANDLE                  ghSvcStopEvent = NULL;

void WINAPI SvcCtrlHandler(DWORD);
void WINAPI SvcMain(DWORD, LPTSTR *);

static void ReportSvcStatus(DWORD, DWORD, DWORD);
static void SvcInit();
static void SvcReportEvent(LPTSTR);


// Purpose:
//   Entry point for the process
//
// Parameters:
//   None
//
// Return value:
//   None
//
void SvcLaunchService() {
    // TO_DO: Add any additional services for the process to this table.
    SERVICE_TABLE_ENTRYW DispatchTable[] =
    {
        { SVCNAME, (LPSERVICE_MAIN_FUNCTIONW)SvcMain },
        { NULL, NULL }
    };

    // This call returns when the service has stopped.
    // The process should simply terminate when the call returns.

    if (!StartServiceCtrlDispatcherW(DispatchTable)) {
        SvcReportEvent(TEXT("StartServiceCtrlDispatcher"));
    }
}

// Install the service binary.
void SvcInstall() {
    SC_HANDLE schSCManager;
    SC_HANDLE schService;
    wchar_t szPath[MAX_PATH];

    if( !GetModuleFileNameW(NULL, szPath, MAX_PATH)) {
        printf("Cannot install service (%%d)\n", GetLastError());
        abort();
    }

    // Get a handle to the SCM database.

    schSCManager = OpenSCManager(
        NULL,                    // local computer
        NULL,                    // ServicesActive database
        SC_MANAGER_ALL_ACCESS);  // full access rights

    if (NULL == schSCManager) {
        printf("OpenSCManager failed (%%d)\n", GetLastError());
        abort();
    }

    // Create the service

    schService = CreateServiceW(
        schSCManager,              // SCM database
        SVCNAME,                   // name of service
        SVCNAME,                   // service name to display
        SERVICE_ALL_ACCESS,        // desired access
        SERVICE_WIN32_OWN_PROCESS, // service type
        SERVICE_DEMAND_START,      // start type
        SERVICE_ERROR_NORMAL,      // error control type
        szPath,                    // path to service's binary
        NULL,                      // no load ordering group
        NULL,                      // no tag identifier
        NULL,                      // no dependencies
        NULL,                      // LocalSystem account
        NULL);                     // no password

    if (schService == NULL) {
        printf("CreateService failed (%%d)\n", GetLastError());
        CloseServiceHandle(schSCManager);
        abort();
    } else {
        printf("Service installed successfully\n");
    }

    CloseServiceHandle(schService);
    CloseServiceHandle(schSCManager);

    exit(0);
}

//
// Purpose:
//   Entry point for the service
//
// Parameters:
//   dwArgc - Number of arguments in the lpszArgv array
//   lpszArgv - Array of strings. The first string is the name of
//     the service and subsequent strings are passed by the process
//     that called the StartService function to start the service.
//
// Return value:
//   None.
//
void WINAPI SvcMain(DWORD dwArgc, LPTSTR *lpszArgv) {
    // Register the handler function for the service

    gSvcStatusHandle = RegisterServiceCtrlHandlerW(
        SVCNAME,
        SvcCtrlHandler
    );

    if( !gSvcStatusHandle ) {
        SvcReportEvent(TEXT("RegisterServiceCtrlHandler"));
        return;
    }

    // These SERVICE_STATUS members remain as set here
    gSvcStatus.dwServiceType = SERVICE_WIN32_OWN_PROCESS;
    gSvcStatus.dwServiceSpecificExitCode = 0;

    // Report initial status to the SCM
    ReportSvcStatus(SERVICE_START_PENDING, NO_ERROR, 3000);

    // Perform service-specific initialization and work.
    SvcInit();
}

extern DWORD WINAPI SvcStartPython(LPVOID lpParam);

static void SvcInit() {
    // Pre-create stop event.
    ghSvcStopEvent = CreateEvent(
        NULL,    // default security attributes
        TRUE,    // manual reset event
        FALSE,   // not signaled
        NULL     // no name
    );

    if (ghSvcStopEvent == NULL) {
        ReportSvcStatus(SERVICE_STOPPED, NO_ERROR, 0);
        return;
    }

    // Report running status when initialization is complete.
    ReportSvcStatus(SERVICE_RUNNING, NO_ERROR, 0);

    HANDLE python_thread = CreateThread(
        NULL,
        0,
        SvcStartPython,
        NULL,
        0,
        NULL
    );

    // Perform work until service stops.
    // Check whether to stop the service.
    WaitForSingleObject(ghSvcStopEvent, INFINITE);

    ReportSvcStatus(SERVICE_STOPPED, NO_ERROR, 0);

    TerminateThread(python_thread, 0);
}


// Purpose:
//   Sets the current service status and reports it to the SCM.
//
// Parameters:
//   dwCurrentState - The current state (see SERVICE_STATUS)
//   dwWin32ExitCode - The system error code
//   dwWaitHint - Estimated time for pending operation,
//     in milliseconds
//
// Return value:
//   None
//
static void ReportSvcStatus(DWORD dwCurrentState, DWORD dwWin32ExitCode, DWORD dwWaitHint) {
    static DWORD dwCheckPoint = 1;

    // Fill in the SERVICE_STATUS structure.
    gSvcStatus.dwCurrentState = dwCurrentState;
    gSvcStatus.dwWin32ExitCode = dwWin32ExitCode;
    gSvcStatus.dwWaitHint = dwWaitHint;

    if (dwCurrentState == SERVICE_START_PENDING) {
        gSvcStatus.dwControlsAccepted = 0;
    } else {
        gSvcStatus.dwControlsAccepted = SERVICE_ACCEPT_STOP;
    }

    if ((dwCurrentState == SERVICE_RUNNING) || (dwCurrentState == SERVICE_STOPPED)) {
        gSvcStatus.dwCheckPoint = 0;
    } else {
        gSvcStatus.dwCheckPoint = dwCheckPoint++;
    }

    // Report the status of the service to the SCM.
    SetServiceStatus(gSvcStatusHandle, &gSvcStatus);
}

// Purpose:
//   Called by SCM whenever a control code is sent to the service
//   using the ControlService function.
//
// Parameters:
//   dwCtrl - control code
//
// Return value:
//   None
//
void WINAPI SvcCtrlHandler(DWORD dwCtrl) {
   // Handle the requested control code.

   switch(dwCtrl) {
      case SERVICE_CONTROL_STOP:
         ReportSvcStatus(SERVICE_STOP_PENDING, NO_ERROR, 0);

         // Signal the service to stop.

         SetEvent(ghSvcStopEvent);
         ReportSvcStatus(gSvcStatus.dwCurrentState, NO_ERROR, 0);

         return;

      case SERVICE_CONTROL_INTERROGATE:
         break;

      default:
         break;
   }
}


// Purpose:
//   Logs messages to the event log
//
// Parameters:
//   szFunction - name of function that failed
//
// Return value:
//   None
//
// Remarks:
//   The service must have an entry in the Application event log.
//
static void SvcReportEvent(LPTSTR szFunction) {
    HANDLE hEventSource;
    LPCWSTR outputs[2];

    wchar_t buffer[80] = L"TODO: Proper reporting";

    hEventSource = RegisterEventSourceW(NULL, SVCNAME);

    if (NULL != hEventSource) {
        // TODO: Change this to work with wchar_t:
        // StringCchPrintf(buffer, 80, TEXT("%%s failed with %%d"), szFunction, GetLastError());

        outputs[0] = SVCNAME;
        outputs[1] = buffer;

        ReportEventW(hEventSource,        // event log handle
                     EVENTLOG_ERROR_TYPE, // event type
                     0,                   // event category
                     SVC_ERROR,           // event identifier
                     NULL,                // no security identifier
                     2,                   // size of lpszStrings array
                     0,                   // no binary data
                     outputs,             // array of strings
                     NULL);               // no binary data

        DeregisterEventSource(hEventSource);
    }
}
"""
