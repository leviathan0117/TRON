#version 330

const int MAX_LIGHTS = 10;

in layout(location = 0) vec3 position;
in layout(location = 1) vec2 texture_cords;
in layout(location = 2) vec3 normals;
in layout(location = 3) vec3 part_offset;
in layout(location = 4) vec3 part_rotation;
in layout(location = 5) float part_resize;
in layout(location = 6) vec3 offset;
in layout(location = 7) vec3 rotation;
in layout(location = 8) float resize;

uniform mat4 view;
uniform mat4 projection;
uniform mat4 view_light[MAX_LIGHTS];
uniform mat4 projection_light[MAX_LIGHTS];

out vec2 textures;
out vec3 fragment_normal;
out vec3 fragment_pos;

out vec4 FragPosLightSpace[MAX_LIGHTS];

mat3 getRotationMatrix(float pitch_angle, float yaw_angle, float roll_angle)
{
    float yaw_sin = sin(yaw_angle);
    float yaw_cos = cos(yaw_angle);

    float pitch_sin = sin(pitch_angle);
    float pitch_cos = cos(pitch_angle);

    float roll_sin = sin(roll_angle);
    float roll_cos = cos(roll_angle);


    mat3 yaw_matrix = mat3(yaw_cos, -yaw_sin, 0,
                           yaw_sin, yaw_cos,  0,
                           0,       0,        1);

    mat3 pitch_matrix = mat3(pitch_cos,  0, pitch_sin,
                             0,          1, 0,
                             -pitch_sin, 0, pitch_cos);

    mat3 roll_matrix = mat3(1, 0,        0,
                            0, roll_cos, -roll_sin,
                            0, roll_sin, roll_cos);


    return roll_matrix * yaw_matrix * pitch_matrix;
}

void main()
{
    mat3 mr = getRotationMatrix(rotation.x, rotation.y, rotation.z);
    mat3 mr_part = getRotationMatrix(part_rotation.x, part_rotation.y, part_rotation.z);
    vec3 object_pos = vec3(position.x * resize, position.y * resize, position.z * resize) * mr_part * mr;
    vec3 world_pos = vec3(object_pos.x + offset.x, object_pos.y + offset.y, object_pos.z + offset.z);
    gl_Position =  projection * view * vec4(world_pos, 1.0f);
    for (int i = 0; i < MAX_LIGHTS; i++)
    {
        FragPosLightSpace[i] = projection_light[i] * view_light[i] * vec4(world_pos, 1.0);
    }

    fragment_normal = normals * mr;
    fragment_pos = world_pos;

    textures = vec2(texture_cords.x, 1 - texture_cords.y);
}