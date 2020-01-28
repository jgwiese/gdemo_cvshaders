#version 330 core

layout (location = 0) in vec3 position_in;
layout (location = 1) in vec2 uv_in;

uniform mat4 modelMatrix;

out vec2 uv;

void main() {
    gl_Position = modelMatrix * vec4(position_in, 1.0);
    //gl_Position = vec4(position_in, 1.0);
    uv = uv_in;
}
