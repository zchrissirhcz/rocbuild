# Analysis of missing return value for non-void function, GCC compiler

## Preparation
- The code and compiler information can be obtained in: https://godbolt.org/z/1GdKb7dc9
- gcc version 13.2
- analysis method: 
    - run the code, found there's no crash, but result is "tricky"
    - observe `eax` register for function return value
- conclusion
    - the `hello()` function makes the `eax` register stores `233`
    - the `print_data()` function 

## Code
`main.c` (instead of cpp file):
```cpp
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
    hello();
}

void example1()
{
    int data[10];
    for (int i = 0; i < 10; i++)
    {
        data[i] = i;
    }
    int res = print_data(data, 10);

    printf("res=%d\n", res);
}

int main()
{
    example1();
    //example2();

    return 0;
}
```


## Execution result
```
ASM generation compiler returned: 0
Execution build compiler returned: 0
Program returned: 0
0 1 2 3 4 5 6 7 8 9 
res=233
```

## Analysis
The disassemble code of `print_data()` is:
```asm
print_data:
 push   rbp
 mov    rbp,rsp
 sub    rsp,0x20
 mov    QWORD PTR [rbp-0x18],rdi
 mov    DWORD PTR [rbp-0x1c],esi
 mov    DWORD PTR [rbp-0x4],0x0
 jmp    401184 <print_data+0x43>
 mov    eax,DWORD PTR [rbp-0x4]
 cdqe
 lea    rdx,[rax*4+0x0]
 mov    rax,QWORD PTR [rbp-0x18]
 add    rax,rdx
 mov    eax,DWORD PTR [rax]
 mov    esi,eax
 mov    edi,0x402004
 mov    eax,0x0
 call   401040 <printf@plt>
 add    DWORD PTR [rbp-0x4],0x1
 mov    eax,DWORD PTR [rbp-0x4]
 cmp    eax,DWORD PTR [rbp-0x1c]
 jl     401159 <print_data+0x18>
 mov    edi,0xa
 call   401030 <putchar@plt>
 mov    eax,0x0
 call   401136 <hello>
 nop
 leave
 ret
```

After calling `hello()`, the `eax` register is with value `233`. 
(Note the `leave` is the function epilogue, hence the stack is balanced, ref: https://handwiki.org/wiki/Function_prologue_and_epilogue)