# Author: Zhuo Zhang <imzhuo@foxmail.com>
# Homepage: https://github.com/zchrissirhcz/rocbuild
# Last update: 2025-08-31 09:43:00
cmake_minimum_required(VERSION 3.15)
include_guard()

option(VS2022_ASAN_DISABLE_VECTOR_ANNOTATION "Disable string annotation for VS2022 ASan?" ON)
option(VS2022_ASAN_DISABLE_STRING_ANNOTATION "Disable vector annotation for VS2022 ASan?" ON)
option(COPY_ASAN_DLLS "Copy ASan DLLs to binary directory?" OFF)

# globally
# https://stackoverflow.com/a/65019152/2999096
# https://docs.microsoft.com/en-us/cpp/build/cmake-presets-vs?view=msvc-170#enable-addresssanitizer-for-windows-and-linux
set(ASAN_AVAILABLE ON)
if((CMAKE_C_COMPILER_ID STREQUAL "MSVC") OR (CMAKE_CXX_COMPILER_ID STREQUAL "MSVC"))
  if((CMAKE_C_COMPILER_VERSION STRLESS 16.0) OR (CMAKE_CXX_COMPILER_VERSION STRLESS 16.0))
    message(FATAL_ERROR "ASAN is available since VS2019, please use higher version of VS")
    set(ASAN_AVAILABLE OFF)
  elseif( ((CMAKE_C_COMPILER_VERSION STRGREATER_EQUAL 16.0) AND (CMAKE_C_COMPILER_VERSION STRLESS 16.7))
    OR ((CMAKE_CXX_COMPILER_VERSION STRGREATER_EQUAL 16.0) AND (CMAKE_CXX_COMPILER_VERSION STRLESS 16.7)) )
    # https://devblogs.microsoft.com/cppblog/asan-for-windows-x64-and-debug-build-support/
    message(FATAL_ERROR "VS2019 x64 ASAN requires VS >= 16.7, please update VS")
    set(ASAN_AVAILABLE OFF)
  else()
    set(ASAN_OPTIONS /fsanitize=address /Zi)
  endif()
elseif(MSVC AND ((CMAKE_C_COMPILER_ID STREQUAL "Clang") OR (CMAKE_CXX_COMPILER_ID STREQUAL "Clang")))
  message(WARNING "Clang-CL not support setup AddressSanitizer via CMakeLists.txt")
  set(ASAN_AVAILABLE OFF)
