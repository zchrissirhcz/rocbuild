#include "mathx.h"
#include "report.h"

int main()
{
    print_result("2 + 3", mathx::add(2, 3));
    print_result("2 * 3", mathx::mul(2, 3));
    print_result("max", mathx::max(2, 3));
    return 0;
}
