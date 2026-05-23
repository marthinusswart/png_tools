// clang-format off
// Legend:
// +------+------------+
// | Code | Type       |
// +------+------------+
// |   0  | Path       |
// |   1  | Wall       |
// |   2  | Power Pill |
// |   3  | Ghost Base |
// |   9  | Other      |
// +------+------------+
UBYTE mapping_alphanumeric[100] = {
    1, 1, 1, 1, 1, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0
};
// clang-format on

/*
 * Runtime Binary Loading Example
 * ------------------------------
 * #include <stdio.h>
 * 
 * // Allocate the array once (100 bytes)
 * UBYTE current_stage_map[100];
 * 
 * // Call this when you want to load a level
 * void load_stage(const char* filepath) {
 *     FILE *file = fopen(filepath, "rb");
 *     if (file != NULL) {
 *         // Read 100 bytes directly into the array
 *         fread(current_stage_map, sizeof(UBYTE), 100, file);
 *         fclose(file);
 *     } else {
 *         printf("Failed to load stage map: %s\n", filepath);
 *     }
 * }
 * 
 * // Usage Example:
 * // load_stage("collision/alphanumeric.bin");
 */
