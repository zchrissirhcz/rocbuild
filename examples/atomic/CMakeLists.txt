cmake_minimum_required(VERSION 3.20)
project(atomic_demo)

add_executable(${PROJECT_NAME} demo.cpp)

target_link_libraries(${PROJECT_NAME}
  PRIVATE
    $<$<IN_LIST:$<CXX_COMPILER_ID>,GNU;Clang>:atomic>
)
