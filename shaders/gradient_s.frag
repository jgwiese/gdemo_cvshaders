#version 330 core

uniform sampler2D scene;
uniform int width;
uniform int height;

in vec2 uv;

out vec4 color_0, color_1;

void main() {
    float lod = 0;
    vec3 gradient_x = 0.5 * (textureLod(scene, uv + vec2(1, 0) / width, lod) - textureLod(scene, uv - vec2(1, 0) / width, lod)).xyz;
    vec3 gradient_y = 0.5 * (textureLod(scene, uv + vec2(0, 1) / height, lod) - textureLod(scene, uv - vec2(0, 1) / height, lod)).xyz;
    gradient_x = (gradient_x + 1) / 2;
    gradient_y = (gradient_y + 1) / 2;

    color_0 = vec4(gradient_x, 1.0);
    color_1 = vec4(gradient_y, 1.0);
}
