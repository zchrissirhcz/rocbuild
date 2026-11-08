# Analysis of missing return value for non-void function, MSVC

First, rename main.cpp to main.c, and modify CMakeLists.txt.

## Debug build type result
In VS2022-x64 Debug build type, the running result is:
```
0 1 2 3 4 5 6 7 8 9
res=233
```

![](vs2022-x64-Debug.png)

`res=233` is due to `hello()` returns 233.

## RelWithDebInfo build type result
```
0 1 2 3 4 5 6 7 8 9
res=1
```

![](vs2022-x64-RelWithDebInfo.png)

`res=1` is due to `printf()` returns 1. The `hello()` is not called due to optimization.

## Corresponding code:
```c
#include <stdio.h>

int hello()
{
    return 233;
}

int print_data(int* data, int len)
{
    for (int i = 0; i < len; i++)
    {
        printf("%d ", data[i]);
    }
    printf("\n");
    // hello();
}

void example1()
{
    int data[10];
    for (int i = 0; i < 10; i++)
    {
        data[i] = i;
    }
    int res = print_data(data, 10);

    printf("res = %d\n", res);
}

int main()
{
    example1();

    return 0;
}

```


## Pure-command-line
Enter x64 Native Tools Command Prompt windows,

```bash
cd build
dumpbin /DISASM RelWithDebInfo\test_rule4.exe > 1.asm
```
