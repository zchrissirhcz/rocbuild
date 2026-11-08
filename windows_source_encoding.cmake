# Author: Zhuo Zhang <imzhuo@foxmail.com>
# Homepage: https://github.com/zchrissirhcz/rocbuild
# Last update: 2025-12-10 00:34:00
cmake_minimum_required(VERSION 3.15)
include_guard()

# avoid wierd compile error and garbage console output on Windows, once you already have the best practice:
# - save source files in UTF-8 without BOM, and use .editorconfig to enforce it
# - git global configured with this on Windows: core.autocrlf=true (i.e. source code with CRLF line ending)
if(CMAKE_SYSTEM_NAME MATCHES "Windows")
  # get code page from windows registry
  if(CMAKE_VERSION VERSION_GREATER_EQUAL 3.24) # query by cmake builtin
    cmake_host_system_information(
      RESULT CodePage
      QUERY WINDOWS_REGISTRY "HKLM/SYSTEM/CurrentControlSet/Control/Nls/CodePage"
      VALUE "ACP"
    )
  else() # query from python
    find_package(Python3 COMPONENTS Interpreter REQUIRED)
    set(_python_script "
import sys
try:
    import winreg
except ImportError:
    try:
        import _winreg as winreg  # Python 2 compatible
    except ImportError:
        print('Failed to get code page', file=sys.stderr)
        sys.exit(1)

try:
    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                         r'SYSTEM\\CurrentControlSet\\Control\\Nls\\CodePage',
                         0, winreg.KEY_READ)
    value, _ = winreg.QueryValueEx(key, 'ACP')
    print(value)
except Exception as e:
    print('Failed to get code page: {}'.format(e), file=sys.stderr)
    sys.exit(1)
")
    
    # save script to file to avoid command line too long and escape issue
    set(_temp_script "${CMAKE_BINARY_DIR}/get_codepage.py")
    file(WRITE "${_temp_script}" "${_python_script}")
    
    execute_process(
      COMMAND "${Python3_EXECUTABLE}" "${_temp_script}"
      RESULT_VARIABLE _result
      OUTPUT_VARIABLE CodePage
      ERROR_VARIABLE _error
      OUTPUT_STRIP_TRAILING_WHITESPACE
    )
    
    if(NOT _result EQUAL 0)
      message(WARNING "Failed to query ACP via Python: ${_error}")
      set(CodePage "")
    endif()
  endif()
  
  if(CodePage STREQUAL "936")
    if(MSVC)
      add_compile_options("/source-charset:utf-8")
      # add_compile_options(
      #   "$<$<COMPILE_LANG_AND_ID:C,MSVC>:/source-charset:utf-8>"
      #   "$<$<COMPILE_LANG_AND_ID:CXX,MSVC>:/source-charset:utf-8>"
      # )
    elseif(MINGW)
      # please download MinGW-w64 with iconv supported
      # i.e. install MSYS2 from: https://www.msys2.org/ , then install packages via command: pacman -S mingw-w64-ucrt-x86_64-gcc
      # w64devkit(https://github.com/skeeto/w64devkit) does not support iconv currently(as of 2025.12.10, 2.5.0)
      # CLion(2025.3) bundled MinGW also does not support iconv currently(as of 2025.12.10)
      add_compile_options(
        -finput-charset=UTF-8
        -fexec-charset=GBK
      )
    endif()
  endif()
endif()