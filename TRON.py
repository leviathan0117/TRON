import glfw
import sys
from OpenGL.GL import *
import OpenGL.GL.shaders
import pyrr
import numpy
import time
import math
from PIL import Image

path_to_res_folder = "./"
aspect_ratio = 1
camera_projection_matrix = None
camera_view_matrix = None


class Camera:
    def __init__(self):
        self.camera_pos = pyrr.Vector3([0.0, 0.0, 0.0])
        self.camera_front = pyrr.Vector3([0.0, 0.0, -1.0])
        self.camera_up = pyrr.Vector3([0.0, 1.0, 0.0])
        self.camera_right = pyrr.Vector3([1.0, 0.0, 0.0])

        self.mouse_sensitivity = 0.25
        self.yaw = 0.0
        self.pitch = 0.0

    def get_view_matrix(self):
        return self.look_at(self.camera_pos, self.camera_pos + self.camera_front, self.camera_up)

    def process_keyboard(self, direction, velocity):
        if direction == "FORWARD":
            self.camera_pos += self.camera_front * velocity
        if direction == "BACKWARD":
            self.camera_pos -= self.camera_front * velocity
        if direction == "LEFT":
            self.camera_pos -= self.camera_right * velocity
        if direction == "RIGHT":
            self.camera_pos += self.camera_right * velocity
        if direction == "UP":
            self.camera_pos += self.camera_up * velocity
        if direction == "DOWN":
            self.camera_pos -= self.camera_up * velocity

    def turn_camera(self, offset_x, offset_y):
        offset_x *= self.mouse_sensitivity
        offset_y *= self.mouse_sensitivity

        self.yaw += offset_x
        self.pitch += offset_y

        if self.pitch > 89.9:
            self.pitch = 89.9
        if self.pitch < -89.9:
            self.pitch = -89.9

        self.update_camera_vectors()

    def update_camera_vectors(self):
        front = pyrr.Vector3([0.0, 0.0, 0.0])
        front.x = math.cos(math.radians(self.yaw)) * math.cos(math.radians(self.pitch))
        front.y = math.sin(math.radians(self.pitch))
        front.z = math.sin(math.radians(self.yaw)) * math.cos(math.radians(self.pitch))

        self.camera_front = pyrr.vector.normalise(front)
        self.camera_right = pyrr.vector.normalise(pyrr.vector3.cross(self.camera_front, pyrr.Vector3([0.0, 1.0, 0.0])))
        self.camera_up = pyrr.vector.normalise(pyrr.vector3.cross(self.camera_right, self.camera_front))

    def look_at(self, position, target, world_up):
        # 1.Position = known
        # 2.Calculate cameraDirection
        axis_z = pyrr.vector.normalise(position - target)
        # 3.Get positive right axis vector
        axis_x = pyrr.vector.normalise(pyrr.vector3.cross(pyrr.vector.normalise(world_up), axis_z))
        # 4.Calculate the camera up vector
        axis_y = pyrr.vector3.cross(axis_z, axis_x)

        # create translation and rotation matrix
        translation = pyrr.Matrix44.identity()
        translation[3][0] = -position.x
        translation[3][1] = -position.y
        translation[3][2] = -position.z

        rotation = pyrr.Matrix44.identity()
        rotation[0][0] = axis_x[0]
        rotation[1][0] = axis_x[1]
        rotation[2][0] = axis_x[2]
        rotation[0][1] = axis_y[0]
        rotation[1][1] = axis_y[1]
        rotation[2][1] = axis_y[2]
        rotation[0][2] = axis_z[0]
        rotation[1][2] = axis_z[1]
        rotation[2][2] = axis_z[2]

        return rotation * translation


def window_resize(window, width, height):
    global aspect_ratio, camera_projection_matrix

    glViewport(0, 0, width, height)

    aspect_ratio = width / height

    camera_projection_matrix = pyrr.matrix44.create_perspective_projection_matrix(45.0, aspect_ratio, 0.1, 100.0)


cam = Camera()
keys = [False] * 1024
lastX, lastY = 960, 540
first_mouse = True


def key_callback(window, key, scan_code, action, mode):
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, True)

    if 0 <= key < 1024:
        if action == glfw.PRESS:
            keys[key] = True
        elif action == glfw.RELEASE:
            keys[key] = False


