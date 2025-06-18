#include <stdio.h>
#include <stdlib.h>
#include <cjson/cJSON.h>

// Create a monitor with a list of supported resolutions
// Note: Returns a heap-allocated string; you need to free it after use.
char *create_monitor(void) {
    const unsigned int resolution_numbers[3][2] = {
        {1280, 720},
        {1920, 1080},
        {3840, 2160}
    };
    char *string = NULL;
    cJSON *name = NULL;
    cJSON *resolutions = NULL;
    cJSON *resolution = NULL;
    cJSON *width = NULL;
    cJSON *height = NULL;
    size_t index = 0;

    // Create the root object monitor
    cJSON *monitor = cJSON_CreateObject();
    if (monitor == NULL) {
        goto end;
    }

    // Create name attribute
    name = cJSON_CreateString("Awesome 4K");
    if (name == NULL) {
        goto end;
    }
    cJSON_AddItemToObject(monitor, "name", name);

    // Create resolutions array
    resolutions = cJSON_CreateArray();
    if (resolutions == NULL) {
        goto end;
    }
    cJSON_AddItemToObject(monitor, "resolutions", resolutions);

    // Create each resolution object and add it to the array
    for (index = 0; index < (sizeof(resolution_numbers) / (2 * sizeof(int))); ++index) {
        resolution = cJSON_CreateObject();
        if (resolution == NULL) {
            goto end;
        }
        cJSON_AddItemToArray(resolutions, resolution);

        // Create and add width
        width = cJSON_CreateNumber(resolution_numbers[index][0]);
        if (width == NULL) {
            goto end;
        }
        cJSON_AddItemToObject(resolution, "width", width);

        // Create and add height
        height = cJSON_CreateNumber(resolution_numbers[index][1]);
        if (height == NULL) {
            goto end;
        }
        cJSON_AddItemToObject(resolution, "height", height);
    }

    // Print JSON string
    string = cJSON_Print(monitor);
    if (string == NULL) {
        fprintf(stderr, "Failed to print monitor.\n");
    }

end:
    cJSON_Delete(monitor);  // Free the created monitor object
    return string;          // Return the JSON string
}

int main() {
    char *monitor_json = create_monitor();
    if (monitor_json != NULL) {
        printf("Monitor JSON:\n%s\n", monitor_json);
        free(monitor_json);  // Free the JSON string
    }
    return 0;
}