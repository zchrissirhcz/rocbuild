#include <stdio.h>

int main()
{
    //(1)
#ifdef __cplusplus
    const int maxn = 10;
    int a[maxn];
    a[10] = 1;
#endif

//(2)
#define MAX 25
    int ar[MAX];
    ar[MAX] = 1;

    //(3)
    int buff[25];
    for (int i = 0; i <= 25; i++) // i exceeds array bound
    {
        buff[i] = 0; // initialize i
        //if (i == 1) { /* Do something */ }
    }

    //(4)
    int data[10];
    data[10] = 233;
    printf("data[10]=%d\n", data[10]);

    return 0;
}
