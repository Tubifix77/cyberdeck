shader_type canvas_item;

// Wall state driven from GDScript
uniform float intensity : hint_range(0.0, 1.0) = 0.0;
uniform vec3 color_idle : source_color = vec3(0.1, 0.2, 0.8);
uniform vec3 color_blocked : source_color = vec3(0.9, 0.5, 0.1);
uniform vec3 color_storm : source_color = vec3(1.0, 0.15, 0.05);
uniform float pulse : hint_range(0.0, 1.0) = 0.0;

// Noise function for organic flame movement
float hash(vec2 p) {
    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    float a = hash(i);
    float b = hash(i + vec2(1.0, 0.0));
    float c = hash(i + vec2(0.0, 1.0));
    float d = hash(i + vec2(1.0, 1.0));
    return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

float fbm(vec2 p) {
    float v = 0.0;
    float a = 0.5;
    for (int i = 0; i < 4; i++) {
        v += a * noise(p);
        p *= 2.0;
        a *= 0.5;
    }
    return v;
}

void fragment() {
    vec2 uv = UV;

    // Edge glow — strongest at screen edges, fading toward center
    float edge_x = min(uv.x, 1.0 - uv.x) * 2.0;
    float edge_y = min(uv.y, 1.0 - uv.y) * 2.0;
    float edge = 1.0 - min(edge_x, edge_y);
    edge = smoothstep(0.6, 1.0, edge);

    // Animated flame noise
    float t = TIME * 0.8;
    vec2 flame_uv = uv * vec2(6.0, 3.0) + vec2(t * 0.3, -t * 0.7);
    float flame = fbm(flame_uv);
    flame = smoothstep(0.3, 0.7, flame);

    // Combine edge mask with flame
    float wall = edge * flame;

    // Color blend based on intensity
    vec3 col = mix(color_idle, color_blocked, intensity);
    col = mix(col, color_storm, smoothstep(0.7, 1.0, intensity));

    // Pulse flash on blocked events
    float flash = pulse * sin(TIME * 12.0) * 0.5 + 0.5;
    col += vec3(flash * pulse * 0.3);

    // Final alpha — base visibility scales with intensity
    float base_alpha = mix(0.05, 0.6, intensity);
    float alpha = wall * base_alpha;

    COLOR = vec4(col, alpha);
}