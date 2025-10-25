#include <atomic>
#include <iostream>

// 自定义结构体（大小超过指针长度，且非内置类型）
struct MyStruct {
    int a;
    double b;
    long long c;
};

int main() {
    // 初始化原子变量
    std::atomic<MyStruct> atomic_struct;

    // 设置初始值
    MyStruct init_val = {42, 3.14, 123456789LL};
    atomic_struct.store(init_val);

    // 原子加载并打印
    MyStruct loaded = atomic_struct.load();
    std::cout << "Loaded values: " 
              << loaded.a << ", " 
              << loaded.b << ", " 
              << loaded.c << std::endl;

    // 原子交换
    MyStruct new_val = {100, 9.81, 987654321LL};
    MyStruct old_val = atomic_struct.exchange(new_val);

    std::cout << "Old values: " 
              << old_val.a << ", " 
              << old_val.b << ", " 
              << old_val.c << std::endl;

    std::cout << "New values: " 
              << atomic_struct.load().a << ", " 
              << atomic_struct.load().b << ", " 
              << atomic_struct.load().c << std::endl;

    return 0;
}
