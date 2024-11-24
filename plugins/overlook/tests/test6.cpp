#include <stdio.h>

int* get_lucky_number()
{
    int data = 10;
    return &data;
}

int main()
{
    int* lucky_number = get_lucky_number();
    printf("lucky number is %d\n", *lucky_number);

    return 0;
}
