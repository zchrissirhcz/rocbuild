//https://docs.microsoft.com/en-us/cpp/error-messages/compiler-warnings/compiler-warning-level-1-c4075?view=msvc-160

// C4075.cpp
// compile with: /W1
#pragma init_seg("mysegg") // C4075

// try..
// #pragma init_seg(user)

// https://stackoverflow.com/a/10199440/2999096

// ```
// #pragma init_seg
// ```
// 是VC++特有的

// g++不能用，但有个类似的：
// ```
// Some_Class  A  __attribute__ ((init_priority (2000)));
// Some_Class  B  __attribute__ ((init_priority (543)));
// ```


int main()
{
    return 0;
}