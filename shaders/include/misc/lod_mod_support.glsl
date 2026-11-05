#if !defined INCLUDE_MISC_LOD_MOD_SUPPORT
#define INCLUDE_MISC_LOD_MOD_SUPPORT

/*
 * Utility include for LoD mod support (Distant Horizons and Voxy)
 */

#if defined DISTANT_HORIZONS
// --------------------
//   Distant Horizons
// --------------------

uniform sampler2D colortex15;

uniform sampler2D dhDepthTex;
uniform sampler2D dhDepthTex1;
uniform mat4 dhProjection;
uniform mat4 dhProjectionInverse;
uniform mat4 dhPreviousProjection;
uniform mat4 dhModelView;
uniform mat4 dhModelViewInverse;
uniform float dhNearPlane;
uniform float dhFarPlane;
uniform int dhRenderDistance;

uniform float combined_near;
uniform float combined_far;

uniform vec4 combined_projection_matrix_0;
uniform vec4 combined_projection_matrix_1;
uniform vec4 combined_projection_matrix_2;
uniform vec4 combined_projection_matrix_3;

uniform vec4 combined_projection_matrix_inverse_0;
uniform vec4 combined_projection_matrix_inverse_1;
uniform vec4 combined_projection_matrix_inverse_2;
uniform vec4 combined_projection_matrix_inverse_3;

#define combined_depth_tex colortex15
#define lod_depth_tex dhDepthTex
#define lod_depth_tex_solid dhDepthTex1
#define lod_depth_tex_shading lod_depth_tex
#define lod_depth_tex_scale taau_render_scale
#define lod_projection_matrix dhProjection
#define lod_projection_matrix_inverse dhProjectionInverse
#define lod_previous_projection_matrix dhPreviousProjection
#define lod_render_distance dhRenderDistance
#define combined_projection_matrix \
    mat4( \
        combined_projection_matrix_0, \
        combined_projection_matrix_1, \
        combined_projection_matrix_2, \
        combined_projection_matrix_3 \
    )
#define combined_projection_matrix_inverse \
    mat4( \
        combined_projection_matrix_inverse_0, \
        combined_projection_matrix_inverse_1, \
        combined_projection_matrix_inverse_2, \
        combined_projection_matrix_inverse_3 \
    )
#elif defined VOXY
// --------
//   Voxy
// --------

uniform sampler2D colortex15;

uniform sampler2D vxDepthTexOpaque;
uniform sampler2D vxDepthTexTrans;
uniform mat4 vxProj;
uniform mat4 vxProjInv;
uniform mat4 vxProjPrev;
uniform int vxRenderDistance;

float combined_near = near;
float combined_far = float(16 * vxRenderDistance);

mat4 combined_projection_matrix = mat4(
    vec4(gbufferProjection[0][0], 0.0, 0.0, 0.0),
    vec4(0.0, gbufferProjection[1][1], 0.0, 0.0),
    vec4(
        gbufferProjection[2][0],
        gbufferProjection[2][1],
        (combined_far + combined_near) / (combined_near - combined_far),
        -1.0
    ),
    vec4(
        0.0,
        0.0,
        (2.0 * combined_far * combined_near) / (combined_near - combined_far),
        0.0
    )
);

mat4 combined_projection_matrix_inverse = mat4(
    vec4(gbufferProjectionInverse[0][0], 0.0, 0.0, 0.0),
    vec4(0.0, gbufferProjectionInverse[1][1], 0.0, 0.0),
    vec4(
        0.0,
        0.0,
        0.0,
        -(combined_far - combined_near) / (2.0 * combined_far * combined_near)
    ),
    vec4(
        gbufferProjectionInverse[3][0],
        gbufferProjectionInverse[3][1],
        -1.0,
        (combined_far + combined_near) / (2.0 * combined_far * combined_near)
    )
);

#define combined_depth_tex colortex15
#define lod_depth_tex vxDepthTexTrans
#define lod_depth_tex_solid vxDepthTexOpaque
#define lod_depth_tex_shading lod_depth_tex_solid
#define lod_depth_tex_scale 1.0
#define lod_projection_matrix vxProj
#define lod_projection_matrix_inverse vxProjInv
#define lod_previous_projection_matrix vxProjPrev
#define lod_render_distance (vxRenderDistance * 16)

// View-space distance of a vanilla (merged) depth value
float vanilla_view_depth(float depth) {
    vec2 zw = (depth * 2.0 - 1.0) * gbufferProjectionInverse[2].zw +
        gbufferProjectionInverse[3].zw;
    return -zw.x / zw.y;
}

// With excludeLodsFromVanillaDepth = false, Voxy reprojects its depth into
// vanilla depth with Minecraft's projection, whose far plane is
// max(4 * render distance, 16 * cloud range) blocks, and clamps it just in
// front of that plane. Every Voxy surface beyond it therefore has the same
// merged depth, so the merged depth can't be compared with the Voxy depth
// there. Vanilla geometry never reaches that far, so a Voxy surface whose
// merged depth lies near the far plane belongs to Voxy.
bool is_voxy_beyond_vanilla_far(float depth_world, float depth_voxy) {
    // The clamped depth lies at 0.996-0.9998 * far for far planes of
    // 128-2048 blocks; float depth resolution there is under 0.003 * far
    const float far_fraction = 0.99;

    return depth_voxy < 1.0 &&
        vanilla_view_depth(depth_world) >= far_fraction * vanilla_view_depth(1.0);
}
#else
#define combined_near near
#define combined_far far
#define combined_projection_matrix gbufferProjection
#define combined_projection_matrix_inverse gbufferProjectionInverse
#define combined_depth_tex depthtex1

#define sample_depth_texture texture
#endif

bool is_lod_terrain(float depth, float depth_lod) {
#if defined VOXY
    // Merged depth is never 1.0 under Voxy surfaces; beyond the vanilla far
    // plane it saturates instead (see is_voxy_beyond_vanilla_far)
    return depth_lod < 1.0 &&
        (depth >= 1.0 || is_voxy_beyond_vanilla_far(depth, depth_lod));
#else
    return depth >= 1.0 && depth_lod < 1.0;
#endif
}

#endif // INCLUDE_MISC_LOD_MOD_SUPPORT
