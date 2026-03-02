#pragma once

#include <filesystem>
#include <string>
#include <string_view>

namespace evaluator {

struct EvalInput {
    std::string run_id;
    std::string candidate_id;
    std::string function_name;
    double x;
    double y;
};

bool read_eval_input(const std::filesystem::path& input_path, EvalInput& out, std::string& error) noexcept;
bool write_success_output(const std::filesystem::path& output_path, double value, std::string& error) noexcept;
bool write_failure_output(const std::filesystem::path& output_path, std::string_view message, std::string& error) noexcept;

}  // namespace evaluator
