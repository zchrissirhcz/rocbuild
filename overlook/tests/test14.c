#include <stdio.h>
#include <stdlib.h>

int main()
{
    int* data = (int*)malloc(sizeof(int) * 10);
    for (int i = 0; i < 10; i++)
    {
        data[i] = i;
    }
    void* p = data;
    p += 5;

    return 0;
}
