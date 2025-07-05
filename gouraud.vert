#version 330

layout (location=0) in vec3 v_position;
layout (location=1) in vec3 v_normal;

uniform mat4 modelview_projection_matrix;
uniform mat4 modelview_matrix;
uniform mat3 normal_matrix;
uniform float shininess;

out vec3 v_color;

void main()
{
    vec3 normal = normalize(normal_matrix * v_normal);
    vec3 lightDir = normalize(vec3(0.5, 0.5, 1.0)); 
    vec3 eyePos = vec3(modelview_matrix * vec4(v_position,1));

    float diff = max(dot(normal, lightDir), 0.0);

    vec3 materialDiffuse = vec3(0.4, 0.4, 0.8);
    vec3 materialSpecular = vec3(1.0);
    vec3 ambient = 0.1 * materialDiffuse;

    vec3 diffuse = diff * materialDiffuse;

    vec3 viewDir = normalize(-eyePos);
    vec3 reflectDir = reflect(-lightDir, normal);

    float spec = pow(max(dot(viewDir, reflectDir), 0.0), shininess);
    vec3 specular = spec * materialSpecular;

    v_color = ambient + diffuse + specular;

    gl_Position = modelview_projection_matrix * vec4(v_position,1);
}
