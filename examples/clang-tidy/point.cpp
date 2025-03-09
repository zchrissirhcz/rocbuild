#include <stdio.h>

struct Point {
	int x;
	int y;
};

int main()
{
	Point* p = new Point;
    printf("x = %d, y = %d\n", p->x, p->y);
    delete p;

    int m = 0xcdcdcdcd;
    printf("m = %d\n", m);

	return 0;
}
