#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

// ---------- 1. 自定义异常类:继承 std::runtime_error ----------
class InsufficientFunds : public std::runtime_error {
public:
    InsufficientFunds(double balance, double amount)
        : std::runtime_error("余额不足"), balance_(balance), amount_(amount) {}

    double balance() const { return balance_; }
    double amount()  const { return amount_;  }

private:
    double balance_;
    double amount_;
};

class Account {
public:
    explicit Account(double b) : balance_(b) {}

    void withdraw(double amount) {
        if (amount <= 0)
            throw std::invalid_argument("取款金额必须为正数");  // 标准异常
        if (amount > balance_)
            throw InsufficientFunds(balance_, amount);         // 自定义异常
        balance_ -= amount;
    }

    double balance() const { return balance_; }

private:
    double balance_;
};

// ---------- 2. 标准异常示例 ----------
int safe_get(const std::vector<int>& v, std::size_t i) {
    return v.at(i);   // 越界时抛 std::out_of_range
}

// ---------- 3. 演示栈展开:局部对象析构仍会被调用 ----------
struct Guard {
    ~Guard() { std::cout << "[Guard] 析构被调用(栈展开)\n"; }
};

int main() {
    // --- 自定义异常 + 标准异常 ---
    try {
        Account acc(100.0);
        acc.withdraw(30);
        std::cout << "余额: " << acc.balance() << "\n";

        Guard g;                     // 抛异常时会被析构
        acc.withdraw(500);           // 抛 InsufficientFunds
    }
    catch (const InsufficientFunds& e) {          // 按 const 引用捕获
        std::cout << "捕获自定义异常: " << e.what()
                  << " (余额=" << e.balance()
                  << ", 请求=" << e.amount() << ")\n";
    }
    catch (const std::exception& e) {             // 兜底:捕获所有标准异常
        std::cout << "捕获标准异常: " << e.what() << "\n";
    }

    // --- 标准异常:vector 越界 ---
    try {
        std::vector<int> v{1, 2, 3};
        std::cout << safe_get(v, 5) << "\n";
    }
    catch (const std::out_of_range& e) {
        std::cout << "越界: " << e.what() << "\n";
    }

    return 0;
}