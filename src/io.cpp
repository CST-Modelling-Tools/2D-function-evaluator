#include "io.hpp"

#include <cmath>
#include <fstream>
#include <string>

#include <nlohmann/json.hpp>

namespace evaluator {

namespace {

using json = nlohmann::json;

bool write_json_file(const std::filesystem::path& path, const json& payload, std::string& error) noexcept {
    std::ofstream out(path, std::ios::binary | std::ios::trunc);
    if (!out) {
        error = "unable to open output file: " + path.string();
        return false;
    }
    out << payload.dump(2) << '\n';
    if (!out.good()) {
        error = "failed while writing output file: " + path.string();
        return false;
    }
    return true;
}

}  // namespace

bool read_eval_input(const std::filesystem::path& input_path, EvalInput& out, std::string& error) noexcept {
    std::ifstream in(input_path, std::ios::binary);
    if (!in) {
        error = "unable to open input file: " + input_path.string();
        return false;
    }

    json root = json::parse(in, nullptr, false);
    if (root.is_discarded()) {
        error = "input JSON is invalid";
        return false;
    }
    if (!root.is_object()) {
        error = "input JSON root must be an object";
        return false;
    }

    const auto run_it = root.find("run_id");
    if (run_it == root.end() || !run_it->is_string()) {
        error = "missing or invalid field: run_id (string required)";
        return false;
    }

    const auto candidate_it = root.find("candidate_id");
    if (candidate_it == root.end() || !candidate_it->is_string()) {
        error = "missing or invalid field: candidate_id (string required)";
        return false;
    }

    const auto params_it = root.find("params");
    if (params_it == root.end() || !params_it->is_object()) {
        error = "missing or invalid field: params (object required)";
        return false;
    }
    const json& params = *params_it;

    const auto x_it = params.find("x");
    if (x_it == params.end() || !x_it->is_number()) {
        error = "missing or invalid field: params.x (number required)";
        return false;
    }

    const auto y_it = params.find("y");
    if (y_it == params.end() || !y_it->is_number()) {
        error = "missing or invalid field: params.y (number required)";
        return false;
    }

    std::string function_name = "sphere";
    const auto fn_it = params.find("function");
    if (fn_it != params.end()) {
        if (!fn_it->is_string()) {
            error = "invalid field: params.function (string required)";
            return false;
        }
        function_name = fn_it->get<std::string>();
    }

    if (const auto context_it = root.find("context"); context_it != root.end() && !context_it->is_object()) {
        error = "invalid field: context (object required when provided)";
        return false;
    }

    const double x = x_it->get<double>();
    const double y = y_it->get<double>();
    if (!std::isfinite(x) || !std::isfinite(y)) {
        error = "params.x and params.y must be finite numbers";
        return false;
    }

    out.run_id = run_it->get<std::string>();
    out.candidate_id = candidate_it->get<std::string>();
    out.function_name = std::move(function_name);
    out.x = x;
    out.y = y;

    return true;
}

bool write_success_output(const std::filesystem::path& output_path, double value, std::string& error) noexcept {
    json payload;
    payload["status"] = "ok";
    payload["metrics"] = json::object({{"f", value}});
    payload["objective"] = value;
    return write_json_file(output_path, payload, error);
}

bool write_failure_output(const std::filesystem::path& output_path, std::string_view message, std::string& error) noexcept {
    json payload;
    payload["status"] = "failed";
    payload["metrics"] = json::object();
    payload["objective"] = nullptr;
    payload["error"] = message;
    return write_json_file(output_path, payload, error);
}

}  // namespace evaluator
