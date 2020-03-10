from OpenGL.GL import *
import numpy
import context


class TronObject:
    def __init__(self, structure_id):
        self.hided = 0
        self.position = None
        self.structure = None
        self.structure_id = structure_id

        self.rotation_array = numpy.array([0, 0, 0], numpy.float32)
        self.instance_array = numpy.array([0, 0, 0], numpy.float32)
        self.resize_array = numpy.array([1], numpy.float32)

        self.rotation_array_previous = numpy.array([0, 0, 0], numpy.float32)
        self.instance_array_previous = numpy.array([0, 0, 0], numpy.float32)
        self.resize_array_previous = numpy.array([0], numpy.float32)

        self.instance_vbo = glGenBuffers(1)
        self.rotation_vbo = glGenBuffers(1)
        self.resize_vbo = glGenBuffers(1)

        self.update_buffers()

        context.main_context.objects.append(self)

    def describe_buffers(self):
        glBindBuffer(GL_ARRAY_BUFFER, self.instance_vbo)
        # instance - 6
        glVertexAttribPointer(6, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glEnableVertexAttribArray(6)
        glVertexAttribDivisor(6, 1)

        glBindBuffer(GL_ARRAY_BUFFER, self.rotation_vbo)
        # rotation - 7
        glVertexAttribPointer(7, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glEnableVertexAttribArray(7)
        glVertexAttribDivisor(7, 1)

        glBindBuffer(GL_ARRAY_BUFFER, self.resize_vbo)
        # resize - 8
        glVertexAttribPointer(8, 1, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glEnableVertexAttribArray(8)
        glVertexAttribDivisor(8, 1)

    def update_buffers(self):
        if not numpy.array_equal(self.rotation_array, self.rotation_array_previous) or \
                not numpy.array_equal(self.instance_array, self.instance_array_previous) or \
                not numpy.array_equal(self.resize_array, self.resize_array_previous):
            glBindBuffer(GL_ARRAY_BUFFER, self.rotation_vbo)
            glBufferData(GL_ARRAY_BUFFER, self.rotation_array.itemsize * len(self.rotation_array),
                         self.rotation_array, GL_DYNAMIC_DRAW)
            glBindBuffer(GL_ARRAY_BUFFER, self.instance_vbo)
            glBufferData(GL_ARRAY_BUFFER, self.instance_array.itemsize * len(self.instance_array),
                         self.instance_array, GL_DYNAMIC_DRAW)
            glBindBuffer(GL_ARRAY_BUFFER, self.resize_vbo)
            glBufferData(GL_ARRAY_BUFFER, self.resize_array.itemsize * len(self.resize_array),
                         self.resize_array, GL_DYNAMIC_DRAW)

            self.rotation_array_previous = self.rotation_array
            self.instance_array_previous = self.instance_array
            self.resize_array_previous = self.resize_array

    def shade_draw(self):
        struct = context.main_context.structures[self.structure_id]

        self.update_buffers()
        for i in struct.subobjects:
            i.update_buffers()
            for j in i.parts:
                if context.main_context.materials[j.material_id].texture_id is not None:
                    glBindVertexArray(j.vao)
                    i.describe_buffers()
                    self.describe_buffers()
                    count_objects = 1
                    glDrawArraysInstanced(GL_TRIANGLES, 0, len(j.points), count_objects)

    def real_draw(self):
        cam = context.main_context.cameras[context.main_context.current_camera]

        context.main_context.shader_texture.bind()
        uniform = glGetUniformLocation(context.main_context.shader_texture.get_shader(), "num_active_lights")
        glUniform1i(uniform, context.main_context.num_active_lights)
        count_added = 0
        for i in range(len(context.main_context.lights)):
            if context.main_context.lights[i].hided == 0:
                context.main_context.lights[i].set_shader_uniforms(context.main_context.shader_texture, count_added, 1)
                count_added += 1
        glUniformMatrix4fv(context.main_context.shader_texture.view_uniform_location, 1, GL_FALSE, cam.camera_view_matrix)
        glUniformMatrix4fv(context.main_context.shader_texture.projection_uniform_location, 1, GL_FALSE,
                           cam.camera_projection_matrix)
        glUniform1i(glGetUniformLocation(context.main_context.shader_texture.get_shader(), "tex_sampler"), 0)
        count_added = 0
        for k in range(len(context.main_context.lights)):
            if context.main_context.lights[k].hided == 0:
                glUniform1i(glGetUniformLocation(context.main_context.shader_texture.get_shader(),
                            "shadowMap[" + str(count_added) + "]"), count_added + 1)
                count_added += 1
        textures_array = []
        for i in context.main_context.lights:
            if i.hided == 0:
                textures_array.append(i.depth_map)
        glBindTextures(1, context.main_context.num_active_lights, textures_array)

        struct = context.main_context.structures[self.structure_id]

        self.update_buffers()
        for i in struct.subobjects:
            i.update_buffers()
            for j in i.parts:
                if context.main_context.materials[j.material_id].texture_id is not None:
                    context.main_context.shader_texture.bind()
                    glActiveTexture(GL_TEXTURE0)
                    context.main_context.textures[context.main_context.materials[j.material_id].texture_id].bind()

                    glBindVertexArray(j.vao)
                    # TODO: do we need this as part buffers, or we can make them subobject buffers?
                    i.describe_buffers()
                    self.describe_buffers()

                    count_objects = 1
                    glDrawArraysInstanced(GL_TRIANGLES, 0, len(j.points), count_objects)

        context.main_context.shader_common.bind()
        uniform = glGetUniformLocation(context.main_context.shader_common.get_shader(), "num_active_lights")
        glUniform1i(uniform, context.main_context.num_active_lights)
        count_added = 0
        for i in range(len(context.main_context.lights)):
            if context.main_context.lights[i].hided == 0:
                context.main_context.lights[i].set_shader_uniforms(context.main_context.shader_common, count_added, 0)
                count_added += 1
        glUniformMatrix4fv(context.main_context.shader_common.view_uniform_location, 1, GL_FALSE, cam.camera_view_matrix)
        glUniformMatrix4fv(context.main_context.shader_common.projection_uniform_location, 1, GL_FALSE,
                           cam.camera_projection_matrix)
        count_added = 0
        for k in range(len(context.main_context.lights)):
            if context.main_context.lights[k].hided == 0:
                glUniform1i(glGetUniformLocation(context.main_context.shader_common.get_shader(),
                                                 "shadowMap[" + str(count_added) + "]"), count_added)
                count_added += 1
        textures_array = []
        for i in context.main_context.lights:
            if i.hided == 0:
                textures_array.append(i.depth_map)
        glBindTextures(0, context.main_context.num_active_lights, textures_array)

        glUniformMatrix4fv(context.main_context.shader_common.view_uniform_location, 1, GL_FALSE, cam.camera_view_matrix)
        glUniformMatrix4fv(context.main_context.shader_common.projection_uniform_location, 1, GL_FALSE,
                           cam.camera_projection_matrix)

        self.update_buffers()
        for i in struct.subobjects:
            i.update_buffers()
            for j in i.parts:
                if context.main_context.materials[j.material_id].texture_id is None:
                    context.main_context.shader_common.bind()
                    glBindVertexArray(j.vao)
                    i.describe_buffers()
                    self.describe_buffers()

                    count_objects = 1
                    glDrawArraysInstanced(GL_TRIANGLES, 0, len(j.points), count_objects)

    def draw(self, rotation_array, instance_array, resize_array):
        self.rotation_array = rotation_array
        self.instance_array = instance_array
        self.resize_array = resize_array

