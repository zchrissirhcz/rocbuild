#include <stdio.h>
#include <string>

int main()
{
    const std::string s = "你好";
    printf("%s\n", s.c_str());
    return 0;
}