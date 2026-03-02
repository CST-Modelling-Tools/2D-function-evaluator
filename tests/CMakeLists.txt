add_executable(test_basic test_basic.cpp)

target_link_libraries(test_basic
    PRIVATE
        nlohmann_json::nlohmann_json
)

if(MSVC)
    target_compile_options(test_basic PRIVATE /W4)
else()
    target_compile_options(test_basic PRIVATE -Wall -Wextra -Wpedantic)
endif()

add_test(
    NAME basic_contract_test
    COMMAND test_basic $<TARGET_FILE:2d-function-evaluator>
)
