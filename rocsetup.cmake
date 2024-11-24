cmake_minimum_required(VERSION 3.25)

function(print_args)
  math(EXPR LAST_INDEX "${CMAKE_ARGC}-1")
  foreach(i RANGE 1 ${LAST_INDEX})
    message("Argument ${i}: ${CMAKE_ARGV${i}}")
  endforeach()
endfunction()


function(print_original_args)
  set(all_args)
  foreach(i RANGE 0 ${CMAKE_ARGC})
    set(all_args "${all_args} ${CMAKE_ARGV${i}}")
  endforeach()
  message(STATUS "ROCSETUP/I: Raw command:${all_args}")
endfunction()


function(parse_args)
  math(EXPR LAST_INDEX "${CMAKE_ARGC}-1")
  set(options -p -a -S -B)
  set(current_option "")
  foreach(i RANGE 1 ${LAST_INDEX})
    # message("Argument ${i}: ${CMAKE_ARGV${i}}")
    set(arg "${CMAKE_ARGV${i}}")
    if(${arg} IN_LIST options)
      set(current_option "${arg}")
    else()
      if(current_option STREQUAL "-p")
        set(ROCBUILD_PLATFORM "${arg}" PARENT_SCOPE)
      elseif(current_option STREQUAL "-a")
        set(ROCBUILD_ARCH "${arg}" PARENT_SCOPE)
      elseif(current_option STREQUAL "-S")
        set(ROCBUILD_SOURCE_DIR "${arg}" PARENT_SCOPE)
      elseif(current_option STREQUAL "-B")
        set(ROCBUILD_BINARY_DIR "${arg}" PARENT_SCOPE)
      endif()
      set(current_option "")
    endif()
  endforeach()
endfunction()

function(set_generator)
  if(ROCBUILD_PLATFORM STREQUAL "vs2022")
    set(ROCBUILD_GENERATOR "Visual Studio 17 2022")
  elseif(ROCBUILD_ARCH STREQUAL "vs2019")
    set(ROCBUILD_GENERATOR "Visual Studio 16 2019")
  endif()

  if(ROCBUILD_GENERATOR MATCHES "Visual Studio")
    if(ROCBUILD_ARCH MATCHES "x64")
      set(ROCBUILD_GENERATOR_EXTRA -A x64)
    elseif(ROCBUILD_ARCH MATCHES "x86")
      set(ROCBUILD_GENERATOR_EXTRA -A win32)
    endif()
  endif()
  set(ROCBUILD_GENERATOR ${ROCBUILD_GENERATOR} PARENT_SCOPE)
  set(ROCBUILD_GENERATOR_EXTRA ${ROCBUILD_GENERATOR_EXTRA} PARENT_SCOPE)
endfunction()


print_original_args()
#print_args()
parse_args()
set_generator()

set(cmake_arguments)

if(ROCBUILD_SOURCE_DIR)
  list(APPEND cmake_arguments -S ${ROCBUILD_SOURCE_DIR})
endif()

if(ROCBUILD_BINARY_DIR)
  list(APPEND cmake_arguments -B ${ROCBUILD_BINARY_DIR})
endif()

if(ROCBUILD_GENERATOR)
  list(APPEND cmake_arguments -G ${ROCBUILD_GENERATOR} ${ROCBUILD_GENERATOR_EXTRA})
endif()

if(ROCBUILD_PLATFORM)
  list(APPEND cmake_arguments -DROCBUILD_PLATFORM=${ROCBUILD_PLATFORM})
else()
  message(FATAL_ERROR "Platform not specified")
endif()

if(ROCBUILD_ARCH)
  list(APPEND cmake_arguments -DROCBUILD_ARCH=${ROCBUILD_ARCH})
else()
  message(FATAL_ERROR "Architecture not specified")
endif()

set(parsed_command "cmake ${cmake_arguments}")
string(REPLACE ";" " " parsed_command_str "${parsed_command}")
message(STATUS "ROCSETUP/I: Parsed command: ${parsed_command_str}")
execute_process(
  COMMAND cmake ${cmake_arguments}
  WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
  RESULT_VARIABLE result
  OUTPUT_VARIABLE output
  ERROR_VARIABLE error_output
)

if(result)
  message("${result}")
endif()
if(output)
  message("${output}")
endif()
if(error_output)
  message("${error_output}")
endif()

