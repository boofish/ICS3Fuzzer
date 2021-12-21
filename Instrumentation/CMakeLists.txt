cmake_minimum_required(VERSION 2.6)

if (${USE_COLOR})
    add_definitions(-DUSE_COLOR)
endif()

if (${USE_DRSYMS})
    add_definitions(-DUSE_DRSYMS)
endif()

if (${INTELPT})
    add_definitions(-DINTELPT)
endif()

set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)

project(shm_monitor)
add_executable(shm_monitor feedback.c hash.h)

if (NOT "${DynamoRIO_DIR}" STREQUAL "")

  project(monitor)

  set(DynamoRIO_LOG_COMPATIBILITY on)

  find_package(DynamoRIO)
  if (NOT DynamoRIO_FOUND)
    message(FATAL_ERROR "DynamoRIO package required to build")
  endif(NOT DynamoRIO_FOUND)

  if (STATIC_LIBRARY)
    set(libtype STATIC)
  else()
    set(libtype SHARED)
  endif ()

  add_library(monitor ${libtype}
    monitor_gx.c
    modules.c
    utils.c
    hash.h
    )
  configure_DynamoRIO_client(monitor)
  use_DynamoRIO_extension(monitor drmgr)
  use_DynamoRIO_extension(monitor drx)
  use_DynamoRIO_extension(monitor drcontainers)
  use_DynamoRIO_extension(monitor drreg)
  use_DynamoRIO_extension(monitor drwrap)
  if (${USE_DRSYMS})
    use_DynamoRIO_extension(monitor drsyms)
  endif()

  # VS2015 Fix
  if (NOT (MSVC_VERSION LESS 1900))
    target_link_libraries(monitor "libucrt.lib")
    target_link_libraries(monitor "libvcruntime.lib")
    target_link_libraries(monitor "Ws2_32.lib")
  endif()

endif()