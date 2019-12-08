#version 330

in vec2 textures;
in vec3 fragment_normal;
in vec3 fragment_pos;

out vec4 color;
uniform sampler2D tex_sampler;

struct DirectionalLight {
  vec3 direction;

  vec3 color;
  float ambientIntensity;
  float diffuseIntensity;
  float specularIntensity; // for debug purposes, should be set to 1.0
};

//uniform vec3 camera_position;
vec3 camera_position = vec3(0.0, 0.0, 0.0);
//uniform float materialSpecularFactor; // should be >= 1.0
float materialSpecularFactor = 32.0;
//uniform float materialSpecularIntensity;
float materialSpecularIntensity = 1.0;
//uniform vec3 materialEmission;
vec3 materialEmission = vec3(0.0, 0.0, 0.0);
uniform DirectionalLight directionalLight;

vec4 calcDirectionalLight(vec3 normal, vec3 fragmentToCamera, DirectionalLight light) {
  vec4 ambientColor = vec4(light.color, 1) * light.ambientIntensity;

  float diffuseFactor = max(0.0, dot(normal, -light.direction));
  vec4 diffuseColor = vec4(light.color, 1) * light.diffuseIntensity * diffuseFactor;

  vec3 lightReflect = normalize(reflect(light.direction, normal));
  float specularFactor = pow(max(0.0, dot(fragmentToCamera, lightReflect)), materialSpecularFactor);
  vec4 specularColor = light.specularIntensity * vec4(light.color, 1) * materialSpecularIntensity * specularFactor;

  return ambientColor + diffuseColor + specularColor;
}

void main()
{
    //color = texture(tex_sampler, textures);
    vec3 normal = normalize(fragment_normal); // normal should be corrected after interpolation
    vec3 fragmentToCamera = normalize(camera_position - fragment_pos);

    vec4 directColor = calcDirectionalLight(normal, fragmentToCamera, directionalLight);
    vec4 linearColor = texture(tex_sampler, textures) * (vec4(materialEmission, 1) + directColor);

    vec4 gamma = vec4(vec3(1.0/2.2), 1);
    color = pow(linearColor, gamma); // gamma-corrected color
}