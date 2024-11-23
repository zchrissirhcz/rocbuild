#include "foo_math.h"
#include <stdlib.h>

static int compare(const void *a, const void *b)
{
    int int_a = *(int *)a;
    int int_b = *(int *)b;

    if (int_a < int_b) return -1;
    else if (int_a > int_b) return 1;
    else return 0;
}

void abs_sort(int n, int* data)
{
    for (int i = 0; i < n; i++)
    {
        data[i] = abs(i);
    }
    qsort(data, n, sizeof(int), compare);
}
