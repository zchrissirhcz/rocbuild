#include <stdio.h>

int main()
{
    int data[4];
    // there is `break` missing. It will run fallthrough
    int a = 0;
    switch (a)
    {
    case 0:
        printf("0\n");
        data[a] = 233;
    case 1:
        printf("1\n");
        data[a-1] = 233;
    case 2:
        printf("2\n");
        data[a-2] = 233;
    case 3:
        printf("3\n");
        data[a-3] = 233;
        break;
    }
}
