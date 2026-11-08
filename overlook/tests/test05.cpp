#include <stdio.h>

int main()
{
    int len = 100;
    for (int i = 0; i < 10; i++)
    {
        int len = 10;
        printf("process %d/%d\n", i, len);
    }

    return 0;
}