elseif((CMAKE_C_COMPILER_ID MATCHES "GNU") OR (CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
  OR (CMAKE_C_COMPILER_ID MATCHES "Clang") OR (CMAKE_CXX_COMPILER_ID MATCHES "Clang"))
  if($ENV{QNX_TARGET} MATCHES "qnx7$")
    set(ASAN_AVAILABLE OFF)
    message(WARNING "QNX SDP 7.1 does not support ASAN")
  else()
    set(ASAN_OPTIONS -fsanitize=address -fno-omit-frame-pointer -g)
  endif()
else()
  message(STATUS "Unknown compiler: ${CMAKE_C_COMPILER_ID} ${CMAKE_CXX_COMPILER_ID}")
  set(ASAN_AVAILABLE OFF)
endif()

if(ASAN_AVAILABLE)
  message(STATUS ">>> USE_ASAN: YES")
  add_compile_options(${ASAN_OPTIONS})
  if((CMAKE_SYSTEM_NAME MATCHES "Windows") AND ((CMAKE_C_COMPILER_ID STREQUAL "MSVC") OR (CMAKE_CXX_COMPILER_ID STREQUAL "MSVC")))
    add_link_options(/ignore:4300) # /INCREMENTAL
    add_link_options(/DEBUG) # LNK4302

    if(CMAKE_CXX_COMPILER_VERSION STRGREATER_EQUAL 17.2)
      if(VS2022_ASAN_DISABLE_VECTOR_ANNOTATION)
        # https://learn.microsoft.com/en-us/cpp/sanitizers/error-container-overflow?view=msvc-170
        add_compile_definitions(_DISABLE_VECTOR_ANNOTATION)
        message(STATUS ">>> VS2022_ASAN_DISABLE_VECTOR_ANNOTATION: YES")
      else()
        message(STATUS ">>> VS2022_ASAN_DISABLE_VECTOR_ANNOTATION: NO")
      endif()
    endif()

    if(CMAKE_CXX_COMPILER_VERSION STRGREATER_EQUAL 17.6)
      if(VS2022_ASAN_DISABLE_STRING_ANNOTATION)
        # https://learn.microsoft.com/en-us/cpp/sanitizers/error-container-overflow?view=msvc-170
        add_compile_definitions(_DISABLE_STRING_ANNOTATION)
        message(STATUS ">>> VS2022_ASAN_DISABLE_STRING_ANNOTATION: YES")
      else()
        message(STATUS ">>> VS2022_ASAN_DISABLE_STRING_ANNOTATION: NO")
      endif()
    endif()

    # https://devblogs.microsoft.com/cppblog/msvc-address-sanitizer-one-dll-for-all-runtime-configurations/
    if((CMAKE_C_COMPILER_VERSION STRGREATER_EQUAL 17.7) OR (CMAKE_CXX_COMPILER_VERSION STRGREATER_EQUAL 17.7))
      if((CMAKE_GENERATOR MATCHES "Visual Studio") AND (CMAKE_VERSION VERSION_GREATER_EQUAL "3.27")) # for running/debugging in Visual Studio
        if(CMAKE_GENERATOR_PLATFORM MATCHES "x64")
          set(CMAKE_VS_DEBUGGER_ENVIRONMENT "PATH=$(VC_ExecutablePath_x64);%PATH%\nASAN_SYMBOLIZER_PATH=$(VC_ExecutablePath_x64)")
        elseif(CMAKE_GENERATOR_PLATFORM MATCHES "Win32")
          set(CMAKE_VS_DEBUGGER_ENVIRONMENT "PATH=$(VC_ExecutablePath_x86);%PATH%\nASAN_SYMBOLIZER_PATH=$(VC_ExecutablePath_x86)")
        endif()
      endif()

      if((CMAKE_GENERATOR MATCHES "Ninja") OR COPY_ASAN_DLLS OR
          ((CMAKE_GENERATOR MATCHES "Visual Studio") AND (CMAKE_VERSION VERSION_LESS "3.27")) )
        get_filename_component(COMPILER_DIR ${CMAKE_CXX_COMPILER} DIRECTORY)
        file(GLOB ASAN_DLLS "${COMPILER_DIR}/clang_rt.asan_dynamic*.dll")
        foreach(ASAN_DLL ${ASAN_DLLS})
          if(DEFINED CMAKE_CONFIGURATION_TYPES)
            foreach(CONFIG_TYPE ${CMAKE_CONFIGURATION_TYPES})
              file(COPY "${ASAN_DLL}" DESTINATION ${CMAKE_BINARY_DIR}/${CONFIG_TYPE})
            endforeach()
          else()
            file(COPY "${ASAN_DLL}" DESTINATION ${CMAKE_BINARY_DIR})
          endif()
        endforeach()
        unset(COMPILER_DIR)
        unset(ASAN_DLLS)
      endif()
    endif()

  else()
    add_link_options(${ASAN_OPTIONS})
  endif()
else()
  message(STATUS ">>> USE_ASAN: NO")
endif()


# per-target
# https://developer.android.com/ndk/guides/asan?hl=zh-cn#cmake
# target_compile_options(${TARGET} PUBLIC -fsanitize=address -fno-omit-frame-pointer -g)
# set_target_properties(${TARGET} PROPERTIES LINK_FLAGS -fsanitize=address) # for non-INTERFACE targets
# target_link_options(${TARGET} INTERFACE -fsanitize=address) # for INTERFACE targets
