#if !defined INCLUDE_SURFACE_WATER_DETAIL
#define INCLUDE_SURFACE_WATER_DETAIL

float water_detail_weight(vec3 world_pos) {
#if WATER_DETAIL_DISTANCE > 0
    return 1.0 - smoothstep(
        0.5 * float(WATER_DETAIL_DISTANCE),
        float(WATER_DETAIL_DISTANCE),
        length(world_pos - cameraPosition)
    );
#else
    return 1.0;
#endif
}

#endif // INCLUDE_SURFACE_WATER_DETAIL
