#ifndef _APIENVIR_H_
#define _APIENVIR_H_

#if defined(_MSC_VER) && !defined(WINDOWS)
#define WINDOWS
#endif

#if defined(WINDOWS)
#include "Win32Interface.hpp"
#endif

#if defined(macintosh)
#include <CoreServices/CoreServices.h>
#endif

#if !defined(ACExtension)
#define ACExtension
#endif

#endif
