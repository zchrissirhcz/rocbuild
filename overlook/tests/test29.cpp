#include <stdio.h>

void hello(char* data)
{
    if (data)
    {
        printf("%s\n", data);
    }
    else
    {
        printf("hello world\n");
    }
}

int main()
{
    char* data1 = "hello cmake";
    int size1 = sizeof(data1);
    printf("sizeof(data1)=%d\n", size1); // 输出的是sizeof(char*)的长度
    hello(data1);                        // 能正常执行并且输出 "hello cmake"，但若hello函数内要用sizeof(data1)，容易出错

    char data2[] = { "hello cmake" };
    int size2 = sizeof(data2);
    printf("sizeof(data2)=%d\n", size2); // 输出的是sizeof(data2)的长度，包括了\0在内
    hello(data2);                        // 能正常执行并且输出 "hello cmake"，而若hello函数内要用sizeof(data2)，则能算对

    return 0;
}
