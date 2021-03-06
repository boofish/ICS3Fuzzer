/* ***************************************************************************
 * Copyright (c) 2012-2013 Google, Inc.  All rights reserved.
 * ***************************************************************************/

/*
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 * * Redistributions of source code must retain the above copyright notice,
 *   this list of conditions and the following disclaimer.
 *
 * * Redistributions in binary form must reproduce the above copyright notice,
 *   this list of conditions and the following disclaimer in the documentation
 *   and/or other materials provided with the distribution.
 *
 * * Neither the name of Google, Inc. nor the names of its contributors may be
 *   used to endorse or promote products derived from this software without
 *   specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED. IN NO EVENT SHALL GOOGLE, INC. OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
 * CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
 * LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
 * OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
 * DAMAGE.
 */

/*
DynamoRIO utility macros. Copied from the DyanmoRIO project,
http://dynamorio.org/
*/


#ifndef CLIENTS_COMMON_UTILS_H_
#define CLIENTS_COMMON_UTILS_H_

#include "dr_api.h"
#include "stdio.h"


#ifdef DEBUG
# define ASSERT(x, msg) DR_ASSERT_MSG(x, msg)
# define IF_DEBUG(x) x
#else
# define ASSERT(x, msg) /* nothing */
# define IF_DEBUG(x) /* nothing */
#endif

/* XXX: should be moved to DR API headers? */
#define BUFFER_SIZE_BYTES(buf)      sizeof(buf)
#define BUFFER_SIZE_ELEMENTS(buf)   (BUFFER_SIZE_BYTES(buf) / sizeof((buf)[0]))
#define BUFFER_LAST_ELEMENT(buf)    (buf)[BUFFER_SIZE_ELEMENTS(buf) - 1]
#define NULL_TERMINATE_BUFFER(buf)  BUFFER_LAST_ELEMENT(buf) = 0
#define ALIGNED(x, alignment) ((((ptr_uint_t)x) & ((alignment)-1)) == 0)
#define TESTANY(mask, var) (((mask) & (var)) != 0)
#define TEST  TESTANY

#ifdef WINDOWS
# define IF_WINDOWS(x) x
# define IF_UNIX_ELSE(x,y) y
#else
# define IF_WINDOWS(x)
# define IF_UNIX_ELSE(x,y) x
#endif

/* Checks for both debug and release builds: */
#define USAGE_CHECK(x, msg) DR_ASSERT_MSG(x, msg)

static inline generic_func_t
cast_to_func(void *p)
{
#ifdef WINDOWS
#  pragma warning(push)
#  pragma warning(disable : 4055)
#endif
    return (generic_func_t) p;
#ifdef WINDOWS
#  pragma warning(pop)
#endif
}

#endif /* CLIENTS_COMMON_UTILS_H_ */
file_t
log_file_open(client_id_t id, void *drcontext, const char *path, const char *name,
              uint flags);

/* close a log file opened by log_file_open */
void
log_file_close(file_t log);

/* Converts a raw file descriptor into a FILE stream. */
FILE *
log_stream_from_file(file_t f);

/* log_file_close does *not* need to be called when calling this on a
 * stream converted from a file descriptor.
 */
void
log_stream_close(FILE *f);


