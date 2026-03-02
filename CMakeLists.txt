cmake_minimum_required(VERSION 3.20)

project(2d-function-evaluator VERSION 0.1.0 LANGUAGES CXX)

include(CTest)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

include(cmake/Dependencies.cmake)

# ---- Core library (shared by the executable and tests) ----
add_library(${PROJECT_NAME}_lib
    src/functions.cpp
    src/io.cpp
)

target_include_directories(${PROJECT_NAME}_lib
    PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}/src
)

target_link_libraries(${PROJECT_NAME}_lib
    PUBLIC
        nlohmann_json::nlohmann_json
)

if(MSVC)
    target_compile_options(${PROJECT_NAME}_lib PRIVATE /W4)
else()
    target_compile_options(${PROJECT_NAME}_lib
        PRIVATE
            -Wall
            -Wextra
            -Wpedantic
            $<$<CONFIG:Release>:-O3>
    )
endif()

# ---- Executable (GOW external evaluator entry point) ----
add_executable(${PROJECT_NAME}
    src/main.cpp
)

target_link_libraries(${PROJECT_NAME}
    PRIVATE
        ${PROJECT_NAME}_lib
)

# ------------------------------------------------------------
# Copy executable to repository-level bin/ directory
#
# Rationale:
# - Avoid requiring "install" (admin privileges on Windows).
# - Provide a stable, predictable path for GOW integration:
#     <repo>/bin/<exe>
# ------------------------------------------------------------
set(REPO_BIN_DIR "${CMAKE_SOURCE_DIR}/bin")

add_custom_command(
    TARGET ${PROJECT_NAME}
    POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E make_directory "${REPO_BIN_DIR}"
    COMMAND ${CMAKE_COMMAND} -E copy_if_different
            "$<TARGET_FILE:${PROJECT_NAME}>"
            "${REPO_BIN_DIR}/$<TARGET_FILE_NAME:${PROJECT_NAME}>"
    COMMENT "Copying ${PROJECT_NAME} to ${REPO_BIN_DIR}"
)

# ---- Build-type guidance for single-config generators (Ninja/Makefiles) ----
if(NOT CMAKE_CONFIGURATION_TYPES AND NOT CMAKE_BUILD_TYPE)
    message(STATUS "No build type selected. For speed, configure with -DCMAKE_BUILD_TYPE=Release.")
elseif(NOT CMAKE_CONFIGURATION_TYPES AND NOT CMAKE_BUILD_TYPE MATCHES "^[Rr]elease$")
    message(WARNING "Non-Release build selected. Use -DCMAKE_BUILD_TYPE=Release for best performance.")
endif()

# Keep install rules for users who want a traditional install, but it is optional.
install(TARGETS ${PROJECT_NAME} RUNTIME DESTINATION bin)

if(BUILD_TESTING)
    add_subdirectory(tests)
endif()