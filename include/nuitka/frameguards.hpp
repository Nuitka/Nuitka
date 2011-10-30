//
//     Copyright 2011, Kay Hayen, mailto:kayhayen@gmx.de
//
//     Part of "Nuitka", an optimizing Python compiler that is compatible and
//     integrates with CPython, but also works on its own.
//
//     If you submit Kay Hayen patches to this software in either form, you
//     automatically grant him a copyright assignment to the code, or in the
//     alternative a BSD license to the code, should your jurisdiction prevent
//     this. Obviously it won't affect code that comes to him indirectly or
//     code you don't submit to him.
//
//     This is to reserve my ability to re-license the code at any time, e.g.
//     the PSF. With this version of Nuitka, using it for Closed Source will
//     not be allowed.
//
//     This program is free software: you can redistribute it and/or modify
//     it under the terms of the GNU General Public License as published by
//     the Free Software Foundation, version 3 of the License.
//
//     This program is distributed in the hope that it will be useful,
//     but WITHOUT ANY WARRANTY; without even the implied warranty of
//     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
//     GNU General Public License for more details.
//
//     You should have received a copy of the GNU General Public License
//     along with this program.  If not, see <http://www.gnu.org/licenses/>.
//
//     Please leave the whole of this copyright notice intact.
//
#ifndef __NUITKA_FRAMEGUARDS_H__
#define __NUITKA_FRAMEGUARDS_H__

inline static void assertCodeObject( PyCodeObject *code_object )
{
    assertObject( (PyObject *)code_object );
}


inline static void assertFrameObject( PyFrameObject *frame_object )
{
    assertObject( (PyObject *)frame_object );

    assertCodeObject( frame_object->f_code );
}

NUITKA_MAY_BE_UNUSED static PyFrameObject *INCREASE_REFCOUNT( PyFrameObject *frame_object )
{
    assertFrameObject( frame_object );

    Py_INCREF( frame_object );
    return frame_object;
}

class FrameGuard
{
public:
    FrameGuard( PyFrameObject *frame_object )
    {
        assertFrameObject( frame_object );

        // Remember it.
        this->frame_object = frame_object;

        // Look at current frame.
        PyFrameObject *old = PyThreadState_GET()->frame;

        // No recursion allowed of course, assert against it.
        assert( old != frame_object );

        // Push the new frame as the currently active one.
        PyThreadState_GET()->frame = frame_object;

        if ( frame_object->f_back != old )
        {
            if ( frame_object->f_back )
            {
                assertFrameObject( frame_object->f_back );
            }

            Py_XDECREF( frame_object->f_back );

            assertFrameObject( old );

            Py_INCREF( old );
            frame_object->f_back = old;
        }

        // Keep the frame object alive for this C++ objects live time.
        Py_INCREF( frame_object );
    }

    ~FrameGuard()
    {
        // Our frame should be on top.
        assert( PyThreadState_GET()->frame == this->frame_object );

        // Put the next frame on top instead.
        PyThreadState_GET()->frame = this->frame_object->f_back;

        // If it exists, detach our frame from it.
        if ( this->frame_object->f_back )
        {
            assertFrameObject( this->frame_object->f_back );
            Py_CLEAR( this->frame_object->f_back );
        }

        // Should still be good.
        assertFrameObject( this->frame_object );

        // Now release out frame object reference.
        Py_DECREF( this->frame_object );
    }

    PyFrameObject *getFrame() const
    {
        return INCREASE_REFCOUNT( this->frame_object );
    }

    PyFrameObject *getFrame0() const
    {
        assertFrameObject( this->frame_object );

        return this->frame_object;
    }

private:
    PyFrameObject *frame_object;
};

#endif
