from OpenGL.GL import *
import OpenGL.GL.shaders

class TronShader:
    def __init__(self):
        self.shader = None
        self.view_uniform_location = None
        self.projection_uniform_location = None

    def compile_shader(self, vertex_shader_location, fragment_shader_location):
        vertex_shader_sourcecode = self.load_shader(vertex_shader_location)
        fragment_shader_sourcecode = self.load_shader(fragment_shader_location)

        self.shader = OpenGL.GL.shaders.compileProgram(
            OpenGL.GL.shaders.compileShader(vertex_shader_sourcecode, GL_VERTEX_SHADER),
            OpenGL.GL.shaders.compileShader(fragment_shader_sourcecode, GL_FRAGMENT_SHADER))

        self.view_uniform_location = glGetUniformLocation(self.shader, "view")
        self.projection_uniform_location = glGetUniformLocation(self.shader, "projection")

    def get_shader(self):
        return self.shader

    def bind(self):
        glUseProgram(self.shader)

    def load_shader(self, shader_location):
        shader_source = ""
        with open(shader_location) as f:
            shader_source = f.read()
        f.close()
        return str.encode(shader_source)

    def unbind(self):
        glUseProgram(0)