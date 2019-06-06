/*
  pygame - Python Game Library

  This library is free software; you can redistribute it and/or
  modify it under the terms of the GNU Library General Public
  License as published by the Free Software Foundation; either
  version 2 of the License, or (at your option) any later version.

  This library is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
  Library General Public License for more details.

  You should have received a copy of the GNU Library General Public
  License along with this library; if not, write to the Free
  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

*/

#include "pygame.h"
#include "doc/camera_doc.h"

#if defined(__unix__)
    #include <structmember.h>
    #include <stdio.h>
    #include <stdlib.h>
    #include <string.h>
    #include <assert.h>

    #include <fcntl.h>              /* low-level i/o */
    #include <unistd.h>
    #include <errno.h>
    #include <sys/stat.h>
    #include <sys/types.h>
    #include <sys/time.h>
    #include <sys/mman.h>
    #include <sys/ioctl.h>

    /* on freebsd there is no asm/types */
    #ifdef linux
        #include <asm/types.h>          /* for videodev2.h */
    #endif

    #include <linux/videodev2.h>
#elif defined(__APPLE__)
    #include <AvailabilityMacros.h>
    /* We support OSX 10.6 and below. */
    #if __MAC_OS_X_VERSION_MAX_ALLOWED <= 1060
        #define PYGAME_MAC_CAMERA_OLD 1
    #endif
#endif

#if defined(PYGAME_MAC_CAMERA_OLD)
        #include <QuickTime/QuickTime.h>
        #include <QuickTime/Movies.h>
        #include <QuickTime/ImageCompression.h>
#endif

/* some constants used which are not defined on non-v4l machines. */
#ifndef V4L2_PIX_FMT_RGB24
    #define V4L2_PIX_FMT_RGB24 'RGB3'
#endif
#ifndef V4L2_PIX_FMT_RGB444
    #define V4L2_PIX_FMT_RGB444 'R444'
#endif
#ifndef V4L2_PIX_FMT_YUYV
    #define V4L2_PIX_FMT_YUYV 'YUYV'
#endif

#define CLEAR(x) memset (&(x), 0, sizeof (x))
#define SAT(c) if (c & (~255)) { if (c < 0) c = 0; else c = 255; }
#define SAT2(c) ((c) & (~255) ? ((c) < 0 ? 0 : 255) : (c))
#define DEFAULT_WIDTH 640
#define DEFAULT_HEIGHT 480
#define RGB_OUT 1
#define YUV_OUT 2
#define HSV_OUT 4
#define CAM_V4L 1 /* deprecated. the incomplete support in pygame was removed */
#define CAM_V4L2 2

struct buffer {
    void * start;
    size_t length;
};

#if defined(__unix__)
typedef struct PyCameraObject {
    PyObject_HEAD
    char* device_name;
    int camera_type;
    unsigned long pixelformat;
    unsigned int color_out;
    struct buffer* buffers;
    unsigned int n_buffers;
    int width;
    int height;
    int size;
    int hflip;
    int vflip;
    int brightness;
    int fd;
} PyCameraObject;
#elif defined(PYGAME_MAC_CAMERA_OLD)
typedef struct PyCameraObject {
    PyObject_HEAD
    char* device_name;              /* unieke name of the device */
    OSType pixelformat;
    unsigned int color_out;
    SeqGrabComponent component;     /* A type used by the Sequence Grabber API */
    SGChannel channel;              /* Channel of the Sequence Grabber */
    GWorldPtr gworld;               /* Pointer to the struct that holds the data of the captured image */
    Rect boundsRect;                /* bounds of the image frame */
    long size;                      /* size of the image in our buffer to draw */
    int hflip;
    int vflip;
    short depth;
    struct buffer pixels;
    //struct buffer tmp_pixels        /* place where the flipped image in temporarly stored if hflip or vflip is true.*/
} PyCameraObject;

#else
/* generic definition.
*/

typedef struct PyCameraObject {
    PyObject_HEAD
    char* device_name;
    int camera_type;
    unsigned long pixelformat;
    unsigned int color_out;
    struct buffer* buffers;
    unsigned int n_buffers;
    int width;
    int height;
    int size;
    int hflip;
    int vflip;
    int brightness;
    int fd;
} PyCameraObject;
#endif

/* internal functions for colorspace conversion */
void colorspace (SDL_Surface *src, SDL_Surface *dst, int cspace);
void rgb24_to_rgb (const void* src, void* dst, int length, SDL_PixelFormat* format);
void rgb444_to_rgb (const void* src, void* dst, int length, SDL_PixelFormat* format);
void rgb_to_yuv (const void* src, void* dst, int length,
                 unsigned long source, SDL_PixelFormat* format);
void rgb_to_hsv (const void* src, void* dst, int length,
                 unsigned long source, SDL_PixelFormat* format);
void yuyv_to_rgb (const void* src, void* dst, int length, SDL_PixelFormat* format);
void yuyv_to_yuv (const void* src, void* dst, int length, SDL_PixelFormat* format);
void uyvy_to_rgb (const void* src, void* dst, int length, SDL_PixelFormat* format);
void uyvy_to_yuv (const void* src, void* dst, int length, SDL_PixelFormat* format);
void sbggr8_to_rgb (const void* src, void* dst, int width, int height,
                    SDL_PixelFormat* format);
void yuv420_to_rgb (const void* src, void* dst, int width, int height,
                    SDL_PixelFormat* format);
void yuv420_to_yuv (const void* src, void* dst, int width, int height,
                    SDL_PixelFormat* format);

#if defined(__unix__)
/* internal functions specific to v4l2 */
char** v4l2_list_cameras (int* num_devices);
int v4l2_get_control (int fd, int id, int *value);
int v4l2_set_control (int fd, int id, int value);
PyObject* v4l2_read_raw (PyCameraObject* self);
int v4l2_xioctl (int fd, int request, void *arg);
int v4l2_process_image (PyCameraObject* self, const void *image,
                               unsigned int buffer_size, SDL_Surface* surf);
int v4l2_query_buffer (PyCameraObject* self);
int v4l2_read_frame (PyCameraObject* self, SDL_Surface* surf);
int v4l2_stop_capturing (PyCameraObject* self);
int v4l2_start_capturing (PyCameraObject* self);
int v4l2_uninit_device (PyCameraObject* self);
int v4l2_init_mmap (PyCameraObject* self);
int v4l2_init_device (PyCameraObject* self);
int v4l2_close_device (PyCameraObject* self);
int v4l2_open_device (PyCameraObject* self);

#elif defined(PYGAME_MAC_CAMERA_OLD)
/* internal functions specific to mac */
char** mac_list_cameras(int* num_devices);
int mac_open_device (PyCameraObject* self);
int mac_init_device(PyCameraObject* self);
int mac_close_device (PyCameraObject* self);
int mac_start_capturing(PyCameraObject* self);
int mac_stop_capturing (PyCameraObject* self);

int mac_get_control(PyCameraObject* self, int id, int* value);
int mac_set_control(PyCameraObject* self, int id, int value);

PyObject* mac_read_raw(PyCameraObject *self);
int mac_read_frame(PyCameraObject* self, SDL_Surface* surf);
int mac_camera_idle(PyCameraObject* self);
int mac_copy_gworld_to_surface(PyCameraObject* self, SDL_Surface* surf);

void flip_image(const void* image, void* flipped_image, int width, int height,
                short depth, int hflip, int vflip);

#endif
