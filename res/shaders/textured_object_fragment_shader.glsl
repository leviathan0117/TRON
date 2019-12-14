#version 330

in vec2 textures;
in vec3 fragment_normal;
in vec3 fragment_pos;
in vec4 FragPosLightSpace;

out vec4 color;
uniform sampler2D tex_sampler;
uniform sampler2D shadowMap;

struct DirectionalLight {
  vec3 direction;

  vec3 color;
  float ambientIntensity;
  float diffuseIntensity;
  float specularIntensity; // for debug purposes, should be set to 1.0
};

uniform vec3 camera_position;
//uniform float materialSpecularFactor; // should be >= 1.0
float materialSpecularFactor = 32.0;
//uniform float materialSpecularIntensity;
float materialSpecularIntensity = 1.0;
//uniform vec3 materialEmission;
vec3 materialEmission = vec3(0.0, 0.0, 0.0);
uniform DirectionalLight directionalLight;

//interpolated fragment normal:
vec3 normal;

vec4 calcDirectionalLight(vec3 normal, vec3 fragmentToCamera, DirectionalLight light)
{
    vec4 ambientColor = vec4(light.color, 1) * light.ambientIntensity;

    float diffuseFactor = max(0.0, dot(normal, -light.direction));
    vec4 diffuseColor = vec4(light.color, 1) * light.diffuseIntensity * diffuseFactor;

    vec3 lightReflect = normalize(reflect(light.direction, normal));
    float specularFactor = pow(max(0.0, dot(fragmentToCamera, lightReflect)), materialSpecularFactor);
    vec4 specularColor = light.specularIntensity * vec4(light.color, 1) * materialSpecularIntensity * specularFactor;

    // perform perspective divide
    vec3 projCoords = FragPosLightSpace.xyz / FragPosLightSpace.w;
    // transform to [0,1] range
    projCoords = projCoords * 0.5 + 0.5;
    // get closest depth value from light's perspective (using [0,1] range fragPosLight as coords)
    float closestDepth = texture(shadowMap, projCoords.xy).r;
    // get depth of current fragment from light's perspective
    float currentDepth = projCoords.z;
    // check whether current frag pos is in shadow
    float bias = 0.005;
    float shadow = currentDepth - bias > closestDepth  ? 1.0 : 0.0;

    return ambientColor + (1.0 - shadow) * (diffuseColor + specularColor);
}

void main()
{
    //color = texture(tex_sampler, textures);
    normal = normalize(fragment_normal); // normal should be corrected after interpolation
    vec3 fragmentToCamera = normalize(camera_position - fragment_pos);

    vec4 directColor = calcDirectionalLight(normal, fragmentToCamera, directionalLight);
    vec4 linearColor = texture(tex_sampler, textures) * (vec4(materialEmission, 1) + directColor);

    vec4 gamma = vec4(vec3(1.0/2.2), 1);
    color = pow(linearColor, gamma); // gamma-corrected color
}