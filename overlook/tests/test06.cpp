#include <stdio.h>

int* get_lucky_number()
{
    int data = 10;
    return &data;
}

int return_stack_addr()
{
    int* lucky_number = get_lucky_number();
    printf("lucky number is %d\n", *lucky_number);

    return 0;
}


#include <string>
#include <iostream>

std::string& f()
{
    std::string s = "Example";
    return s; // exits the scope of s:
              // its destructor is called and its storage deallocated
}

int dangling_reference()
{ 
    std::string& r = f(); // dangling reference
    std::cout << r;       // undefined behavior: reads from a dangling reference
    std::string s = f();  // undefined behavior: copy-initializes from a dangling reference
    std::cout << s << std::endl;
    return 0;
}


int main(int argc, char** /*argv*/)
{
    return_stack_addr();
    dangling_reference();

    return 0;
}
