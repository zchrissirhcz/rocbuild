#include <stdio.h>

void print_data(int* data, size_t len)
{
    for (size_t i = 0; i < len; i++)
    {
        printf("%d\n", data[i]);
    }
}

int main()
{
    int data[10] = { 0, 1, 2, 3, 4, 5, 6, 7, 8, 9 };
    print_data(data, 10, 233);

    return 0;
}
