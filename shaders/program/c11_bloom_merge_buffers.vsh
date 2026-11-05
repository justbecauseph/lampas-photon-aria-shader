/*
--------------------------------------------------------------------------------

  Photon Shader by SixthSurge

  program/c11_bloom_merge_buffers:
  Copy bloom tiles from read buffer to write buffer

--------------------------------------------------------------------------------
*/

#include "/include/global.glsl"

out vec2 uv;

uniform vec2 view_pixel_size;

void main() {
    // Only cover the odd bloom tiles (x >= 0.5, y >= 0.75). The 2-pixel margin
    // below y = 0.75 keeps copying the row under each tile that the bloom
    // composite's bilinear lookup reads and the blur passes do not write.
    const vec2 rect_max = vec2(1.0);
    vec2 rect_min = vec2(0.5, 0.75 - 2.0 * view_pixel_size.y);

    vec2 vertex_pos = mix(rect_min, rect_max, gl_Vertex.xy);
    uv = vertex_pos;

    gl_Position = vec4(vertex_pos * 2.0 - 1.0, 0.0, 1.0);
}
