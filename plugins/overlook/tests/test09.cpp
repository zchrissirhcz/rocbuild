#include <stdio.h>
#include <iostream>
#include <vector>

using namespace std;

int main()
{
    vector<int> data;
    data.push_back(1);
    data.push_back(2);
    data.push_back(3);

    for (int i = 0; i < data.size(); i++)
    {
        printf("data[%d]=%d\n", i, data[i]);
    }

    return 0;
}
