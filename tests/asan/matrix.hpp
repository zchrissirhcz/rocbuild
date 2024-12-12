#pragma once

class Matrix
{
public:
    Matrix(int rows, int cols) : rows(rows), cols(cols)
    {
        data = new int[rows * cols];
    }

    ~Matrix()
    {
        delete[] data;
    }

    int& operator()(int i, int j)
    {
        return data[i * cols + j];
    }

    int operator()(int i, int j) const
    {
        return data[i * cols + j];
    }

    int getRows() const
    {
        return rows;
    }

    int getCols() const
    {
        return cols;
    }

private:
    int rows;
    int cols;
    int* data;
};