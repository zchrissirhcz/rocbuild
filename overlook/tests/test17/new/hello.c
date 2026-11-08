#include "hello.h"

#include <stdio.h>

void hello(const char* name, int repeat)
{
    for (int i = 0; i < repeat; i++)
    {
        if (name == NULL)
        {
            printf("hello world\n");
        }
        else
        {
            printf("hello, %s\n", name);
        }
    }
}