#version 330 core

in vec2 uv;

uniform sampler2D scene;

out vec4 color_out_0;

void main() {
    color_out_0 = textureLod(scene, uv, 0);
}
