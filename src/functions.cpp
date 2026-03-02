#include "functions.hpp"

#include <array>
#include <cmath>
#include <numbers>
#include <string_view>

namespace evaluator {

namespace {

// 1) Sphere
double sphere(double x, double y) noexcept {
    return (x * x) + (y * y);
}

// 2) Rosenbrock
double rosenbrock(double x, double y) noexcept {
    const double a = 1.0 - x;
    const double b = y - (x * x);
    return (a * a) + (100.0 * b * b);
}

// 3) Rastrigin
double rastrigin(double x, double y) noexcept {
    constexpr double pi = std::numbers::pi_v<double>;
    return 20.0
        + ((x * x) - 10.0 * std::cos(2.0 * pi * x))
        + ((y * y) - 10.0 * std::cos(2.0 * pi * y));
}

// 4) Ackley
double ackley(double x, double y) noexcept {
    constexpr double pi = std::numbers::pi_v<double>;
    constexpr double a = 20.0;
    constexpr double b = 0.2;

    const double sum_sq = 0.5 * ((x * x) + (y * y));
    const double sum_cos = 0.5 * (std::cos(2.0 * pi * x) + std::cos(2.0 * pi * y));

    return -a * std::exp(-b * std::sqrt(sum_sq))
           - std::exp(sum_cos)
           + a
           + std::exp(1.0);
}

// 5) Himmelblau
double himmelblau(double x, double y) noexcept {
    const double a = (x * x) + y - 11.0;
    const double b = x + (y * y) - 7.0;
    return (a * a) + (b * b);
}

// 6) Beale
double beale(double x, double y) noexcept {
    const double t1 = 1.5 - x + x * y;
    const double t2 = 2.25 - x + x * y * y;
    const double t3 = 2.625 - x + x * y * y * y;
    return (t1 * t1) + (t2 * t2) + (t3 * t3);
}

// 7) Goldstein–Price
double goldstein_price(double x, double y) noexcept {
    const double a = x + y + 1.0;
    const double b = 19.0 - 14.0 * x + 3.0 * x * x
                     - 14.0 * y + 6.0 * x * y + 3.0 * y * y;

    const double c = 2.0 * x - 3.0 * y;
    const double d = 18.0 - 32.0 * x + 12.0 * x * x
                     + 48.0 * y - 36.0 * x * y + 27.0 * y * y;

    return (1.0 + (a * a) * b) * (30.0 + (c * c) * d);
}

// 8) McCormick
double mccormick(double x, double y) noexcept {
    return std::sin(x + y)
           + (x - y) * (x - y)
           - 1.5 * x
           + 2.5 * y
           + 1.0;
}

constexpr std::array<FunctionInfo, 8> kRegistry{{
    {"sphere", &sphere, {-5.0, 5.0, -5.0, 5.0}},
    {"rosenbrock", &rosenbrock, {-2.0, 2.0, -1.0, 3.0}},
    {"rastrigin", &rastrigin, {-5.12, 5.12, -5.12, 5.12}},
    {"ackley", &ackley, {-5.0, 5.0, -5.0, 5.0}},
    {"himmelblau", &himmelblau, {-6.0, 6.0, -6.0, 6.0}},
    {"beale", &beale, {-4.5, 4.5, -4.5, 4.5}},
    {"goldstein_price", &goldstein_price, {-2.0, 2.0, -2.0, 2.0}},
    {"mccormick", &mccormick, {-1.5, 4.0, -3.0, 4.0}},
}};

}  // namespace

FunctionPtr find_function(std::string_view name) noexcept {
    for (const auto& e : kRegistry) {
        if (e.name == name) {
            return e.fn;
        }
    }
    return nullptr;
}

const FunctionInfo* registry(std::size_t& out_count) noexcept {
    out_count = kRegistry.size();
    return kRegistry.data();
}

}  // namespace evaluator