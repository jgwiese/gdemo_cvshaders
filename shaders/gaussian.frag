#version 330 core

const int filter_size = 3;
//float k[9] = float[](1, 2, 1, 2, 4, 2, 1, 2, 1);
//const float k[9] = float[](1, 1, 1, 1, 1, 1, 1, 1, 1);
//const float k[25] = float[](1, 2, 4, 2, 1, 2, 4, 8, 4, 2, 4, 8, 16, 8, 4, 2, 4, 8, 4, 2, 1, 2, 4, 2, 1);

uniform sampler2D scene;

in vec2 uvs[filter_size*filter_size];
out vec4 color_0;

void main() {
    vec3 color = vec3(0);

    for (int i = 0; i < filter_size*filter_size; i++) {
        color += texture(scene, uvs[i]).xyz;
    }
    color /= (filter_size * filter_size);

    color_0 = vec4(color, 1.0);
}
