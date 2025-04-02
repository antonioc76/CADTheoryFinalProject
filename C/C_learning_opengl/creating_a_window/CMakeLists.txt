cmake_minimum_required(VERSION 3.8)

project("Creating_A_Window")

add_subdirectory(lib/glfw)

add_subdirectory(lib/glad)

add_executable(hellogl src/hellogl.c)

target_link_libraries(hellogl glfw glad)

target_include_directories(hellogl PUBLIC "lib/glfw/include", PUBLIC "lib/glad/include") 