/*
 * Terminal Launcher Stub for macOS App Bundles
 *
 * This small binary is used as the CFBundleExecutable for macOS app bundles
 * that need terminal/console access (TUI applications). When launched from
 * Finder, it detects that stdout is not a TTY and relaunches itself in
 * Terminal.app. When already running in a terminal, it simply executes the
 * actual application binary.
 *
 * Part of Nuitka, the Python compiler.
 * Copyright 2025, Kay Hayen, https://nuitka.net
 * Licensed under the Apache License, Version 2.0
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <libgen.h>
#include <mach-o/dyld.h>
#include <sys/param.h>

/* Get the path to this executable */
static char *get_executable_path(void) {
    static char path[MAXPATHLEN];
    uint32_t size = sizeof(path);

    if (_NSGetExecutablePath(path, &size) != 0) {
        return NULL;
    }

    /* Resolve any symlinks to get the real path */
    char *resolved = realpath(path, NULL);
    if (resolved != NULL) {
        strncpy(path, resolved, sizeof(path) - 1);
        path[sizeof(path) - 1] = '\0';
        free(resolved);
    }

    return path;
}

/* Get the directory containing this executable */
static char *get_executable_dir(const char *exe_path) {
    static char dir[MAXPATHLEN];
    strncpy(dir, exe_path, sizeof(dir) - 1);
    dir[sizeof(dir) - 1] = '\0';
    return dirname(dir);
}

int main(int argc, char *argv[]) {
    char *exe_path = get_executable_path();
    if (exe_path == NULL) {
        fprintf(stderr, "Error: Could not determine executable path\n");
        return 1;
    }

    char *exe_dir = get_executable_dir(exe_path);
    char *exe_name = basename(exe_path);

    /* Check if stdout is connected to a terminal */
    if (!isatty(STDOUT_FILENO)) {
        /*
         * Not running in a terminal (launched from Finder/Dock).
         * Relaunch this executable in Terminal.app.
         */
        char open_cmd[MAXPATHLEN + 64];
        snprintf(open_cmd, sizeof(open_cmd), "open -a Terminal \"%s\"", exe_path);

        /* Use system() to launch Terminal with this executable */
        int result = system(open_cmd);
        return (result == 0) ? 0 : 1;
    }

    /*
     * Running in a terminal. Change to the bundle's MacOS directory
     * and execute the actual binary (which has "_bin" suffix).
     */
    if (chdir(exe_dir) != 0) {
        fprintf(stderr, "Error: Could not change to directory: %s\n", exe_dir);
        return 1;
    }

    /* Build the path to the actual binary */
    char binary_path[MAXPATHLEN];
    snprintf(binary_path, sizeof(binary_path), "./%s_bin", exe_name);

    /* Execute the actual binary, passing through all arguments */
    execv(binary_path, argv);

    /* If execv returns, it failed */
    fprintf(stderr, "Error: Could not execute: %s\n", binary_path);
    return 1;
}
