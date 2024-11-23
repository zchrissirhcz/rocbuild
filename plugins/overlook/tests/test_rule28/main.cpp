// C4553.cpp
// compile with: /W1
int func()
{
    return 0;
}

int main()
{
    int i = 233;
    i == func(); // C4553
    // try the following line instead
    // i = func();

    return 0;
}
