#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <string>

class SmartPhone
{
    int price;
    std::string name;
};

int main()
{
    printf("hello cmake\n");

    SmartPhone* sp = (SmartPhone*)malloc(sizeof(SmartPhone));
    memset(sp, 0, sizeof(*sp));

    return 0;
}
