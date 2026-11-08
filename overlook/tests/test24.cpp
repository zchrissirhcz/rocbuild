// C4003.cpp
// compile with: /WX
#define test(a, b) (a + b)

int main()
{
    int a = 1;
    int b = 2;
    a = test(b); // C4003
    // try..
    a = test(a, b);

    return 0;
}