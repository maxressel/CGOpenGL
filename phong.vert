#version 330

layout (location=0) in vec3 v_position;
layout (location=1) in vec3 v_normal;

uniform mat4 modelview_projection_matrix;
uniform mat4 modelview_matrix;
uniform mat3 normal_matrix;

out vec3 frag_pos;
out vec3 frag_normal;

void main()
{
    frag_pos = vec3(modelview_matrix * vec4(v_position,1));
    frag_normal = normalize(normal_matrix * v_normal);

    gl_Position = modelview_projection_matrix * vec4(v_position,1);
}
