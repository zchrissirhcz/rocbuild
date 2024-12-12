#include <iostream>  
#include <opencv2/opencv.hpp>  

int main() {  
    // Create a simple grayscale image (100x100)  
    cv::Mat image = cv::Mat::zeros(100, 100, CV_8UC1);  

    // Normal pixel access  
    int x = 50, y = 50;  
    image.data[y * image.cols + x] = 255; // Set the center pixel to white  

    // Out-of-bounds access (directly manipulating the underlying data pointer)  
    uchar* data = image.data;  
    int total_pixels = image.rows * image.cols;  

    // Construct an out-of-bounds access  
    // This will not trigger any OpenCV checks but will cause undefined behavior  
    uchar out_of_bounds_value = data[total_pixels + 10]; // Access beyond the image data  
    std::cout << "Out of bounds value: " << (int)out_of_bounds_value << std::endl;  

    return 0;  
}