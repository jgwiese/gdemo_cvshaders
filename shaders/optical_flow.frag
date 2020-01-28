#version 330 core
const int filter_size = 3;
const float epsilon = 0.000000001;
const float pi = 3.1415926535897932384626433832795 + epsilon;
const float k[9] = float[](1, 2, 1, 2, 4, 2, 1, 2, 1);
//const float k[9] = float[](1, 1, 1, 1, 1, 1, 1, 1, 1);
//const float k[25] = float[](1, 2, 4, 2, 1, 2, 4, 8, 4, 2, 4, 8, 16, 8, 4, 2, 4, 8, 4, 2, 1, 2, 4, 2, 1);
//const float k[9] = float[](-1, -1, -1, -1, 8, -1, -1, -1, -1);
//const float k[9] = float[](-1, -2, -1, 0, 0, 0, +1, +2, +1);

uniform sampler2D gradient_t;
uniform sampler2D gradient_s_x;
uniform sampler2D gradient_s_y;
uniform int width;
uniform int height;

in vec2 uvs[filter_size * filter_size];
out vec4 color_out, data_out;

vec3 scale_back(vec3 gradient) {
    return (gradient * 2.0 - 1.0);
}

float rgb2gray(vec3 v) {
    return (v.x + v.y + v.z) / 3;
}

float valueFromTexture(sampler2D texture, vec2 uv, float lod) {
    vec2 tex_unit = vec2(1.0/width, 1.0/height);
    vec3 color = scale_back(textureLod(texture, uv, lod).rgb);
    color += scale_back(textureLod(texture, uv + vec2(-1, 0) * tex_unit, lod).rgb);
    color += scale_back(textureLod(texture, uv + vec2(1, 0) * tex_unit, lod).rgb);
    color += scale_back(textureLod(texture, uv + vec2(0, -1) * tex_unit, lod).rgb);
    color += scale_back(textureLod(texture, uv + vec2(0, 1) * tex_unit, lod).rgb);

    return rgb2gray(color/5);
}

vec3 hsv2rgb(vec3 c)
{
    vec4 K = vec4(1.0, 2.0 / 3.0, 1.0 / 3.0, 3.0);
    vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
    return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
}

void main() {
    float lod = 0;
    float k_sum = 0;

    float m11 = 0;
    float m12 = 0;
    float m22 = 0;
    float q1 = 0;
    float q2 = 0;

    for (int i = 0; i < filter_size * filter_size; i++) {
        m11 += valueFromTexture(gradient_s_x, uvs[i], lod) * valueFromTexture(gradient_s_x, uvs[i], lod) * k[i];
        m12 += valueFromTexture(gradient_s_x, uvs[i], lod) * valueFromTexture(gradient_s_y, uvs[i], lod) * k[i];
        m22 += valueFromTexture(gradient_s_y, uvs[i], lod) * valueFromTexture(gradient_s_y, uvs[i], lod) * k[i];

        q1 += valueFromTexture(gradient_t, uvs[i], lod) * valueFromTexture(gradient_s_x, uvs[i], lod) * k[i];
        q2 += valueFromTexture(gradient_t, uvs[i], lod) * valueFromTexture(gradient_s_y, uvs[i], lod) * k[i];

        k_sum += k[i];
    }

    if (k_sum > epsilon) {
        m11 /= k_sum;
        m12 /= k_sum;
        m22 /= k_sum;
        q1 /= k_sum;
        q2 /= k_sum;
    }
    float vx = (m22 * q1 - m12 * q2) / (m12 * m12 - m11 * m22 + epsilon);
    float vy = (m11 * q2 - m12 * q1) / (m12 * m12 - m11 * m22 + epsilon);
    float r = sqrt(vx * vx + vy * vy);
    float angle = atan(vy, vx);
    angle = angle / 2 / pi;

    vec3 hsv = vec3(angle, 1.0, clamp(r, 0, 1));
    vec3 rgb = hsv2rgb(hsv);

    color_out = vec4(rgb, 1.0);
    data_out = vec4(vx, vy, r, angle);
}