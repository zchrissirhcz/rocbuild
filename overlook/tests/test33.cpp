#include <stdio.h>

int main()
{
    int a = 3;

    if (a == 1)
    {
        printf("1\n");
    }
    else if (a = 2) // people careless write this, if not notice linter (e.g. Intellisense, Clangd), this only lead to compile warn for first time compile, later no warning
    {
        printf("2\n");
    }
    else if (a == 3)
    {
        printf("3\n");
    }

    return 0;
}
