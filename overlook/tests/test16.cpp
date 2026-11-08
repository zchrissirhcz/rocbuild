#include <stdio.h>
#include <stdlib.h>

int main()
{
    int data[5];
    for (int i = 0; i < 5; i++)
    {
        data[i] = i;
    }
    free(data);

    return 0;
}
