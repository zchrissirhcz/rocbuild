#include <stdio.h>

int hello()
{
    return 233;
}

int print_data(int* data, int len)
{
    for (int i = 0; i < len; i++)
    {
        printf("%d ", data[i]);
    }
    printf("\n");
    // here the return statement is missing, the compiler will generate an UB
    hello();
}

void example1()
{
    int data[10];
    for (int i = 0; i < 10; i++)
    {
        data[i] = i;
    }
    int res = print_data(data, 10);

    printf("res=%d\n", res);
}

//---------------------

int func1(int i)
{
    if (i)
        return 3; // C4715 warning, nothing returned if i == 0
}

void fatal()
{
}
int glue()
{
    if (0)
        return 1;
    else if (0)
        return 0;
    else
        fatal(); // C4715
}

void example2()
{
    func1(233);
    int qaq = glue();
    printf("%d\n", qaq);
}

//-----------------------------

int main()
{
    example1();
    //example2();

    return 0;
}
