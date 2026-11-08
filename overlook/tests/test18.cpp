#include <iostream>
using namespace std;

#define TEST "test1"
#define TEST "test2" // C4005 delete or rename to resolve the warning

int main()
{
    cout << TEST << endl;
}
