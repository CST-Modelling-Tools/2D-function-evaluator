#include "functions.hpp"

#include <cstddef>
#include <cstdio>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>

#include <nlohmann/json.hpp>

#ifdef _WIN32
    #define NOMINMAX
    #include <windows.h>
#endif

namespace fs = std::filesystem;

namespace {

fs::path make_temp_dir() {
    const fs::path base = fs::temp_directory_path() / "2d_function_evaluator_tests";
    fs::create_directories(base);

    char buf[L_tmpnam];
    if (std::tmpnam(buf) == nullptr) {
        throw std::runtime_error("std::tmpnam failed");
    }

    const fs::path unique = base / fs::path(buf).filename();
    fs::create_directories(unique);
    return unique;
}

void write_json_file(const fs::path& p, const nlohmann::json& j) {
    std::ofstream os(p, std::ios::binary);
    if (!os) {
        throw std::runtime_error("failed to open file for writing: " + p.string());
    }
    os << j.dump(2);
    os.flush();
    if (!os) {
        throw std::runtime_error("failed to write file: " + p.string());
    }
}

nlohmann::json read_json_file(const fs::path& p) {
    std::ifstream is(p, std::ios::binary);
    if (!is) {
        throw std::runtime_error("failed to open file for reading: " + p.string());
    }
    nlohmann::json j;
    is >> j;
    return j;
}

void require(bool cond, const std::string& msg) {
    if (!cond) {
        throw std::runtime_error(msg);
    }
}

#ifdef _WIN32

std::wstring to_wstring(const std::string& s) {
    if (s.empty()) return std::wstring{};
    const int len = MultiByteToWideChar(CP_UTF8, 0, s.c_str(), -1, nullptr, 0);
    if (len <= 0) throw std::runtime_error("MultiByteToWideChar failed");
    std::wstring w(static_cast<std::size_t>(len - 1), L'\0');
    MultiByteToWideChar(CP_UTF8, 0, s.c_str(), -1, w.data(), len);
    return w;
}

int run_process_windows(const fs::path& exe,
                        const fs::path& input,
                        const fs::path& output) {
    // Build a single command line string as required by CreateProcessW.
    // We quote every argument defensively.
    const std::string cmd_utf8 =
        "\"" + exe.string() + "\""
        " --input \"" + input.string() + "\""
        " --output \"" + output.string() + "\"";

    std::wstring cmd = to_wstring(cmd_utf8);

    STARTUPINFOW si{};
    si.cb = sizeof(si);
    PROCESS_INFORMATION pi{};

    // CreateProcessW may modify the command line buffer; pass a mutable buffer.
    std::wstring mutable_cmd = cmd;

    const BOOL ok = CreateProcessW(
        /*lpApplicationName*/ nullptr,
        /*lpCommandLine*/    mutable_cmd.data(),
        /*lpProcessAttributes*/ nullptr,
        /*lpThreadAttributes*/  nullptr,
        /*bInheritHandles*/     FALSE,
        /*dwCreationFlags*/     0,
        /*lpEnvironment*/       nullptr,
        /*lpCurrentDirectory*/  nullptr,
        /*lpStartupInfo*/       &si,
        /*lpProcessInformation*/&pi
    );

    if (!ok) {
        const DWORD err = GetLastError();
        throw std::runtime_error("CreateProcessW failed with GetLastError=" + std::to_string(err));
    }

    WaitForSingleObject(pi.hProcess, INFINITE);

    DWORD exit_code = 0;
    GetExitCodeProcess(pi.hProcess, &exit_code);

    CloseHandle(pi.hThread);
    CloseHandle(pi.hProcess);

    return static_cast<int>(exit_code);
}

#endif

}  // namespace

int main(int argc, char** argv) {
    try {
        // 1) Internal registry smoke test
        {
            std::size_t n = 0;
            const evaluator::FunctionInfo* reg = evaluator::registry(n);
            require(reg != nullptr, "registry() returned null");
            require(n > 0, "registry() returned empty registry");

            auto fn = evaluator::find_function("sphere");
            require(fn != nullptr, "find_function(\"sphere\") returned null");

            const double v = fn(3.0, 4.0);
            require(v == 25.0, "sphere(3,4) expected 25.0, got " + std::to_string(v));
        }

        // 2) External contract smoke test
        require(argc >= 2 && argv[1] != nullptr && std::string(argv[1]).size() > 0,
                "missing evaluator executable path argument");

        const fs::path evaluator_exe = fs::path(argv[1]);
        require(fs::exists(evaluator_exe), "evaluator executable does not exist: " + evaluator_exe.string());

        const fs::path tmpdir = make_temp_dir();
        const fs::path input_path = tmpdir / "input.json";
        const fs::path output_path = tmpdir / "output.json";

        const nlohmann::json input = {
            {"run_id", "test_run"},
            {"candidate_id", "test_candidate"},
            {"params", {{"x", 3.0}, {"y", 4.0}, {"function", "sphere"}}},
            {"context", nlohmann::json::object()}
        };

        write_json_file(input_path, input);

#ifdef _WIN32
        const int rc = run_process_windows(evaluator_exe, input_path, output_path);
#else
        // If you later run tests on Linux/macOS CI, replace this with posix_spawn/exec.
        const std::string cmd =
            "\"" + evaluator_exe.string() + "\""
            " --input \"" + input_path.string() + "\""
            " --output \"" + output_path.string() + "\"";
        const int rc = std::system(cmd.c_str());
#endif

        require(rc == 0, "evaluator exited with non-zero code: " + std::to_string(rc));
        require(fs::exists(output_path), "output.json was not created: " + output_path.string());

        const nlohmann::json out = read_json_file(output_path);

        require(out.contains("status") && out["status"].is_string(), "output missing string field 'status'");
        require(out["status"].get<std::string>() == "ok", "evaluator returned non-ok status");

        double f = 0.0;
        bool found = false;
        if (out.contains("objective") && out["objective"].is_number()) {
            f = out["objective"].get<double>();
            found = true;
        } else if (out.contains("metrics") && out["metrics"].is_object() &&
                   out["metrics"].contains("f") && out["metrics"]["f"].is_number()) {
            f = out["metrics"]["f"].get<double>();
            found = true;
        }

        require(found, "output missing objective value (expected 'objective' or 'metrics.f')");
        require(f == 25.0, "expected objective 25.0, got " + std::to_string(f));

        // Best-effort cleanup
        std::error_code ec;
        fs::remove_all(tmpdir, ec);

        return 0;

    } catch (const std::exception& ex) {
        std::cerr << "Test failed: " << ex.what() << "\n";
        return 1;
    }
}