#version 330

in layout(location = 0) vec2 position;
in layout(location = 1) vec4 color_in;

out vec4 color;

void main()
{
    gl_Position = vec4(position, 0.0f, 1.0f);
    color = color_in;
}
