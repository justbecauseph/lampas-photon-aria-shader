#if !defined INCLUDE_MISC_VOXY_MERGED_DEPTH
#define INCLUDE_MISC_VOXY_MERGED_DEPTH

#if defined VOXY

/*
 * Determines whether a surface is owned by Voxy when Voxy depth is merged
 * into vanilla depth buffers (excludeLodsFromVanillaDepth = false).
 */
bool is_voxy_surface(float depth_world, float depth_voxy) {
    if (depth_voxy >= 1.0) {
        return false;
    }

    if (depth_world >= 1.0) {
        return true;
    }

    float z_world = screen_to_view_space_depth(
        gbufferProjectionInverse,
        depth_world
    );
    float z_voxy = screen_to_view_space_depth(
        lod_projection_matrix_inverse,
        depth_voxy
    );

    float epsilon = max(0.001 * z_voxy, 0.1);
    return z_voxy <= z_world + epsilon;
}

#endif // VOXY

#endif // INCLUDE_MISC_VOXY_MERGED_DEPTH