def do_movement():
    speed = 0.1
    if keys[glfw.KEY_W]:
        cam.process_keyboard("FORWARD", speed)
    if keys[glfw.KEY_S]:
        cam.process_keyboard("BACKWARD", speed)
    if keys[glfw.KEY_A]:
        cam.process_keyboard("LEFT", speed)
    if keys[glfw.KEY_D]:
        cam.process_keyboard("RIGHT", speed)
    if keys[glfw.KEY_SPACE]:
        cam.process_keyboard("UP", speed)
    if keys[glfw.KEY_C]:
        cam.process_keyboard("DOWN", speed)


def mouse_callback(window, xpos, ypos):
    global first_mouse, lastX, lastY

    if first_mouse:
        lastX = xpos
        lastY = ypos
        first_mouse = False

    offset_x = xpos - lastX
    offset_y = lastY - ypos

    lastX = xpos
    lastY = ypos

    cam.turn_camera(offset_x, offset_y)


class Shader:
    def __init__(self):
        self.shader = None
        self.view_uniform_location = None
        self.projection_uniform_location = None

    def compile_shader(self, vertex_shader_location, fragment_shader_location):
        vertex_shader_location = path_to_res_folder + vertex_shader_location
        fragment_shader_location = path_to_res_folder + fragment_shader_location

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


shader_texture = Shader()
shader_common = Shader()


class Texture:
    def __init__(self):
        self.id = None

    def load(self, path_to_texture):
        path_to_texture = path_to_res_folder + path_to_texture
        self.id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.id)
        # Set the texture wrapping parameters
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        # Set texture filtering parameters
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        # load image
        image = Image.open(path_to_texture)
        # TODO: speed up this line:
        img_data = numpy.array(list(image.getdata()), numpy.uint8)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, image.width, image.height, 0, GL_RGB, GL_UNSIGNED_BYTE, img_data)
        glBindTexture(GL_TEXTURE_2D, 0)

        return self.id

    def bind(self):
        glBindTexture(GL_TEXTURE_2D, self.id)


