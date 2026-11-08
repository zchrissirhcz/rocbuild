
#include <iostream>
#include <string>

using namespace std;

class A
{
public:
    A()
    {
        cout << "new object" << endl;
    }
    ~A()
    {
        cout << "delete object" << endl;
    }
};

A&& func()
{
    return move(A());
}

int main()
{
    A&& a = func();
    cout << "function end" << endl;
    return 0;
}
