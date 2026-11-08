#include <CL/cl.h>

#include <cstdio>
#include <vector>

int main()
{
    cl_uint platform_count = 0;
    cl_int error = clGetPlatformIDs(0, nullptr, &platform_count);
    if (error != CL_SUCCESS)
    {
        std::printf("clGetPlatformIDs failed: %d\n", static_cast<int>(error));
        return 1;
    }

    std::printf("OpenCL platforms: %u\n", platform_count);
    std::vector<cl_platform_id> platforms(platform_count);
    if (platform_count > 0)
    {
        clGetPlatformIDs(platform_count, platforms.data(), nullptr);
    }

    for (cl_uint i = 0; i < platform_count; ++i)
    {
        char name[256] = {};
        char version[256] = {};
        clGetPlatformInfo(platforms[i], CL_PLATFORM_NAME, sizeof(name), name, nullptr);
        clGetPlatformInfo(platforms[i], CL_PLATFORM_VERSION, sizeof(version), version, nullptr);

        cl_uint device_count = 0;
        clGetDeviceIDs(platforms[i], CL_DEVICE_TYPE_ALL, 0, nullptr, &device_count);
        std::printf("[%u] %s | %s | devices: %u\n", i, name, version, device_count);
    }
    return 0;
}
