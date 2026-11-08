
#include <stdio.h>

#define WIN32_LEAN_AND_MEAN
#include <Windows.h>

// Callback for receiving installation instances
typedef void (*instance_callback)(const wchar_t* version, const wchar_t* path);

extern int
get_vs_installations(instance_callback callback);


typedef struct ISetupInstanceVTable ISetupInstanceVTable;
typedef struct ISetupInstance ISetupInstance;

typedef struct IEnumSetupInstancesVTable IEnumSetupInstancesVTable;
typedef struct IEnumSetupInstances IEnumSetupInstances;

typedef struct ISetupConfigurationVTable ISetupConfigurationVTable;
typedef struct ISetupConfiguration ISetupConfiguration;

typedef HRESULT (__stdcall* QueryInterfaceFn)(void* this, REFIID riid, void** object);
typedef ULONG (__stdcall* AddRefFn)(void* this);
typedef ULONG (__stdcall* ReleaseFn)(void* this);

#define DECLARE_IUNKNOWN \
	QueryInterfaceFn QueryInterface; \
	AddRefFn AddRef; \
	ReleaseFn Release

typedef HRESULT (__stdcall* GetInstanceIdFn)(
	ISetupInstance* instance,
	wchar_t** id);

typedef HRESULT (__stdcall* GetInstallDateFn)(
	ISetupInstance* instance,
	LPFILETIME date);

typedef HRESULT (__stdcall* GetInstallationNameFn)(
	ISetupInstance* instance,
	wchar_t** name);

typedef HRESULT (__stdcall* GetInstallationPathFn)(
	ISetupInstance* instance,
	wchar_t** path);

typedef HRESULT (__stdcall* GetInstallationVersionFn)(
	ISetupInstance* instance,
	wchar_t** version);

typedef HRESULT (__stdcall* GetDisplayNameFn)(
	ISetupInstance* instance,
	LCID id,
	wchar_t** name);

typedef HRESULT (__stdcall* GetDescriptionFn)(
	ISetupInstance* instance,
	LCID id,
	wchar_t** description);

typedef HRESULT (__stdcall* ResolvePathFn)(
	ISetupInstance* instance,
	const wchar_t* relative_path,
	wchar_t** absolute_path);

struct ISetupInstanceVTable {
	DECLARE_IUNKNOWN;

	GetInstanceIdFn GetInstanceId;
	GetInstallDateFn GetInstallDate;
	GetInstallationNameFn GetInstallationName;
	GetInstallationPathFn GetInstallationPath;
	GetInstallationVersionFn GetInstallationVersion;
	GetDisplayNameFn GetDisplayName;
	GetDescriptionFn GetDescription;
	ResolvePathFn ResolvePath;
};

struct ISetupInstance {
	ISetupInstanceVTable* vtable;
};

typedef HRESULT (__stdcall* NextFn)(
	IEnumSetupInstances* instance,
	ULONG num,
	ISetupInstance** setup,
	ULONG* fetched);

typedef HRESULT (__stdcall* SkipFn)(
	IEnumSetupInstances* instance,
	ULONG num);

typedef HRESULT (__stdcall* ResetFn)(
	IEnumSetupInstances* instance);

typedef HRESULT (__stdcall* CloneFn)(
	IEnumSetupInstances* instance,
	IEnumSetupInstances** instances
	);

struct IEnumSetupInstancesVTable {
	DECLARE_IUNKNOWN;

	NextFn Next;
	SkipFn Skip;
	ResetFn Reset;
	CloneFn Clone;
};

struct IEnumSetupInstances {
	IEnumSetupInstancesVTable* vtable;
};

typedef HRESULT(__stdcall* EnumInstancesFn)(
	ISetupConfiguration* configuration,
	IEnumSetupInstances** instances);

struct ISetupConfigurationVTable {
	DECLARE_IUNKNOWN;

	EnumInstancesFn EnumInstances;
	void* GetInstanceForCurrentProcess;
	void* GetInstanceForPath;
};

