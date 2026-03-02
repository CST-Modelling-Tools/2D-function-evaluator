#include "functions.hpp"
#include "io.hpp"

#include <filesystem>
#include <iostream>
#include <string>
#include <string_view>

namespace {

/// CLI options for the evaluator executable.
///
/// The evaluator follows the GOW external-evaluator contract:
///   <exe> --input input.json --output output.json
///
/// Additionally, we provide a discovery option:
///   --print-functions
/// which prints all built-in function names and their recommended bounds, then exits.

struct CliOptions {
    std::filesystem::path input_path;
    std::filesystem::path output_path;
    bool show_help = false;
    bool print_functions = false;
};

std::string_view exe_name_or_default(int argc, char** argv) noexcept {
    if (argc > 0 && argv != nullptr && argv[0] != nullptr && argv[0][0] != '\0') {
        return argv[0];
    }
    return "2d-function-evaluator";
}

/// Print concise usage information.
///
/// Keep this short because this tool is usually invoked by an orchestration system
/// (GOW). Human-oriented discovery is provided via --help and --print-functions.

void print_usage(std::ostream& os, std::string_view exe_name) {
    os << "Usage:\n"
       << "  " << exe_name << " --input <path> --output <path>\n"
       << "  " << exe_name << " --print-functions\n"
       << "  " << exe_name << " --help\n";
}

/// Print all registered functions and their recommended bounds, then exit.
///
/// Output format is intentionally simple and stable for easy scripting:
///   <name> x:[xmin,xmax] y:[ymin,ymax]

void print_functions(std::ostream& os) {
    std::size_t n = 0;
    const evaluator::FunctionInfo* reg = evaluator::registry(n);
    for (std::size_t i = 0; i < n; ++i) {
        const auto& e = reg[i];
        os << e.name
           << " x:[" << e.bounds.xmin << "," << e.bounds.xmax << "]"
           << " y:[" << e.bounds.ymin << "," << e.bounds.ymax << "]\n";
    }
}

/// Parse CLI arguments.
///
/// Notes:
/// - Unknown flags are tolerated to keep compatibility with orchestration wrappers.
/// - We validate required flags only if we are not in a "print/help" mode.

bool parse_cli(int argc, char** argv, CliOptions& out, std::string& error) {
    // Accept running with no args only for help-like behavior: require explicit flags.
    if (argc <= 1) {
        error = "missing required flags --input and --output (or use --print-functions / --help)";
        return false;
    }

    for (int i = 1; i < argc; ++i) {
        const std::string_view arg = argv[i] ? std::string_view{argv[i]} : std::string_view{};

        if (arg == "--help") {
            out.show_help = true;
            return true;  // short-circuit: help wins
        }
        if (arg == "--print-functions") {
            out.print_functions = true;
            return true;  // short-circuit: printing registry does not require I/O paths
        }
        if (arg == "--input") {
            if (i + 1 >= argc || argv[i + 1] == nullptr) {
                error = "--input requires a path";
                return false;
            }
            out.input_path = argv[++i];
            continue;
        }
        if (arg == "--output") {
            if (i + 1 >= argc || argv[i + 1] == nullptr) {
                error = "--output requires a path";
                return false;
            }
            out.output_path = argv[++i];
            continue;
        }

        // Unknown flags are tolerated for contract compatibility.
    }

    if (out.input_path.empty()) {
        error = "missing required flag --input";
        return false;
    }
    if (out.output_path.empty()) {
        error = "missing required flag --output";
        return false;
    }
    return true;
}

/// Best-effort error reporting that follows the evaluator contract.
///
/// If writing the failure output fails (e.g., invalid path), also report to stderr.
/// Returns the recommended process exit code.

int fail_and_maybe_write_output(const std::filesystem::path& output_path,
                                std::string_view message) noexcept {
    std::string write_error;
    if (!output_path.empty()) {
        if (evaluator::write_failure_output(output_path, std::string(message), write_error)) {
            return 1;
        }
    }

    // Either output path was empty or writing output failed.
    std::cerr << "Error: " << message << '\n';
    if (!write_error.empty()) {
        std::cerr << "Error: " << write_error << '\n';
    }
    return 1;
}

}  // namespace

int main(int argc, char** argv) {
    const std::string_view exe_name = exe_name_or_default(argc, argv);

    CliOptions cli;
    std::string error;
    if (!parse_cli(argc, argv, cli, error)) {
        print_usage(std::cerr, exe_name);
        std::cerr << "Error: " << error << '\n';
        return 2;  // CLI usage error
    }

    if (cli.show_help) {
        print_usage(std::cout, exe_name);
        return 0;
    }

    if (cli.print_functions) {
        // Contract-neutral discovery mode (does not touch input/output JSON files).
        print_functions(std::cout);
        return 0;
    }

    // Normal evaluator mode: read input.json, evaluate, write output.json.
    try {
        evaluator::EvalInput input{};
        if (!evaluator::read_eval_input(cli.input_path, input, error)) {
            return fail_and_maybe_write_output(cli.output_path, error);
        }

        const evaluator::FunctionPtr fn = evaluator::find_function(input.function_name);
        if (fn == nullptr) {
            const std::string fn_error = "unknown function: " + input.function_name;
            return fail_and_maybe_write_output(cli.output_path, fn_error);
        }

        const double value = fn(input.x, input.y);

        std::string write_error;
        if (!evaluator::write_success_output(cli.output_path, value, write_error)) {
            std::cerr << "Error: " << write_error << '\n';
            return 1;
        }
        return 0;

    } catch (const std::exception& ex) {
        return fail_and_maybe_write_output(cli.output_path, ex.what());
    } catch (...) {
        return fail_and_maybe_write_output(cli.output_path, "unexpected error");
    }
}