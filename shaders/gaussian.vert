#version 330 core

layout (location = 0) in vec3 position_in;
layout (location = 1) in vec2 uv_in;

const int filter_size = 3;

uniform int width;
uniform int height;
uniform mat4 modelMatrix;

out vec2 uvs[filter_size * filter_size];

void main() {
    gl_Position = modelMatrix * vec4(position_in, 1.0);

    vec2 tex_unit = vec2(1.0 / width, 1.0 / height);
    int range = filter_size / 2;

    int i;
    for (int y = -range; y <= range; y++) {
        for (int x = -range; x <= range; x++) {
            i = (y + range) * filter_size + (x + range);
            uvs[i] = uv_in + vec2(x, y) * tex_unit * 1;
        }
    }
}