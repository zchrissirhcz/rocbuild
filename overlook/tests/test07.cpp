#include <stdio.h>

int read_of_unitialized()
{
    int data; // garbage value

    if (data > 10)
    {
        printf("data > 10\n");
    }
    else
    {
        printf("data <= 10\n");
    }

    int* ptr;
    printf("*ptr = %d\n", *ptr);

    return 0;
}

__attribute__((noinline))
int bar(int n)
{
    return n * n;
}

__attribute__((noinline))
int foo(const int *p)
{
    int n;

    if (p)
        n = p[0];
    return bar(n);
}

// https://zhuanlan.zhihu.com/p/1891261469053671394
// segmentation fault
int write_of_unitlialized()
{
    foo(0);
    return 0;
}

int main()
{
    // read_of_unitialized();
    write_of_unitlialized();

    return 0;
}