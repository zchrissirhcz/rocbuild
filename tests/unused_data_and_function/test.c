#include <stdio.h>

// Unused function (should be removed)
void unused_function() {
    printf("This function is not used.\n");
}

// Used function (should be kept)
void used_function() {
    printf("This function is used.\n");
}

// Unused global variable (should be removed)
int unused_global_variable = 42;

// Used global variable (should be kept)
int used_global_variable = 100;

int main() {
    void (*volatile func_ptr)() = used_function;
    func_ptr();
    printf("Used global variable: %d\n", used_global_variable);
    return 0;
}