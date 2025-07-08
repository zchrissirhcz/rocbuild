// compile: 
//      cl dll_checker.cpp /std:c++17 /O2 /MT /EHsc /Fe:dll_checker.exe
// usage:
//      dll_checker.exe /path/to/xxx.exe
// related:
//      https://stackoverflow.com/questions/7378959/how-to-check-for-dll-dependency
//      Dependencies.exe -chain mydll.dll -depth 1
#include <windows.h>
#include <iostream>
#include <vector>
#include <string>
#include <algorithm>
#include <iomanip>
#include <sstream>

class PEAnalyzer {
private:
    HANDLE hFile;
    HANDLE hMapping;
    LPVOID pBase;
    PIMAGE_DOS_HEADER pDosHeader;
    PIMAGE_NT_HEADERS pNtHeaders;
    PIMAGE_SECTION_HEADER pSectionHeader;
    bool is64Bit;

public:
    PEAnalyzer() : hFile(INVALID_HANDLE_VALUE), hMapping(NULL), pBase(NULL) {}

    ~PEAnalyzer() {
        if (pBase) UnmapViewOfFile(pBase);
        if (hMapping) CloseHandle(hMapping);
        if (hFile != INVALID_HANDLE_VALUE) CloseHandle(hFile);
    }

    bool LoadFile(const std::string& filepath) {
        hFile = CreateFileA(filepath.c_str(), GENERIC_READ, FILE_SHARE_READ,
                           NULL, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
        if (hFile == INVALID_HANDLE_VALUE) {
            std::cerr << "Unable to open file: " << filepath << std::endl;
            return false;
        }

        hMapping = CreateFileMapping(hFile, NULL, PAGE_READONLY, 0, 0, NULL);
        if (!hMapping) {
            std::cerr << "Unable to create file mapping" << std::endl;
            return false;
        }

        pBase = MapViewOfFile(hMapping, FILE_MAP_READ, 0, 0, 0);
        if (!pBase) {
            std::cerr << "Unable to map file to memory" << std::endl;
            return false;
        }

        // Parse DOS header
        pDosHeader = (PIMAGE_DOS_HEADER)pBase;
        if (pDosHeader->e_magic != IMAGE_DOS_SIGNATURE) {
            std::cerr << "Not a valid PE file (invalid DOS signature)" << std::endl;
            return false;
        }

        // Parse NT header
        pNtHeaders = (PIMAGE_NT_HEADERS)((BYTE*)pBase + pDosHeader->e_lfanew);
        if (pNtHeaders->Signature != IMAGE_NT_SIGNATURE) {
            std::cerr << "Not a valid PE file (invalid PE signature)" << std::endl;
            return false;
        }

        // Determine 32-bit or 64-bit
        is64Bit = (pNtHeaders->FileHeader.Machine == IMAGE_FILE_MACHINE_AMD64);

        // Get section table
        pSectionHeader = IMAGE_FIRST_SECTION(pNtHeaders);

        return true;
    }

    // Convert RVA to file offset
    DWORD RvaToFileOffset(DWORD rva) {
        for (int i = 0; i < pNtHeaders->FileHeader.NumberOfSections; i++) {
            PIMAGE_SECTION_HEADER section = &pSectionHeader[i];
            if (rva >= section->VirtualAddress &&
                rva < section->VirtualAddress + section->SizeOfRawData) {
                return rva - section->VirtualAddress + section->PointerToRawData;
            }
        }
        return 0;
    }

    // Get list of imported DLLs
    std::vector<std::string> GetImportedDlls() {
        std::vector<std::string> dlls;

        DWORD importRva, importSize;
        if (is64Bit) {
            PIMAGE_NT_HEADERS64 pNt64 = (PIMAGE_NT_HEADERS64)pNtHeaders;
            importRva = pNt64->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_IMPORT].VirtualAddress;
            importSize = pNt64->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_IMPORT].Size;
        } else {
            PIMAGE_NT_HEADERS32 pNt32 = (PIMAGE_NT_HEADERS32)pNtHeaders;
            importRva = pNt32->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_IMPORT].VirtualAddress;
            importSize = pNt32->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_IMPORT].Size;
        }

        if (importRva == 0 || importSize == 0) {
            return dlls;
        }

        DWORD importOffset = RvaToFileOffset(importRva);
        if (importOffset == 0) {
            return dlls;
        }

        PIMAGE_IMPORT_DESCRIPTOR pImport = (PIMAGE_IMPORT_DESCRIPTOR)((BYTE*)pBase + importOffset);

        // Traverse import table
        while (pImport->Name != 0) {
            DWORD nameOffset = RvaToFileOffset(pImport->Name);
            if (nameOffset != 0) {
                char* dllName = (char*)((BYTE*)pBase + nameOffset);
                dlls.push_back(dllName);
            }
            pImport++;
        }

        return dlls;
    }
};

