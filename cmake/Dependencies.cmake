include(FetchContent)

option(USE_SYSTEM_NLOHMANN_JSON "Use system-installed nlohmann_json package" OFF)

if(USE_SYSTEM_NLOHMANN_JSON)
    find_package(nlohmann_json CONFIG REQUIRED)
else()
    FetchContent_Declare(
        nlohmann_json
        GIT_REPOSITORY https://github.com/nlohmann/json.git
        GIT_TAG v3.11.3
        GIT_SHALLOW TRUE
    )
    FetchContent_MakeAvailable(nlohmann_json)
endif()
