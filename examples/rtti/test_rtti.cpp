// rtti_test.cpp
#include <iostream>
#include <typeinfo>

// ---------- 检测编译期特性 ----------
//#if defined(__GXX_RTTI) || defined(_CPPRTTI)
//#  define HAS_RTTI 1
//#else
//#  define HAS_RTTI 0
//#endif
//
//#if defined(__cpp_exceptions) || defined(__EXCEPTIONS) || defined(_CPPUNWIND)
//#  define HAS_EXCEPTIONS 1
//#else
//#  define HAS_EXCEPTIONS 0
//#endif


// ---------- 测试用类型 ----------
struct Animal {
    virtual ~Animal() = default;
    virtual const char* name() const { return "Animal"; }
};
struct Dog : Animal {
    const char* name() const override { return "Dog"; }
    void bark() const { std::cout << "    Woof!\n"; }
};
struct Cat : Animal {
    const char* name() const override { return "Cat"; }
    void meow() const { std::cout << "    Meow!\n"; }
};

int main() {
    Dog dog;
    Cat cat;
    Animal* animals[] = { &dog, &cat };

    // ===== 虚函数分发:不需要 RTTI,禁用 RTTI 后仍正常 =====
    std::cout << "Virtual dispatch (no RTTI needed):\n";
    for (Animal* a : animals)
        std::cout << "  " << a->name() << "\n";

    // ===== RTTI 相关(只在开启时编译) =====
    std::cout << "\nRTTI is ENABLED\n";

    // 1) typeid
    std::cout << "  typeid(*a).name(): ";
    for (Animal* a : animals)
        std::cout << typeid(*a).name() << " ";
    std::cout << "\n";

    // 2) typeid 比较
    std::cout << "  typeid(dog) == typeid(Dog): "
              << (typeid(dog) == typeid(Dog) ? "true" : "false") << "\n";

    // 3) dynamic_cast 指针:成功
    if (Dog* d = dynamic_cast<Dog*>(&dog)) {
        std::cout << "  dynamic_cast<Dog*>(&dog) succeeded:";
        d->bark();
    }

    // 4) dynamic_cast 指针:失败返回 nullptr
    if (Dog* d = dynamic_cast<Dog*>(&cat)) {
        d->bark();
    } else {
        std::cout << "  dynamic_cast<Dog*>(&cat) returned nullptr\n";
    }

    // 5) dynamic_cast 引用:失败抛 std::bad_cast(需开启异常)
    try {
        Animal& ref = cat;
        Dog&    dr  = dynamic_cast<Dog&>(ref);
        dr.bark();
    } catch (const std::bad_cast& e) {
        std::cout << "  dynamic_cast<Dog&>(cat) threw std::bad_cast: "
                  << e.what() << "\n";
    }
    std::cout << "  [exceptions disabled] skip dynamic_cast-reference test "
                 "(would call std::terminate)\n";

    std::cout << "\nRTTI is DISABLED (this is what we want!)\n";
    std::cout << "  The following would fail to compile without #if:\n";
    std::cout << "    typeid(*a)\n";
    std::cout << "    dynamic_cast<Dog*>(a)\n";
    std::cout << "    dynamic_cast<Dog&>(ref)\n";

    return 0;
}