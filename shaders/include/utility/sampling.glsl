#if !defined INCLUDE_UTILITY_SAMPLING
#define INCLUDE_UTILITY_SAMPLING

vec2 vogel_disc_sample(int step_index, int step_count, float rotation) {
    const float golden_angle = 2.4;

    float r = sqrt(step_index + 0.5) / sqrt(float(step_count));
    float theta = step_index * golden_angle + rotation;

    return r * vec2(cos(theta), sin(theta));
}

// Same points as vogel_disc_sample(), without per-sample trigonometry.
// Initialize dir to vec2(cos(rotation), sin(rotation)) and call this once for
// each step_index in increasing order, starting at 0.
vec2 vogel_disc_sample_incremental(
    int step_index,
    float rcp_sqrt_step_count,
    inout vec2 dir
) {
    const float golden_angle = 2.4;
    const mat2 golden_rotation = mat2(
        cos(golden_angle),
        sin(golden_angle),
        -sin(golden_angle),
        cos(golden_angle)
    );

    float r = sqrt(float(step_index) + 0.5) * rcp_sqrt_step_count;
    vec2 sample_pos = r * dir;
    dir = golden_rotation * dir;

    return sample_pos;
}

vec3 uniform_sphere_sample(vec2 hash) {
    hash.x *= tau;
    hash.y = 2.0 * hash.y - 1.0;
    return vec3(
        vec2(sin(hash.x), cos(hash.x)) * sqrt(1.0 - hash.y * hash.y),
        hash.y
    );
}

vec3 uniform_hemisphere_sample(vec3 vector, vec2 hash) {
    vec3 dir = uniform_sphere_sample(hash);
    return dot(dir, vector) < 0.0 ? -dir : dir;
}

// https://amietia.com/lambertnotangent.html
vec3 cosine_weighted_hemisphere_sample(vec3 vector, vec2 hash) {
    vec3 dir = normalize(uniform_sphere_sample(hash) + vector);
    return dot(dir, vector) < 0.0 ? -dir : dir;
}

#endif // INCLUDE_UTILITY_SAMPLING
