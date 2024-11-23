#include <stdio.h>

int reflect101_clip(int ti, int size)
{
    if (ti < 0)
    {
        return -ti;
    }
    else if (ti > size - 1)
    {
        return 2 * size - 2 - ti; // size-1 - (ti-(size-1))  =>  size - 1 - (ti - size + 1) => size - 1 - ti + size - 1 => 2*size - 2 - ti
    }
    // 这里忘记 ti 在正常范围的情况下的返回值
    //else {
    //    return ti;
    //}
}

int main()
{
    printf("hello cmake\n");
    int ti = 20;
    int size = 100;
    int new_ti = reflect101_clip(20, size);
    printf("ti=%d, reflect101_clip(ti,%d)=%d\n", ti, size, new_ti);
    return 0;
}
