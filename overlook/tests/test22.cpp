// C4129.cpp
// compile with: /W1

#include <iostream>

int main()
{
    //char array1[] = "\/709";   // C4129
    char array2[] = "\n709"; // OK

    std::cout << "Default arguments: 1 I:\datasets\ADAS\adas_pcbt_test_20190403\images\list_imgtxt" << std::endl;

    return 0;
}