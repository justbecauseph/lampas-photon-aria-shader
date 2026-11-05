/*
--------------------------------------------------------------------------------

  Photon Shader by SixthSurge

  program/c14_color_grading:
  Apply bloom, color grading and tone mapping then convert to rec. 709

--------------------------------------------------------------------------------
*/

#include "/include/global.glsl"

out vec2 uv;

// Frame-uniform values, computed once instead of per pixel
flat out float exposure;

#ifdef VIGNETTE
flat out float vignette_exponent;
#endif

#if GRADE_WHITE_BALANCE != 6500
flat out mat3 white_balance_matrix;
#endif

uniform sampler2D colortex5; // scene color, exposure in texel (0, 0) alpha

#ifdef VIGNETTE
uniform float blindness;
uniform float darknessFactor;
uniform float frameTimeCounter;

uniform float biome_cave;
#endif

#include "/include/post_processing/aces/utility.glsl"
#include "/include/utility/color.glsl"

void main() {
    uv = gl_MultiTexCoord0.xy;

    exposure = texelFetch(colortex5, ivec2(0), 0).a;

#ifdef VIGNETTE
    const float vignette_intensity = 0.08 * VIGNETTE_INTENSITY;

    float darkness_pulse = 1.0 - dampen(abs(cos(2.0 * frameTimeCounter)));

    vignette_exponent = vignette_intensity + 0.1 * biome_cave +
        0.3 * blindness + 0.2 * darkness_pulse * darknessFactor;
#endif

#if GRADE_WHITE_BALANCE != 6500
    vec3 src_xyz = blackbody(float(GRADE_WHITE_BALANCE)) * rec2020_to_xyz;
    vec3 dst_xyz = blackbody(6500.0) * rec2020_to_xyz;
    white_balance_matrix = get_chromatic_adaptation_matrix(src_xyz, dst_xyz);
#endif

    gl_Position = vec4(gl_Vertex.xy * 2.0 - 1.0, 0.0, 1.0);
}
