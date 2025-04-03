building on MinGW

navigate to the parent directory of a project (contains lib and src folders)

run

`cmake -G "MinGW Makefiles" -S . -B build`

`cmake --build ./build`