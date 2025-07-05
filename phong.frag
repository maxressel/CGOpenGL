#version 330

in vec3 frag_pos;
in vec3 frag_normal;

uniform float shininess;

out vec4 f_color;

void main()
{
    vec3 normal = normalize(frag_normal);
    vec3 lightDir = normalize(vec3(0.5, 0.5, 1.0)); 

    float diff = max(dot(normal, lightDir), 0.0);

    vec3 materialDiffuse = vec3(0.4, 0.4, 0.8);
    vec3 materialSpecular = vec3(1.0);
    vec3 ambient = 0.1 * materialDiffuse;

    vec3 diffuse = diff * materialDiffuse;

    vec3 viewDir = normalize(-frag_pos);
    vec3 reflectDir = reflect(-lightDir, normal);

    float spec = pow(max(dot(viewDir, reflectDir), 0.0), shininess);
    vec3 specular = spec * materialSpecular;

    vec3 color = ambient + diffuse + specular;

    f_color = vec4(color,1);
}
