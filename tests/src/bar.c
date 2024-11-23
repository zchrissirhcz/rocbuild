#include "bar.h"
#include "bar_internal.h"

int bar() { return 1 + bar_internal(); }