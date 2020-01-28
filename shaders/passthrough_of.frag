#version 330 core

in vec2 uv;

uniform sampler2D color_in;
uniform sampler2D data_in;

out vec4 color_out, data_out;

void main() {
    float lod = 4;
    //color_out = vec4(vec3(textureLod(color_in, uv, lod)), lod);
    //data_out = vec4(vec3(textureLod(data_in, uv, lod)), lod);

    vec4 high_res_color = textureLod(color_in, uv, 0);
    vec4 low_res_color = textureLod(color_in, uv, lod);

    vec4 high_res_data = textureLod(data_in, uv, 0);
    vec4 low_res_data = textureLod(data_in, uv, lod);

    color_out = low_res_color;
    data_out = low_res_data;
}
