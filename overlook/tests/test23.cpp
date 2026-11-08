// C4002.cpp
// compile with: /W1
#define test(a) (a)

int main()
{
    int a = 1;
    int b = 2;
    a = test(a, b); // C4002
    // try..
    a = test(a);

    return 0;
}