class DllFinder {
private:
    std::vector<std::string> searchPaths;
    std::string exeDirectory;

public:
    void InitSearchPaths(const std::string& exePath) {
        // 1. EXE directory
        size_t lastSlash = exePath.find_last_of("\\/");
        if (lastSlash != std::string::npos) {
            exeDirectory = exePath.substr(0, lastSlash);
            searchPaths.push_back(exeDirectory);
        }

        // 2. Windows system directory
        char systemDir[MAX_PATH];
        if (GetSystemDirectoryA(systemDir, MAX_PATH)) {
            searchPaths.push_back(systemDir);
        }

        // 3. Windows directory
        char windowsDir[MAX_PATH];
        if (GetWindowsDirectoryA(windowsDir, MAX_PATH)) {
            searchPaths.push_back(windowsDir);

            // 4. SysWOW64 (if exists)
            std::string sysWow64 = std::string(windowsDir) + "\\SysWOW64";
            if (GetFileAttributesA(sysWow64.c_str()) != INVALID_FILE_ATTRIBUTES) {
                searchPaths.push_back(sysWow64);
            }
        }

        // 5. Current directory
        char currentDir[MAX_PATH];
        if (GetCurrentDirectoryA(MAX_PATH, currentDir)) {
            searchPaths.push_back(currentDir);
        }

        // 6. PATH environment variable
        char* pathEnv = nullptr;
        size_t pathLen = 0;
        if (_dupenv_s(&pathEnv, &pathLen, "PATH") == 0 && pathEnv != nullptr) {
            std::string pathStr(pathEnv);
            size_t start = 0;
            size_t end = pathStr.find(';');

            while (end != std::string::npos) {
                std::string path = pathStr.substr(start, end - start);
                if (!path.empty()) {
                    searchPaths.push_back(path);
                }
                start = end + 1;
                end = pathStr.find(';', start);
            }

            if (start < pathStr.length()) {
                searchPaths.push_back(pathStr.substr(start));
            }

            free(pathEnv);
        }

        // Remove duplicates
        std::sort(searchPaths.begin(), searchPaths.end());
        searchPaths.erase(std::unique(searchPaths.begin(), searchPaths.end()), searchPaths.end());
    }

    std::pair<bool, std::string> FindDll(const std::string& dllName) {
        for (const auto& path : searchPaths) {
            std::string fullPath = path + "\\" + dllName;
            if (GetFileAttributesA(fullPath.c_str()) != INVALID_FILE_ATTRIBUTES) {
                return {true, fullPath};
            }
        }
        return {false, ""};
    }

    std::string GetSearchLocation(const std::string& fullPath) {
        // Determine which search location the DLL was found in
        if (fullPath.find(exeDirectory) == 0) {
            return "AppDir";
        }

        char systemDir[MAX_PATH];
        GetSystemDirectoryA(systemDir, MAX_PATH);
        if (fullPath.find(systemDir) == 0) {
            return "System32";
        }

        char windowsDir[MAX_PATH];
        GetWindowsDirectoryA(windowsDir, MAX_PATH);
        std::string sysWow64 = std::string(windowsDir) + "\\SysWOW64";
        if (fullPath.find(sysWow64) == 0) {
            return "SysWOW64";
        }

        if (fullPath.find(windowsDir) == 0) {
            return "WindowsDir";
        }

        return "PATH";
    }
};

void PrintHelp() {
    std::cout << "PE Dependency Analysis Tool v1.0\n";
    std::cout << "Usage: pe_analyzer.exe <PE file path>\n";
    std::cout << "Example: pe_analyzer.exe C:\\Windows\\System32\\notepad.exe\n";
}

int main(int argc, char* argv[]) {
    if (argc != 2) {
        PrintHelp();
        return 1;
    }

    std::string targetFile = argv[1];

    // Check if file exists
    if (GetFileAttributesA(targetFile.c_str()) == INVALID_FILE_ATTRIBUTES) {
        std::cerr << "Error: File not found - " << targetFile << std::endl;
        return 1;
    }

    PEAnalyzer analyzer;
    if (!analyzer.LoadFile(targetFile)) {
        return 1;
    }

    std::vector<std::string> dlls = analyzer.GetImportedDlls();

    if (dlls.empty()) {
        std::cout << "This PE file does not import any DLLs" << std::endl;
        return 0;
    }

    DllFinder finder;
    finder.InitSearchPaths(targetFile);

    for (const auto& dll : dlls) {
        auto [found, path] = finder.FindDll(dll);
        if (found)
        {
            std::string location = finder.GetSearchLocation(path);
            std::cout << "\t" << dll << " => " << location
                      << " (" << path << ")" << std::endl;
        }
        else
        {
            std::cout << "\t" << dll << " => not found" << std::endl;
        }
    }

    std::cout << std::string(80, '-') << std::endl;
    std::cout << "Total: " << dlls.size() << " DLL dependencies" << std::endl;

    return 0;
}
