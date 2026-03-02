#pragma once

#include <cstddef>
#include <string_view>

namespace evaluator {

using FunctionPtr = double (*)(double, double);

struct Bounds {
    double xmin{};
    double xmax{};
    double ymin{};
    double ymax{};
};

struct FunctionInfo {
    std::string_view name;
    FunctionPtr fn;
    Bounds bounds;
};

/// Find an objective function by name (case-sensitive).
FunctionPtr find_function(std::string_view name) noexcept;

/// Returns pointer to an internal, read-only registry array and writes its size to out_count.
/// The returned pointer remains valid for the lifetime of the program.
const FunctionInfo* registry(std::size_t& out_count) noexcept;

}  // namespace evaluator