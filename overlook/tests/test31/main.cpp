#include <iostream>

class Array
{
public:
    Array(int _len)
        : len(_len)
    {
        data = new double[len];
        for (int i = 0; i < len; i++)
        {
            data[i] = 0;
            printf("data[%d]=%f\n", i, data[i]);
        }
    }

    friend std::ostream& operator<<(std::ostream& os, const Array& arr);

public:
    int len;
    double* data;
};

std::ostream& operator<<(std::ostream& os, const Array& arr)
{
    for (int i = 0; i < arr.len; i++)
    {
        if (i > 0)
        {
            os << ', '; // 这里，导致输出的值，从第二个开始，原本是0而输出不为0
        }
        os << arr.data[i] << '\n';
    }
    os << '\n';
    return os;
}

void test_array()
{
    Array arr(4);
    std::cout << arr << std::endl;
}

int main()
{
    test_array();

    return 0;
}
