import context
from OpenGL.GL import *
import numpy
import shader_handling
import pyrr

class TronDirectionalLight:
    def __init__(self):
        self.id = len(context.main_context.lights)
        context.main_context.lights.append(self)

        self.hided = 0

        self.quad_vertices = [-1.0, 1.0, 0.0, 0.0, 1.0,
                              -1.0, -1.0, 0.0, 0.0, 0.0,
                              1.0, 1.0, 0.0, 1.0, 1.0,
                              1.0, -1.0, 0.0, 1.0, 0.0]

        self.quad_vertices = numpy.array(self.quad_vertices, dtype=numpy.float32)
        self.quadVAO = glGenVertexArrays(1)
        self.quadVBO = glGenBuffers(1)
        glBindVertexArray(self.quadVAO)
        glBindBuffer(GL_ARRAY_BUFFER, self.quadVBO)
        glBufferData(GL_ARRAY_BUFFER, self.quad_vertices.itemsize * len(self.quad_vertices), self.quad_vertices,
                     GL_STATIC_DRAW)
        # position - 0
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, self.quad_vertices.itemsize * 5, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        # textures - 1
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, self.quad_vertices.itemsize * 5, ctypes.c_void_p(12))
        glEnableVertexAttribArray(1)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)

        self.depth_map_fbo = glGenFramebuffers(1)
        self.shadow_map_width = 4096
        self.shadow_map_height = self.shadow_map_width
        self.depth_map = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.depth_map)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT,
                     self.shadow_map_width, self.shadow_map_height, 0, GL_DEPTH_COMPONENT, GL_FLOAT, None)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)

        glBindFramebuffer(GL_FRAMEBUFFER, self.depth_map_fbo)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D, self.depth_map, 0)
        glDrawBuffer(GL_NONE)
        glReadBuffer(GL_NONE)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

        self.depth_shader = shader_handling.TronShader()
        self.depth_shader.compile_shader(context.main_context.path_to_res_folder + "res/shaders/shadow_fill_vertex_shader.glsl",
                                        context.main_context.path_to_res_folder + "res/shaders/shadow_fill_fragment_shader.glsl")
        self.draw_shader = shader_handling.TronShader()
        self.draw_shader.compile_shader(context.main_context.path_to_res_folder + "res/shaders/shadow_draw_vertex_shader.glsl",
                                        context.main_context.path_to_res_folder + "res/shaders/shadow_draw_fragment_shader.glsl")

        self.shadow_projection_matrix = None
        self.shadow_view_matrix = None

        self.position = None
        self.direction = None
        self.color = None
        self.brightness = None
        self.brightness_for_materials = None

    def describe(self, position, color, brightness, brightness_for_materials):
        self.position = position
        max_value = max(abs(i) for i in self.position)
        self.direction = [-i / max_value for i in self.position]
        self.color = color
        self.brightness = brightness
        self.brightness_for_materials = brightness_for_materials

    def update_shade_map(self):
        # Matrices:
        near_plane = 1.0
        far_plane = 100.0

        self.shadow_projection_matrix = \
            pyrr.matrix44.create_orthogonal_projection_matrix(-20.0, 20.0, -20.0, 20.0, near_plane, far_plane)
        # TODO: fix the 'looking directly down' problem
        self.shadow_view_matrix = pyrr.matrix44.create_look_at(self.position, [0, 0, 0.000001], [0.0, 1.0, 0.0])

        # shadow draw:
        self.depth_shader.bind()
        glUniformMatrix4fv(self.depth_shader.view_uniform_location, 1, GL_FALSE, self.shadow_view_matrix)
        glUniformMatrix4fv(self.depth_shader.projection_uniform_location, 1, GL_FALSE, self.shadow_projection_matrix)

        glViewport(0, 0, self.shadow_map_width, self.shadow_map_height)
        glBindFramebuffer(GL_FRAMEBUFFER, self.depth_map_fbo)
        glClear(GL_DEPTH_BUFFER_BIT)

        for item in context.main_context.objects:
            if item.hided == 0:
                item.shade_draw()

        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        window_width = context.main_context.windows[context.main_context.current_window].window_width
        window_height = context.main_context.windows[context.main_context.current_window].window_height
        glViewport(0, 0, window_width, window_height)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # DEBUG:
        self.draw_shader.bind()
        glBindTexture(GL_TEXTURE_2D, self.depth_map)
        glBindVertexArray(self.quadVAO)
        glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)
        glBindVertexArray(0)

    def set_shader_uniforms(self, shader, self_id, material_type):
        uniform = glGetUniformLocation(shader.get_shader(), "view_light[" + str(self_id) + "]")
        glUniformMatrix4fv(uniform, 1, GL_FALSE, self.shadow_view_matrix)
        uniform = glGetUniformLocation(shader.get_shader(), "projection_light[" + str(self_id) + "]")
        glUniformMatrix4fv(uniform, 1, GL_FALSE, self.shadow_projection_matrix)
        # #############################################################
        uniform = glGetUniformLocation(shader.get_shader(), "directionalLight[" + str(self_id) + "].direction")

        glUniform3f(uniform, self.direction[0], self.direction[1], self.direction[2])
        uniform = glGetUniformLocation(shader.get_shader(), "directionalLight[" + str(self_id) + "].color")
        glUniform3f(uniform, self.color[0], self.color[1], self.color[2])
        if material_type:
            uniform = glGetUniformLocation(shader.get_shader(),
                                           "directionalLight[" + str(self_id) + "].ambientIntensity")
            glUniform1f(uniform, self.brightness[0])
            uniform = glGetUniformLocation(shader.get_shader(),
                                           "directionalLight[" + str(self_id) + "].diffuseIntensity")
            glUniform1f(uniform, self.brightness[1])
            uniform = glGetUniformLocation(shader.get_shader(),
                                           "directionalLight[" + str(self_id) + "].specularIntensity")
            glUniform1f(uniform, self.brightness[2])
        else:
            uniform = glGetUniformLocation(shader.get_shader(),
                                           "directionalLight[" + str(self_id) + "].ambientIntensity")
            glUniform1f(uniform, self.brightness_for_materials[0])
            uniform = glGetUniformLocation(shader.get_shader(),
                                           "directionalLight[" + str(self_id) + "].diffuseIntensity")
            glUniform1f(uniform, self.brightness_for_materials[1])
            uniform = glGetUniformLocation(shader.get_shader(),
                                           "directionalLight[" + str(self_id) + "].specularIntensity")
            glUniform1f(uniform, self.brightness_for_materials[2])
        uniform = glGetUniformLocation(shader.get_shader(), "camera_position")
        glUniform3f(uniform,
                    context.main_context.cameras[context.main_context.current_camera].camera_pos[0],
                    context.main_context.cameras[context.main_context.current_camera].camera_pos[1],
                    context.main_context.cameras[context.main_context.current_camera].camera_pos[2])

