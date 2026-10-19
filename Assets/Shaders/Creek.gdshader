shader_type spatial;
render_mode cull_disabled;

void fragment() {
    float ripple = sin(UV.y * 95.0 - TIME * 2.0 + sin(UV.x * 17.0))
                 * sin(UV.x * 33.0 + UV.y * 28.0 + TIME * 0.7);
    float glint = smoothstep(0.72, 1.0, ripple);
    ALBEDO = mix(vec3(0.035, 0.23, 0.28), vec3(0.21, 0.56, 0.57), glint * 0.65);
    ROUGHNESS = 0.28;
    METALLIC = 0.12;
    NORMAL_MAP = normalize(vec3(ripple * 0.08 + 0.5, 0.5, 1.0));
}