class TexturedCubes:
    def __init__(self):
        self.points = numpy.zeros(0)
        self.triangles = numpy.zeros(0)
        self.load_data()

        self.shader = Shader()
        self.shader.compile_shader("res/shaders/textured_object_vertex_shader.glsl", "res/shaders/textured_object_fragment_shader.glsl")

        self.texture = Texture()
        self.texture.load("res/textures/crate.jpg")

        self.vao = glGenVertexArrays(1)
        self.points_vbo = glGenBuffers(1)
        self.instance_vbo = glGenBuffers(1)
        self.rotation_vbo = glGenBuffers(1)
        self.resize_vbo = glGenBuffers(1)
        self.ibo = glGenBuffers(1)

        glBindVertexArray(self.vao)

        glBindBuffer(GL_ARRAY_BUFFER, self.points_vbo)
        glBufferData(GL_ARRAY_BUFFER, self.points.itemsize * len(self.points), self.points, GL_STATIC_DRAW)
        # position - 0
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, self.points.itemsize * 5, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        # textures - 1
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, self.points.itemsize * 5, ctypes.c_void_p(12))
        glEnableVertexAttribArray(1)

        glBindBuffer(GL_ARRAY_BUFFER, self.instance_vbo)
        # instance - 2
        glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glEnableVertexAttribArray(2)
        glVertexAttribDivisor(2, 1)

        glBindBuffer(GL_ARRAY_BUFFER, self.rotation_vbo)
        # rotation - 3
        glVertexAttribPointer(3, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glEnableVertexAttribArray(3)
        glVertexAttribDivisor(3, 1)

        glBindBuffer(GL_ARRAY_BUFFER, self.resize_vbo)
        # resize - 4
        glVertexAttribPointer(4, 1, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glEnableVertexAttribArray(4)
        glVertexAttribDivisor(4, 1)

        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ibo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.triangles.itemsize * len(self.triangles),
                     self.triangles, GL_STATIC_DRAW)

        self.view_uniform_location = glGetUniformLocation(self.shader.get_shader(), "view")
        self.projection_uniform_location = glGetUniformLocation(self.shader.get_shader(), "projection")

        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)
        glBindVertexArray(0)
        glUseProgram(0)

    def draw(self, rotation_array, instance_array, resize_array):
        global aspect_ratio, camera_projection_matrix, camera_view_matrix

        self.texture.bind()

        self.shader.bind()
        glUniformMatrix4fv(self.view_uniform_location, 1, GL_FALSE, camera_view_matrix)
        glUniformMatrix4fv(self.projection_uniform_location, 1, GL_FALSE, camera_projection_matrix)

        glBindVertexArray(self.vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.rotation_vbo)
        glBufferData(GL_ARRAY_BUFFER, rotation_array.itemsize * len(rotation_array), rotation_array, GL_DYNAMIC_DRAW)
        glBindBuffer(GL_ARRAY_BUFFER, self.instance_vbo)
        glBufferData(GL_ARRAY_BUFFER, instance_array.itemsize * len(instance_array), instance_array, GL_DYNAMIC_DRAW)
        glBindBuffer(GL_ARRAY_BUFFER, self.resize_vbo)
        glBufferData(GL_ARRAY_BUFFER, resize_array.itemsize * len(resize_array), resize_array, GL_DYNAMIC_DRAW)

        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ibo)

        count_cubes = int(len(rotation_array) / 3)
        glDrawElementsInstanced(GL_TRIANGLES, len(self.triangles), GL_UNSIGNED_INT, None, count_cubes)

    def load_data(self):
        self.points = [-0.5, -0.5, 0.5, 0.0, 0.0,
                       0.5, -0.5, 0.5, 1.0, 0.0,
                       0.5, 0.5, 0.5, 1.0, 1.0,
                       -0.5, 0.5, 0.5, 0.0, 1.0,

                       -0.5, -0.5, -0.5, 0.0, 0.0,
                       0.5, -0.5, -0.5, 1.0, 0.0,
                       0.5, 0.5, -0.5, 1.0, 1.0,
                       -0.5, 0.5, -0.5, 0.0, 1.0,

                       0.5, -0.5, -0.5, 0.0, 0.0,
                       0.5, 0.5, -0.5, 1.0, 0.0,
                       0.5, 0.5, 0.5, 1.0, 1.0,
                       0.5, -0.5, 0.5, 0.0, 1.0,

                       -0.5, 0.5, -0.5, 0.0, 0.0,
                       -0.5, -0.5, -0.5, 1.0, 0.0,
                       -0.5, -0.5, 0.5, 1.0, 1.0,
                       -0.5, 0.5, 0.5, 0.0, 1.0,

                       -0.5, -0.5, -0.5, 0.0, 0.0,
                       0.5, -0.5, -0.5, 1.0, 0.0,
                       0.5, -0.5, 0.5, 1.0, 1.0,
                       -0.5, -0.5, 0.5, 0.0, 1.0,

                       0.5, 0.5, -0.5, 0.0, 0.0,
                       -0.5, 0.5, -0.5, 1.0, 0.0,
                       -0.5, 0.5, 0.5, 1.0, 1.0,
                       0.5, 0.5, 0.5, 0.0, 1.0]

        self.points = numpy.array(self.points, dtype=numpy.float32)

        self.triangles = [0, 1, 2, 2, 3, 0,
                          4, 5, 6, 6, 7, 4,
                          8, 9, 10, 10, 11, 8,
                          12, 13, 14, 14, 15, 12,
                          16, 17, 18, 18, 19, 16,
                          20, 21, 22, 22, 23, 20]

        self.triangles = numpy.array(self.triangles, dtype=numpy.uint32)


