#version 330 core

uniform sampler2D scene;
uniform sampler2D scene_previous;

in vec2 uv;
out vec4 color_0;

void main() {
    float lod = 0;
    vec3 gradient_t = textureLod(scene, uv, lod).xyz - textureLod(scene_previous, uv, lod).xyz;
    gradient_t = (gradient_t + 1) / 2;

    color_0 = vec4(gradient_t, 1.0);
}
