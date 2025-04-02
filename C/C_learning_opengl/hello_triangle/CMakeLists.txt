CMAKE_MINIMUM_REQUIRED(VERSION 3.0)

project("hello_triangle")

add_subdirectory(lib/glad)

add_subdirectory(lib/glfw)

add_executable(hitri src/hello_triangle.c)

add_executable(example src/example_code.c)

target_link_libraries(hitri glad glfw)

target_include_directories(hitri PUBLIC "lib/glad/include" PUBLIC "lib/glfw/include")

target_link_libraries(example glad glfw)

target_include_directories(example PUBLIC "lib/glad/include" PUBLIC "lib/glfw/include")
