#if !defined INCLUDE_FOG_VL_BUFFER
#define INCLUDE_FOG_VL_BUFFER

// The volumetric fog buffers (colortex6 transmittance, colortex7 scattering)
// are always half resolution, because colortex6 also holds the AO history.
// c0_vl renders into the lower-left vl_buffer_scale of them.
const float vl_buffer_scale = VL_RENDER_SCALE / 0.5;

// Clamps a fog buffer coordinate to half a texel inside the region c0_vl
// writes, so bilinear filtering never reads texels outside it
vec2 vl_buffer_clamp(vec2 coord, vec2 buffer_res) {
    if (vl_buffer_scale < 1.0) {
        vec2 region = floor(buffer_res * vl_buffer_scale);
        coord = clamp(coord, 0.5 / buffer_res, (region - 0.5) / buffer_res);
    }
    return coord;
}

// Fog buffer coordinate of a screen uv
vec2 vl_buffer_coord(vec2 uv, vec2 buffer_res) {
    return vl_buffer_clamp(uv * vl_buffer_scale, buffer_res);
}

#endif // INCLUDE_FOG_VL_BUFFER