class Object:
    def __init__(self, texture_dir_location, object_file_location):
        self.materials = []
        self.subobjects = []

        self.load_data(texture_dir_location, object_file_location)
        self.count_subobjects = len(self.subobjects)

        self.vaos = []
        self.points_vbos = []
        self.instance_vbos = []
        self.rotation_vbos = []
        self.resize_vbos = []

        for i in range(self.count_subobjects):
            self.vaos.append(glGenVertexArrays(max(self.subobjects[i].count_parts, 2)))
            self.points_vbos.append(glGenBuffers(max(self.subobjects[i].count_parts, 2)))
            self.instance_vbos.append(glGenBuffers(max(self.subobjects[i].count_parts, 2)))
            self.rotation_vbos.append(glGenBuffers(max(self.subobjects[i].count_parts, 2)))
            self.resize_vbos.append(glGenBuffers(max(self.subobjects[i].count_parts, 2)))

            for j in range(self.subobjects[i].count_parts):
                if self.materials[self.subobjects[i].parts[j].material_id].texture is not None:
                    glBindVertexArray(self.vaos[i][j])

                    glBindBuffer(GL_ARRAY_BUFFER, self.points_vbos[i][j])
                    glBufferData(GL_ARRAY_BUFFER,
                                 self.subobjects[i].parts[j].points.itemsize * len(self.subobjects[i].parts[j].points),
                                 self.subobjects[i].parts[j].points, GL_STATIC_DRAW)
                    # position - 0
                    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, self.subobjects[i].parts[j].points.itemsize * 8,
                                          ctypes.c_void_p(0))
                    glEnableVertexAttribArray(0)
                    # textures - 1
                    glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, self.subobjects[i].parts[j].points.itemsize * 8,
                                          ctypes.c_void_p(3 * 4))
                    glEnableVertexAttribArray(1)
                    # normals - 2
                    glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, self.subobjects[i].parts[j].points.itemsize * 8,
                                          ctypes.c_void_p((3 + 2) * 4))
                    glEnableVertexAttribArray(2)

                    glBindBuffer(GL_ARRAY_BUFFER, self.instance_vbos[i][j])
                    # instance - 3
                    glVertexAttribPointer(3, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
                    glEnableVertexAttribArray(3)
                    glVertexAttribDivisor(3, 1)

                    glBindBuffer(GL_ARRAY_BUFFER, self.rotation_vbos[i][j])
                    # rotation - 4
                    glVertexAttribPointer(4, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
                    glEnableVertexAttribArray(4)
                    glVertexAttribDivisor(4, 1)

                    glBindBuffer(GL_ARRAY_BUFFER, self.resize_vbos[i][j])
                    # resize - 5
                    glVertexAttribPointer(5, 1, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
                    glEnableVertexAttribArray(5)
                    glVertexAttribDivisor(5, 1)
                else:
                    glBindVertexArray(self.vaos[i][j])

                    glBindBuffer(GL_ARRAY_BUFFER, self.points_vbos[i][j])
                    glBufferData(GL_ARRAY_BUFFER,
                                 self.subobjects[i].parts[j].points.itemsize * len(self.subobjects[i].parts[j].points),
                                 self.subobjects[i].parts[j].points, GL_STATIC_DRAW)
                    # position - 0
                    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, self.subobjects[i].parts[j].points.itemsize * 10,
                                          ctypes.c_void_p(0))
                    glEnableVertexAttribArray(0)
                    # color - 1
                    glVertexAttribPointer(1, 4, GL_FLOAT, GL_FALSE, self.subobjects[i].parts[j].points.itemsize * 10,
                                          ctypes.c_void_p(12))
                    glEnableVertexAttribArray(1)
                    # normals - 2
                    glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, self.subobjects[i].parts[j].points.itemsize * 10,
                                          ctypes.c_void_p((3 + 4) * 4))
                    glEnableVertexAttribArray(2)

                    glBindBuffer(GL_ARRAY_BUFFER, self.instance_vbos[i][j])
                    # instance - 3
                    glVertexAttribPointer(3, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
                    glEnableVertexAttribArray(3)
                    glVertexAttribDivisor(3, 1)

                    glBindBuffer(GL_ARRAY_BUFFER, self.rotation_vbos[i][j])
                    # rotation - 4
                    glVertexAttribPointer(4, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
                    glEnableVertexAttribArray(4)
                    glVertexAttribDivisor(4, 1)

                    glBindBuffer(GL_ARRAY_BUFFER, self.resize_vbos[i][j])
                    # resize - 5
                    glVertexAttribPointer(5, 1, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
                    glEnableVertexAttribArray(5)
                    glVertexAttribDivisor(5, 1)

        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)
        glBindVertexArray(0)
        glUseProgram(0)

    def draw(self, rotation_array, instance_array, resize_array):
        global aspect_ratio, camera_projection_matrix, camera_view_matrix
        global shader_texture, shader_common

        for i in range(self.count_subobjects):
            for j in range(self.subobjects[i].count_parts):
                if self.materials[self.subobjects[i].parts[j].material_id].texture is not None:
                    shader_texture.bind()
                    glUniformMatrix4fv(shader_texture.view_uniform_location, 1, GL_FALSE, camera_view_matrix)
                    glUniformMatrix4fv(shader_texture.projection_uniform_location, 1, GL_FALSE,
                                       camera_projection_matrix)
                    self.materials[self.subobjects[i].parts[j].material_id].texture.bind()
                    glBindVertexArray(self.vaos[i][j])
                    glBindBuffer(GL_ARRAY_BUFFER, self.rotation_vbos[i][j])
                    glBufferData(GL_ARRAY_BUFFER, rotation_array.itemsize * len(rotation_array),
                                 rotation_array, GL_DYNAMIC_DRAW)
                    glBindBuffer(GL_ARRAY_BUFFER, self.instance_vbos[i][j])
                    glBufferData(GL_ARRAY_BUFFER, instance_array.itemsize * len(instance_array),
                                 instance_array, GL_DYNAMIC_DRAW)
                    glBindBuffer(GL_ARRAY_BUFFER, self.resize_vbos[i][j])
                    glBufferData(GL_ARRAY_BUFFER, resize_array.itemsize * len(resize_array),
                                 resize_array, GL_DYNAMIC_DRAW)

                    count_objects = int(len(rotation_array) / 3)
                    if not keys[glfw.KEY_P]:
                        glDrawArraysInstanced(GL_TRIANGLES, 0, len(self.subobjects[i].parts[j].points), count_objects)
                        pass
                    else:
                        glPointSize(2)
                        glDrawArraysInstanced(GL_POINTS, 0, len(self.subobjects[i].parts[j].points), count_objects)
        for i in range(self.count_subobjects):
            for j in range(self.subobjects[i].count_parts):
                if self.materials[self.subobjects[i].parts[j].material_id].texture is None:
                    shader_common.bind()
                    glUniformMatrix4fv(shader_common.view_uniform_location, 1, GL_FALSE, camera_view_matrix)
                    glUniformMatrix4fv(shader_common.projection_uniform_location, 1, GL_FALSE, camera_projection_matrix)

                    glBindVertexArray(self.vaos[i][j])
                    glBindBuffer(GL_ARRAY_BUFFER, self.rotation_vbos[i][j])
                    glBufferData(GL_ARRAY_BUFFER, rotation_array.itemsize * len(rotation_array),
                                 rotation_array, GL_DYNAMIC_DRAW)
                    glBindBuffer(GL_ARRAY_BUFFER, self.instance_vbos[i][j])
                    glBufferData(GL_ARRAY_BUFFER, instance_array.itemsize * len(instance_array),
                                 instance_array, GL_DYNAMIC_DRAW)
                    glBindBuffer(GL_ARRAY_BUFFER, self.resize_vbos[i][j])
                    glBufferData(GL_ARRAY_BUFFER, resize_array.itemsize * len(resize_array),
                                 resize_array, GL_DYNAMIC_DRAW)

                    count_objects = int(len(rotation_array) / 3)
                    if not keys[glfw.KEY_P]:
                        glDrawArraysInstanced(GL_TRIANGLES, 0, len(self.subobjects[i].parts[j].points), count_objects)
                    else:
                        glPointSize(2)
                        glDrawArraysInstanced(GL_POINTS, 0, len(self.subobjects[i].parts[j].points), count_objects)
        # sys.exit(0)

    def load_data(self, texture_dir_location, object_file_location):
        object_file_location = path_to_res_folder + object_file_location
        mtl_file_location = object_file_location.replace(".obj", ".mtl")
        last_it = -1

        for line in open(mtl_file_location, "r"):
            # delete the ending '\n'
            line = line.replace("\n", "")

            if line.startswith("#"):
                continue
            elif line.startswith("newmtl"):
                self.materials.append(Material())
                last_it += 1

                value = line.split(" ")[1]
                self.materials[last_it].name = value
            elif line.startswith("Ns"):
                value = line.split(" ")[1]
                self.materials[last_it].ns = float(value)
            elif line.startswith("Ka"):
                values = line.split(" ")
                self.materials[last_it].ka.append(float(values[1]))
                self.materials[last_it].ka.append(float(values[2]))
                self.materials[last_it].ka.append(float(values[3]))
            elif line.startswith("Kd"):
                values = line.split(" ")
                self.materials[last_it].kd.append(float(values[1]))
                self.materials[last_it].kd.append(float(values[2]))
                self.materials[last_it].kd.append(float(values[3]))
            elif line.startswith("Ks"):
                values = line.split(" ")
                self.materials[last_it].ks.append(float(values[1]))
                self.materials[last_it].ks.append(float(values[2]))
                self.materials[last_it].ks.append(float(values[3]))
            elif line.startswith("Ni"):
                value = line.split(" ")[1]
                self.materials[last_it].ni = float(value)
            elif line.startswith("d"):
                value = line.split(" ")[1]
                self.materials[last_it].d = float(value)
            elif line.startswith("illum"):
                value = line.split(" ")[1]
                self.materials[last_it].illum = int(value)
            elif line.startswith("map_Kd"):
                value = line.split(" ")[1]
                self.materials[last_it].map_kd = value

        for i in self.materials:
            if i.map_kd != "":
                i.texture = Texture()
                i.texture.load(texture_dir_location + i.map_kd)

        keep_alive_counter = 0

        tmp_vertex_coordinates = []
        tmp_texture_coordinates = []
        tmp_normal_coordinates = []

        tmp_vertex_index = []
        tmp_texture_index = []
        tmp_normal_index = []

        state = 0
        current_material_name = 0
        current_material = None

        for line in open(object_file_location, 'r'):
            keep_alive_counter += 1
            if keep_alive_counter == 10 ** 5:
                # THIS RESOLVES THE 'WINDOW STOPPED RESPONDING' PROBLEM
                glfw.poll_events()
                keep_alive_counter = 0

            line = line.replace("\n", "")
            if line.startswith("#"):
                continue
            data = line.split(" ")
            if not data:
                continue

            # Points data:
            if data[0] == "v":
                tmp_vertex_coordinates.append([float(data[1]), float(data[2]), float(data[3])])
            if data[0] == "vt":
                tmp_texture_coordinates.append([float(data[1]), float(data[2])])
            if data[0] == "vn":
                tmp_normal_coordinates.append([float(data[1]), float(data[2]), float(data[3])])

            # Objects and materials:
            if data[0] == "usemtl":
                current_material_name = data[1]
                state = 1
            if data[0] == "o":
                self.subobjects.append(SubObject())
                self.subobjects[-1].name = data[1]
                state = 1

            # Subpart handling:
            if data[0] == "f" and state:
                self.subobjects[-1].parts.append(SubObjectPart())
                for i in range(len(self.materials)):
                    if self.materials[i].name == current_material_name:
                        self.subobjects[-1].parts[-1].material_id = i
                        current_material = self.materials[i]
                state = 0
            if data[0] == "f":
                if current_material.texture is not None:
                    indexes = data[1].split("/")
                    self.subobjects[-1].parts[-1].points.extend(tmp_vertex_coordinates[int(indexes[0]) - 1])
                    self.subobjects[-1].parts[-1].points.extend(tmp_texture_coordinates[int(indexes[1]) - 1])
                    self.subobjects[-1].parts[-1].points.extend(tmp_normal_coordinates[int(indexes[2]) - 1])
                    indexes = data[2].split("/")
                    self.subobjects[-1].parts[-1].points.extend(tmp_vertex_coordinates[int(indexes[0]) - 1])
                    self.subobjects[-1].parts[-1].points.extend(tmp_texture_coordinates[int(indexes[1]) - 1])
                    self.subobjects[-1].parts[-1].points.extend(tmp_normal_coordinates[int(indexes[2]) - 1])
                    indexes = data[3].split("/")
                    self.subobjects[-1].parts[-1].points.extend(tmp_vertex_coordinates[int(indexes[0]) - 1])
                    self.subobjects[-1].parts[-1].points.extend(tmp_texture_coordinates[int(indexes[1]) - 1])
                    self.subobjects[-1].parts[-1].points.extend(tmp_normal_coordinates[int(indexes[2]) - 1])
                    if len(data) == 5:
                        indexes = data[3].split("/")
                        self.subobjects[-1].parts[-1].points.extend(tmp_vertex_coordinates[int(indexes[0]) - 1])
                        self.subobjects[-1].parts[-1].points.extend(tmp_texture_coordinates[int(indexes[1]) - 1])
                        self.subobjects[-1].parts[-1].points.extend(tmp_normal_coordinates[int(indexes[2]) - 1])
                        indexes = data[4].split("/")
                        self.subobjects[-1].parts[-1].points.extend(tmp_vertex_coordinates[int(indexes[0]) - 1])
                        self.subobjects[-1].parts[-1].points.extend(tmp_texture_coordinates[int(indexes[1]) - 1])
                        self.subobjects[-1].parts[-1].points.extend(tmp_normal_coordinates[int(indexes[2]) - 1])
                        indexes = data[1].split("/")
                        self.subobjects[-1].parts[-1].points.extend(tmp_vertex_coordinates[int(indexes[0]) - 1])
                        self.subobjects[-1].parts[-1].points.extend(tmp_texture_coordinates[int(indexes[1]) - 1])
                        self.subobjects[-1].parts[-1].points.extend(tmp_normal_coordinates[int(indexes[2]) - 1])
                # This is when we don't need vertices
                else:
                    color = [current_material.kd[0], current_material.kd[1], current_material.kd[2], current_material.d]
                    indexes = data[1].split("/")
                    self.subobjects[-1].parts[-1].points.extend(tmp_vertex_coordinates[int(indexes[0]) - 1])
                    self.subobjects[-1].parts[-1].points.extend(color)
                    self.subobjects[-1].parts[-1].points.extend(tmp_normal_coordinates[int(indexes[2]) - 1])
                    indexes = data[2].split("/")
                    self.subobjects[-1].parts[-1].points.extend(tmp_vertex_coordinates[int(indexes[0]) - 1])
                    self.subobjects[-1].parts[-1].points.extend(color)
                    self.subobjects[-1].parts[-1].points.extend(tmp_normal_coordinates[int(indexes[2]) - 1])
                    indexes = data[3].split("/")
                    self.subobjects[-1].parts[-1].points.extend(tmp_vertex_coordinates[int(indexes[0]) - 1])
                    self.subobjects[-1].parts[-1].points.extend(color)
                    self.subobjects[-1].parts[-1].points.extend(tmp_normal_coordinates[int(indexes[2]) - 1])
                    if len(data) == 5:
                        indexes = data[3].split("/")
                        self.subobjects[-1].parts[-1].points.extend(tmp_vertex_coordinates[int(indexes[0]) - 1])
                        self.subobjects[-1].parts[-1].points.extend(color)
                        self.subobjects[-1].parts[-1].points.extend(tmp_normal_coordinates[int(indexes[2]) - 1])
                        indexes = data[4].split("/")
                        self.subobjects[-1].parts[-1].points.extend(tmp_vertex_coordinates[int(indexes[0]) - 1])
                        self.subobjects[-1].parts[-1].points.extend(color)
                        self.subobjects[-1].parts[-1].points.extend(tmp_normal_coordinates[int(indexes[2]) - 1])
                        indexes = data[1].split("/")
                        self.subobjects[-1].parts[-1].points.extend(tmp_vertex_coordinates[int(indexes[0]) - 1])
                        self.subobjects[-1].parts[-1].points.extend(color)
                        self.subobjects[-1].parts[-1].points.extend(tmp_normal_coordinates[int(indexes[2]) - 1])
        for sub in self.subobjects:
            sub.count_parts = len(sub.parts)
            for part in sub.parts:
                part.points = numpy.array(part.points, dtype=numpy.float32).flatten()


class SubObjectPart:
    def __init__(self):
        self.material_id = 0
        self.points = []


class SubObject:
    def __init__(self):
        self.name = ""
        self.parts = []
        self.count_parts = 0


class Material:
    def __init__(self):
        self.name = ""
        self.ns = 0
        self.kd = []
        self.ka = []
        self.ks = []
        self.ni = 0
        self.d = 0
        self.illum = 0
        self.map_kd = ""
        self.map_ks = ""
        self.map_ka = ""
        self.map_bump = ""
        self.map_d = ""

        self.texture = None


class FPS:
    def __init__(self, user_interval):
        self.startTime = time.time()
        self.interval = user_interval
        self.counter = 0

    def update(self):
        self.counter += 1

    def print_fps(self):
        if (time.time() - self.startTime) > self.interval:
            print("FPS: ", self.counter / (time.time() - self.startTime))
            self.counter = 0
            self.startTime = time.time()

    def update_and_print(self):
        self.counter += 1
        if (time.time() - self.startTime) > self.interval:
            fps = self.counter / (time.time() - self.startTime)
            print("FPS: ", fps)
            self.counter = 0
            self.startTime = time.time()
            return fps
        return 0


class Program:
    def __init__(self):
        if not glfw.init():
            print("Failed to init GLFW!")
            sys.exit(1)

        # Declaring variables
        self.window = None
        self.window_height = None
        self.window_width = None
        self.window_name = None

        self.background_color_r = 0.0
        self.background_color_g = 0.0
        self.background_color_b = 0.0
        self.background_color_alpha = 1.0

    def create_window(self, **kwargs):
        self.window_width = kwargs.get('width', 800)
        self.window_height = kwargs.get('height', 600)
        self.window_name = kwargs.get('name', "My OpenGL window")
        self.window = glfw.create_window(self.window_width, self.window_height, self.window_name, None, None)

        glfw.set_window_size_callback(self.window, window_resize)
        glfw.set_key_callback(self.window, key_callback)
        glfw.set_cursor_pos_callback(self.window, mouse_callback)
        glfw.set_input_mode(self.window, glfw.CURSOR, glfw.CURSOR_DISABLED)

        if not self.window:
            print("Failed to create window")
            glfw.terminate()
            sys.exit(2)

        glfw.make_context_current(self.window)

        cam.turn_camera(0, 0)

        global shader_texture, shader_common
        shader_texture.compile_shader("res/shaders/textured_object_vertex_shader.glsl", "res/shaders/textured_object_fragment_shader.glsl")
        shader_common.compile_shader("res/shaders/common_object_vertex_shader.glsl", "res/shaders/common_object_fragment_shader.glsl")

    def window_loop(self, user_function):
        global camera_view_matrix
        global shader_texture, shader_common

        fps = FPS(1)

        glEnable(GL_DEPTH_TEST)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_BLEND)

        while not glfw.window_should_close(self.window):
            glfw.poll_events()
            do_movement()
            glClearColor(self.background_color_r, self.background_color_g,
                         self.background_color_b, self.background_color_alpha)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

            camera_view_matrix = cam.get_view_matrix()


            #glm::vec3 direction = glm::normalize(glm::vec3(0.0f, -1.0f, 1.0f));
            shader_texture.bind()
            uniform = glGetUniformLocation(shader_texture.get_shader(), "directionalLight.direction")
            glUniform3f(uniform, 0, -0.707107, 0.707107)
            uniform = glGetUniformLocation(shader_texture.get_shader(), "directionalLight.color")
            glUniform3f(uniform, 1.0, 1.0, 1.0)
            uniform = glGetUniformLocation(shader_texture.get_shader(), "directionalLight.ambientIntensity")
            glUniform1f(uniform, 0.1)
            uniform = glGetUniformLocation(shader_texture.get_shader(), "directionalLight.diffuseIntensity")
            glUniform1f(uniform, 1)
            uniform = glGetUniformLocation(shader_texture.get_shader(), "directionalLight.specularIntensity")
            glUniform1f(uniform, 1)
            #glUniform1f(programId, "directionalLight.ambientIntensity", float(directionalLightEnabled)*0.1f);
            #glUniform1f(programId, "directionalLight.diffuseIntensity", float(directionalLightEnabled)*0.1f);
            #glUniform1f(programId, "directionalLight.specularIntensity", float(directionalLightEnabled)*1.0f);

            user_function()

            glfw.swap_buffers(self.window)

            fps.update_and_print()
