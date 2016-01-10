

set(WinSparkle_ROOT_DIR "" CACHE PATH "WinSparkle root directory")

# Determine the project architecture.
if(NOT DEFINED PROJECT_ARCH)
  if(CMAKE_SIZEOF_VOID_P MATCHES 8)
    set(PROJECT_ARCH "x86_64")
  else()
    set(PROJECT_ARCH "x86")
  endif()
endif()

# Hints to look for libraries and runtime paths, and for runtime names
if(${PROJECT_ARCH} STREQUAL "x86_64")
    set(WinSparkle_RUNTIME_DIR "x64/Release")
elseif(${PROJECT_ARCH} STREQUAL "x86")
    set(WinSparkle_RUNTIME_DIR "Release")
else()
    message(ERROR "No PROJECT_ARCH value recognized: ${PROJECT_ARCH}")
endif()

find_path(WinSparkle_INCLUDE_DIRS
    NAMES "winsparkle.h"
    HINTS ${WinSparkle_ROOT_DIR}
    PATH_SUFFIXES 
        "include"
)

find_library(WinSparkle_LIBRARIES
    NAMES WinSparkle.lib 
    HINTS ${WinSparkle_ROOT_DIR}
    PATH_SUFFIXES
        ${WinSparkle_RUNTIME_DIR}
)

set(WinSparkle_RUNTIME_LIBRARIES "WinSparkle.dll")