typedef struct ISetupConfiguration {
	ISetupConfigurationVTable* vtable;
} ISetupConfiguration;

typedef HRESULT(__stdcall* GetSetupConfigurationFn)(
	ISetupConfiguration** configuration,
	void* reserved);

static size_t
environment_variable(const char* variable, char* value, size_t capacity) {
	unsigned int required;
	if ((required = GetEnvironmentVariableA(variable, value, (unsigned int)capacity)) > capacity)
		return 0;
	return (required > 0) ? required : 0;
}

static size_t
get_library_path(char* path, size_t capacity) {
#if defined( __x86_64__ ) ||  defined( __x86_64 ) || defined( __amd64 ) || defined( _M_AMD64 ) || defined( _AMD64_ )
	const char subpath[] = "\\Microsoft\\VisualStudio\\Setup\\x64\\Microsoft.VisualStudio.Setup.Configuration.Native.dll\0";
#else
	const char subpath[] = "\\Microsoft\\VisualStudio\\Setup\\x86\\Microsoft.VisualStudio.Setup.Configuration.Native.dll\0";
#endif
	size_t path_length = environment_variable("ProgramData", path, capacity);
	size_t subpath_length = sizeof(subpath);
	if (!path_length || (path_length + subpath_length) > capacity)
		return 0;

	memcpy(path + path_length, subpath, subpath_length);
	return path_length + subpath_length;
}


int
get_vs_installations(instance_callback callback) {
	HMODULE lib = 0;
	int result = -1;

	char lib_path[512];
	size_t path_length = get_library_path(lib_path, sizeof(lib_path));
	if (!path_length) {
		printf("ERROR: Unable to get VisualStudio Setup Configuration library path\n");
		goto cleanup;
	}

	lib = LoadLibraryA(lib_path);
	if (!lib) {
		printf("ERROR: Unable to load VisualStudio Setup Configuration library\n");
		goto cleanup;
	}

	GetSetupConfigurationFn get_setup_configuration = (GetSetupConfigurationFn)GetProcAddress(lib, "GetSetupConfiguration");
	if (!get_setup_configuration) {
		printf("ERROR: Unable to get VisualStudio Setup Configuration entry point\n");
		goto cleanup;
	}

	ISetupConfiguration* configuration = 0;
	HRESULT code = get_setup_configuration(&configuration, 0);
	if (code != S_OK) {
		printf("ERROR: GetSetupConfiguration call failed (0x%08lx)\n", code);
		goto cleanup;
	}

	IEnumSetupInstances* enum_instances = 0;
	code = configuration->vtable->EnumInstances(configuration, &enum_instances);
	if (code != S_OK) {
		printf("ERROR: EnumInstances call failed (0x%08lx)\n", code);
		goto cleanup;
	}

	result = 0;
	while (enum_instances) {
		ULONG fetched = 0;
		ISetupInstance* setup_instance = 0;
		code = enum_instances->vtable->Next(enum_instances, 1, &setup_instance, &fetched);
		if ((code == S_FALSE) || !fetched)
			break;
		if (code != S_OK) {
			printf("ERROR: While enumerating instances, Next call failed (0x%08lx)\n", code);
			goto cleanup;
		}

		wchar_t* version = 0;
		wchar_t* path = 0;
		code = setup_instance->vtable->GetInstallationVersion(setup_instance, &version);
		if (code == S_OK)
			code = setup_instance->vtable->GetInstallationPath(setup_instance, &path);
		if (code == S_OK)
			printf("%ls %ls\n", version, path);
	}

cleanup:

	if (lib)
		FreeLibrary(lib);

	return result;
}

#ifdef COMPILE_TOOL

static void
print_callback(const wchar_t* version, const wchar_t* path) {
	printf("%ls %ls\n", version, path);
}

int
main(int argc, char** argv) {
	(void)sizeof(argc);
	(void)sizeof(argv);

	return get_vs_installations(print_callback);
}

#endif
