#include <stdio.h>

int x = 7;
int y = 5;

void p1()
{
}

void p2();

int main()
{
    p2();

    printf("y=%d\n", y);

    return 0;
}