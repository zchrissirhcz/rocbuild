#include <iostream>

void func1()
{
    1; // C4555
}

void func2()
{
    int x;
    x; // C4555
}

void example1()
{
    func1();
    func2();
}

void example2()
{
    int i = 0, j = 0;
    i + j; // C4552
    // try the following line instead
    // (i + j);

    int k = 233;
}


bool master_is_working = false;
void example3()
{
    auto f = []()
    {
        !master_is_working;  // C4552
    };

    f();
    std::cout << std::boolalpha << master_is_working << std::endl;
    // expected output: true
    // actual output: true
    // this examples is taken from 程序员还需要理解汇编吗？ - 光度的回答 - 知乎
    // https://www.zhihu.com/question/609318862/answer/3115910062
}

int main()
{
    example1();
    example2();

    return 0;
}
