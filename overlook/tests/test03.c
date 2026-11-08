#include <stdio.h>

void print_data(int* data, int len)
{
    for (int i = 0; i < len; i++)
    {
        printf("%d ", data[i]);
    }
    printf("\n");
}

int main()
{
    unsigned char data[10];
    for (int i = 0; i < 10; i++)
    {
        data[i] = i;
    }
    print_data(data, 10);

    return 0;
}
