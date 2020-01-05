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
aspect_ratio = None
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

    camera_projection_matrix = pyrr.matrix44.create_perspective_projection_matrix(60.0, aspect_ratio, 0.001, 1000.0)


cam = Camera()
camera_view_matrix = cam.get_view_matrix()
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


class TronContext:
    def __init__(self):
        self.materials = []
        self.textures = []
        self.structures = []

        self.windows = []

        self.objects = []
        self.lights = []

        self.shader_texture = TronShader()
        self.shader_common = TronShader()

        self.current_window = None

    def activate(self):
        self.load_shaders()

    def load_shaders(self):
        self.shader_texture.compile_shader("res/shaders/textured_object_vertex_shader.glsl",
                                           "res/shaders/textured_object_fragment_shader.glsl")
        self.shader_common.compile_shader("res/shaders/common_object_vertex_shader.glsl",
                                          "res/shaders/common_object_fragment_shader.glsl")


main_context = TronContext()


class TronMaterial:
    def __init__(self):
        global main_context

        self.id = len(main_context.materials)

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

        self.texture_id = None


class TronTexture:
    def __init__(self):
        global main_context

        self.id = len(main_context.textures)
        self.opengl_id = glGenTextures(1)
        self.name = None

    def load(self, file_location):
        self.name = file_location
        glBindTexture(GL_TEXTURE_2D, self.opengl_id)
        # Set the texture wrapping parameters
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        # Set texture filtering parameters
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        # load image
        image = Image.open(file_location)
        # TODO: speed up this line:
        img_data = numpy.array(list(image.getdata()), numpy.uint8)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, image.width, image.height, 0, GL_RGB, GL_UNSIGNED_BYTE, img_data)
        glBindTexture(GL_TEXTURE_2D, 0)

        return self.id

    def bind(self):
        glBindTexture(GL_TEXTURE_2D, self.opengl_id)


class TronPart:
    def __init__(self):
        self.material_id = None
        self.points = []

        self.vao = glGenVertexArrays(1)
        self.points_vbo = glGenBuffers(1)
        self.instance_vbo = glGenBuffers(1)
        self.rotation_vbo = glGenBuffers(1)
        self.resize_vbo = glGenBuffers(1)

        self.rotation_array = numpy.array([0, 0, 0], numpy.float32)
        self.instance_array = numpy.array([0, 0, 0], numpy.float32)
        self.resize_array = numpy.array([1], numpy.float32)

        self.rotation_array_previous = numpy.array([0, 0, 0], numpy.float32)
        self.instance_array_previous = numpy.array([0, 0, 0], numpy.float32)
        self.resize_array_previous = numpy.array([0], numpy.float32)

    def fill_buffers(self):
        global main_context

        glBindVertexArray(self.vao)
        if main_context.materials[self.material_id].texture_id is not None:
            glBindBuffer(GL_ARRAY_BUFFER, self.points_vbo)
            glBufferData(GL_ARRAY_BUFFER,
                         self.points.itemsize * len(self.points),
                         self.points, GL_STATIC_DRAW)
            # position - 0
            glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, self.points.itemsize * 8,
                                  ctypes.c_void_p(0))
            glEnableVertexAttribArray(0)
            # textures - 1
            glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, self.points.itemsize * 8,
                                  ctypes.c_void_p(3 * 4))
            glEnableVertexAttribArray(1)
            # normals - 2
            glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, self.points.itemsize * 8,
                                  ctypes.c_void_p((3 + 2) * 4))
            glEnableVertexAttribArray(2)
        else:
            glBindBuffer(GL_ARRAY_BUFFER, self.points_vbo)
            glBufferData(GL_ARRAY_BUFFER,
                         self.points.itemsize * len(self.points),
                         self.points, GL_STATIC_DRAW)
            # position - 0
            glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, self.points.itemsize * 10,
                                  ctypes.c_void_p(0))
            glEnableVertexAttribArray(0)
            # color - 1
            glVertexAttribPointer(1, 4, GL_FLOAT, GL_FALSE, self.points.itemsize * 10,
                                  ctypes.c_void_p(3 * 4))
            glEnableVertexAttribArray(1)
            # normals - 2
            glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, self.points.itemsize * 10,
                                  ctypes.c_void_p((3 + 4) * 4))
            glEnableVertexAttribArray(2)

        glBindBuffer(GL_ARRAY_BUFFER, self.instance_vbo)
        # instance - 3
        glVertexAttribPointer(3, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glEnableVertexAttribArray(3)
        glVertexAttribDivisor(3, 1)

        glBindBuffer(GL_ARRAY_BUFFER, self.rotation_vbo)
        # rotation - 4
        glVertexAttribPointer(4, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glEnableVertexAttribArray(4)
        glVertexAttribDivisor(4, 1)

        glBindBuffer(GL_ARRAY_BUFFER, self.resize_vbo)
        # resize - 5
        glVertexAttribPointer(5, 1, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glEnableVertexAttribArray(5)
        glVertexAttribDivisor(5, 1)

        self.update_buffers()

    def update_buffers(self):
        glBindVertexArray(self.vao)
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


class TronSubobject:
    def __init__(self):
        self.delta_position = [0.0, 0.0, 0.0]
        self.delta_rotation = [0.0, 0.0, 0.0]
        self.delta_size = 1.0
        self.parts = []
        self.name = None
        self.count_parts = 0


class TronStructure:
    def __init__(self):
        global main_context

        self.id = len(main_context.structures)

        self.subobjects = []


class TronFileHandler:
    def __init__(self):
        pass

    def load_mtl(self, file_location, texture_directory_location):
        global main_context

        last_it = -1

        ids = []

        for line in open(file_location, "r"):
            # delete the ending '\n'
            line = line.replace("\n", "")

            if line.startswith("#"):
                continue
            elif line.startswith("newmtl"):
                main_context.materials.append(TronMaterial())
                ids.append(main_context.materials[-1].id)
                last_it += 1

                value = line.split(" ")[1]
                main_context.materials[-1].name = value
            elif line.startswith("Ns"):
                value = line.split(" ")[1]
                main_context.materials[-1].ns = float(value)
            elif line.startswith("Ka"):
                values = line.split(" ")
                main_context.materials[-1].ka.append(float(values[1]))
                main_context.materials[-1].ka.append(float(values[2]))
                main_context.materials[-1].ka.append(float(values[3]))
            elif line.startswith("Kd"):
                values = line.split(" ")
                main_context.materials[-1].kd.append(float(values[1]))
                main_context.materials[-1].kd.append(float(values[2]))
                main_context.materials[-1].kd.append(float(values[3]))
            elif line.startswith("Ks"):
                values = line.split(" ")
                main_context.materials[-1].ks.append(float(values[1]))
                main_context.materials[-1].ks.append(float(values[2]))
                main_context.materials[-1].ks.append(float(values[3]))
            elif line.startswith("Ni"):
                value = line.split(" ")[1]
                main_context.materials[-1].ni = float(value)
            elif line.startswith("d"):
                value = line.split(" ")[1]
                main_context.materials[-1].d = float(value)
            elif line.startswith("illum"):
                value = line.split(" ")[1]
                main_context.materials[-1].illum = int(value)
            elif line.startswith("map_Kd"):
                value = line.split(" ")[1]
                main_context.materials[-1].map_kd = value

        for i in ids:
            mat = main_context.materials[i]
            if mat.map_kd != "":
                main_context.textures.append(TronTexture())
                main_context.textures[-1].load(texture_directory_location + mat.map_kd)
                mat.texture_id = main_context.textures[-1].id

    def load_obj(self, file_location):
        global main_context

        main_context.structures.append(TronStructure())
        current_object = main_context.structures[-1]

        keep_alive_counter = 0

        tmp_vertex_coordinates = []
        tmp_texture_coordinates = []
        tmp_normal_coordinates = []

        state = 0
        current_material_name = 0
        current_material = None

        for line in open(file_location, 'r'):
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
                current_object.subobjects.append(TronSubobject())
                current_object.subobjects[-1].name = data[1]
                state = 1

            # Subpart handling:
            if data[0] == "f" and state:
                current_object.subobjects[-1].parts.append(TronPart())
                for i in range(len(main_context.materials)):
                    if main_context.materials[i].name == current_material_name:
                        current_object.subobjects[-1].parts[-1].material_id = i
                        current_material = main_context.materials[i]
                state = 0
            if data[0] == "f":
                if current_material.map_kd is not "":
                    indexes = data[1].split("/")
                    current_object.subobjects[-1].parts[-1].points.extend(tmp_vertex_coordinates[int(indexes[0]) - 1])
                    current_object.subobjects[-1].parts[-1].points.extend(tmp_texture_coordinates[int(indexes[1]) - 1])
                    current_object.subobjects[-1].parts[-1].points.extend(tmp_normal_coordinates[int(indexes[2]) - 1])
                    indexes = data[2].split("/")
                    current_object.subobjects[-1].parts[-1].points.extend(tmp_vertex_coordinates[int(indexes[0]) - 1])
                    current_object.subobjects[-1].parts[-1].points.extend(tmp_texture_coordinates[int(indexes[1]) - 1])
                    current_object.subobjects[-1].parts[-1].points.extend(tmp_normal_coordinates[int(indexes[2]) - 1])
                    indexes = data[3].split("/")
                    current_object.subobjects[-1].parts[-1].points.extend(tmp_vertex_coordinates[int(indexes[0]) - 1])
                    current_object.subobjects[-1].parts[-1].points.extend(tmp_texture_coordinates[int(indexes[1]) - 1])
                    current_object.subobjects[-1].parts[-1].points.extend(tmp_normal_coordinates[int(indexes[2]) - 1])
                    if len(data) == 5:
                        indexes = data[3].split("/")
                        current_object.subobjects[-1].parts[-1].points.extend(
                            tmp_vertex_coordinates[int(indexes[0]) - 1])
                        current_object.subobjects[-1].parts[-1].points.extend(
                            tmp_texture_coordinates[int(indexes[1]) - 1])
                        current_object.subobjects[-1].parts[-1].points.extend(
                            tmp_normal_coordinates[int(indexes[2]) - 1])
                        indexes = data[4].split("/")
                        current_object.subobjects[-1].parts[-1].points.extend(
                            tmp_vertex_coordinates[int(indexes[0]) - 1])
                        current_object.subobjects[-1].parts[-1].points.extend(
                            tmp_texture_coordinates[int(indexes[1]) - 1])
                        current_object.subobjects[-1].parts[-1].points.extend(
                            tmp_normal_coordinates[int(indexes[2]) - 1])
                        indexes = data[1].split("/")
                        current_object.subobjects[-1].parts[-1].points.extend(
                            tmp_vertex_coordinates[int(indexes[0]) - 1])
                        current_object.subobjects[-1].parts[-1].points.extend(
                            tmp_texture_coordinates[int(indexes[1]) - 1])
                        current_object.subobjects[-1].parts[-1].points.extend(
                            tmp_normal_coordinates[int(indexes[2]) - 1])
                # This is when we don't need vertices
                else:
                    color = [current_material.kd[0], current_material.kd[1], current_material.kd[2], current_material.d]
                    indexes = data[1].split("/")
                    current_object.subobjects[-1].parts[-1].points.extend(tmp_vertex_coordinates[int(indexes[0]) - 1])
                    current_object.subobjects[-1].parts[-1].points.extend(color)
                    current_object.subobjects[-1].parts[-1].points.extend(tmp_normal_coordinates[int(indexes[2]) - 1])
                    indexes = data[2].split("/")
                    current_object.subobjects[-1].parts[-1].points.extend(tmp_vertex_coordinates[int(indexes[0]) - 1])
                    current_object.subobjects[-1].parts[-1].points.extend(color)
                    current_object.subobjects[-1].parts[-1].points.extend(tmp_normal_coordinates[int(indexes[2]) - 1])
                    indexes = data[3].split("/")
                    current_object.subobjects[-1].parts[-1].points.extend(tmp_vertex_coordinates[int(indexes[0]) - 1])
                    current_object.subobjects[-1].parts[-1].points.extend(color)
                    current_object.subobjects[-1].parts[-1].points.extend(tmp_normal_coordinates[int(indexes[2]) - 1])
                    if len(data) == 5:
                        indexes = data[3].split("/")
                        current_object.subobjects[-1].parts[-1].points.extend(
                            tmp_vertex_coordinates[int(indexes[0]) - 1])
                        current_object.subobjects[-1].parts[-1].points.extend(color)
                        current_object.subobjects[-1].parts[-1].points.extend(
                            tmp_normal_coordinates[int(indexes[2]) - 1])
                        indexes = data[4].split("/")
                        current_object.subobjects[-1].parts[-1].points.extend(
                            tmp_vertex_coordinates[int(indexes[0]) - 1])
                        current_object.subobjects[-1].parts[-1].points.extend(color)
                        current_object.subobjects[-1].parts[-1].points.extend(
                            tmp_normal_coordinates[int(indexes[2]) - 1])
                        indexes = data[1].split("/")
                        current_object.subobjects[-1].parts[-1].points.extend(
                            tmp_vertex_coordinates[int(indexes[0]) - 1])
                        current_object.subobjects[-1].parts[-1].points.extend(color)
                        current_object.subobjects[-1].parts[-1].points.extend(
                            tmp_normal_coordinates[int(indexes[2]) - 1])

        for sub in current_object.subobjects:
            sub.count_parts = len(sub.parts)
            for part in sub.parts:
                part.points = numpy.array(part.points, dtype=numpy.float32).flatten()

        for sub in current_object.subobjects:
            for part in sub.parts:
                part.fill_buffers()

        return current_object.id


class TronObject:
    def __init__(self, structure_id):
        global main_context

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

        main_context.objects.append(self)

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
        global main_context

        struct = main_context.structures[self.structure_id]

        for i in struct.subobjects:
            for j in i.parts:
                glBindVertexArray(j.vao)
                j.update_buffers()
                self.describe_buffers()
                self.update_buffers()
                count_objects = 1
                glDrawArraysInstanced(GL_TRIANGLES, 0, len(j.points), count_objects)

    def real_draw(self):
        global camera_projection_matrix, camera_view_matrix
        global main_context
        global cam
        camera_view_matrix = cam.get_view_matrix()

        main_context.shader_texture.bind()
        uniform = glGetUniformLocation(main_context.shader_texture.get_shader(), "num_active_lights")
        glUniform1i(uniform, len(main_context.lights))
        for i in range(len(main_context.lights)):
            main_context.lights[i].set_shader_uniforms(main_context.shader_texture, i, 1)
        glUniformMatrix4fv(main_context.shader_texture.view_uniform_location, 1, GL_FALSE, camera_view_matrix)
        glUniformMatrix4fv(main_context.shader_texture.projection_uniform_location, 1, GL_FALSE,
                           camera_projection_matrix)
        glUniform1i(glGetUniformLocation(main_context.shader_texture.get_shader(), "tex_sampler"), 0)
        for k in range(len(main_context.lights)):
            glUniform1i(glGetUniformLocation(main_context.shader_texture.get_shader(),
                        "shadowMap[" + str(k) + "]"), k + 1)
        textures_array = []
        for i in main_context.lights:
            textures_array.append(i.depth_map)
        glBindTextures(1, len(main_context.lights), textures_array)

        struct = main_context.structures[self.structure_id]

        for i in struct.subobjects:
            for j in i.parts:
                if main_context.materials[j.material_id].texture_id is not None:
                    main_context.shader_texture.bind()
                    glActiveTexture(GL_TEXTURE0)
                    main_context.textures[main_context.materials[j.material_id].texture_id].bind()

                    glBindVertexArray(j.vao)
                    j.update_buffers()
                    self.describe_buffers()
                    self.update_buffers()

                    count_objects = 1
                    glDrawArraysInstanced(GL_TRIANGLES, 0, len(j.points), count_objects)

        main_context.shader_common.bind()
        uniform = glGetUniformLocation(main_context.shader_common.get_shader(), "num_active_lights")
        glUniform1i(uniform, len(main_context.lights))
        for i in range(len(main_context.lights)):
            main_context.lights[i].set_shader_uniforms(main_context.shader_common, i, 0)

        glUniformMatrix4fv(main_context.shader_common.view_uniform_location, 1, GL_FALSE, camera_view_matrix)
        glUniformMatrix4fv(main_context.shader_common.projection_uniform_location, 1, GL_FALSE,
                           camera_projection_matrix)
        for i in struct.subobjects:
            for j in i.parts:
                if main_context.materials[j.material_id].texture_id is None:
                    main_context.shader_common.bind()
                    glBindVertexArray(j.vao)
                    j.update_buffers()
                    self.describe_buffers()
                    self.update_buffers()

                    count_objects = 1
                    glDrawArraysInstanced(GL_TRIANGLES, 0, len(j.points), count_objects)

    def draw(self, rotation_array, instance_array, resize_array):
        self.rotation_array = rotation_array
        self.instance_array = instance_array
        self.resize_array = resize_array


class TronDirectionalLight:
    def __init__(self):
        global main_context

        self.id = len(main_context.lights)
        main_context.lights.append(self)

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

        self.depth_shader = TronShader()
        self.depth_shader.compile_shader("res/shaders/shadow_fill_vertex_shader.glsl",
                                         "res/shaders/shadow_fill_fragment_shader.glsl")
        self.draw_shader = TronShader()
        self.draw_shader.compile_shader("res/shaders/shadow_draw_vertex_shader.glsl",
                                        "res/shaders/shadow_draw_fragment_shader.glsl")

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
        global main_context
        # Matrices:
        near_plane = 1.0
        far_plane = 100.0

        self.shadow_projection_matrix = \
            pyrr.matrix44.create_orthogonal_projection_matrix(-20.0, 20.0, -20.0, 20.0, near_plane, far_plane)
        self.shadow_view_matrix = pyrr.matrix44.create_look_at(self.position, [0.0, 0.0, 0.0], [0.0, 1.0, 0.0])

        # shadow draw:
        self.depth_shader.bind()
        glUniformMatrix4fv(self.depth_shader.view_uniform_location, 1, GL_FALSE, self.shadow_view_matrix)
        glUniformMatrix4fv(self.depth_shader.projection_uniform_location, 1, GL_FALSE, self.shadow_projection_matrix)

        glViewport(0, 0, self.shadow_map_width, self.shadow_map_height)
        glBindFramebuffer(GL_FRAMEBUFFER, self.depth_map_fbo)
        glClear(GL_DEPTH_BUFFER_BIT)

        for item in main_context.objects:
            if item.hided == 0:
                item.shade_draw()

        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        window_width = main_context.windows[main_context.current_window].window_width
        window_height = main_context.windows[main_context.current_window].window_height
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
        glUniform3f(uniform, cam.camera_pos[0], cam.camera_pos[1], cam.camera_pos[2])


class TronWindow:
    def __init__(self, **kwargs):
        global main_context

        self.id = len(main_context.windows)
        # OpenGL ID:
        self.opengl_id = None
        self.window_name = None
        self.window_width = None
        self.window_height = None

        self.background_color_r = 0.0
        self.background_color_g = 0.0
        self.background_color_b = 0.0
        self.background_color_alpha = 1.0

        self.create(**kwargs)

        main_context.load_shaders()

        def sample_function():
            pass

        self.user_function = sample_function

        self.time_pr = time.time_ns()
        self.total_ms = 0
        self.total_frames = 0

    def create(self, **kwargs):
        self.window_width = kwargs.get('width', 800)
        self.window_height = kwargs.get('height', 600)
        self.window_name = kwargs.get('name', "My OpenGL window")
        self.opengl_id = glfw.create_window(self.window_width, self.window_height, self.window_name, None, None)

        glfw.set_window_size_callback(self.opengl_id, window_resize)
        glfw.set_key_callback(self.opengl_id, key_callback)
        glfw.set_cursor_pos_callback(self.opengl_id, mouse_callback)
        glfw.set_input_mode(self.opengl_id, glfw.CURSOR, glfw.CURSOR_DISABLED)

        global cam
        cam.turn_camera(0, 0)

        if not self.opengl_id:
            print("(!) TRON FATAL ERROR: Failed to create a window")
            glfw.terminate()
            sys.exit(2)

        self.activate()

        window_resize(0, self.window_width, self.window_height)
        glClearColor(self.background_color_r, self.background_color_g,
                     self.background_color_b, self.background_color_alpha)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glfw.swap_buffers(self.opengl_id)

    def activate(self):
        glfw.make_context_current(self.opengl_id)

    def draw(self):
        global main_context
        global cam, camera_view_matrix

        self.time_pr = time.time_ns()

        main_context.current_window = self.id

        self.activate()

        self.user_function()

        do_movement()
        camera_view_matrix = cam.get_view_matrix()
        glfw.poll_events()
        glClearColor(self.background_color_r, self.background_color_g,
                     self.background_color_b, self.background_color_alpha)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        for i in main_context.lights:
            if i.hided == 0:
                i.update_shade_map()

        glViewport(0, 0, self.window_width, self.window_height)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        for i in main_context.objects:
            if i.hided == 0:
                i.real_draw()

        glfw.swap_buffers(self.opengl_id)

        # TODO: make this not a exit, but just closing the window:
        if glfw.window_should_close(self.opengl_id):
            sys.exit(0)


        add = (time.time_ns() - self.time_pr) / 10**6
        self.total_ms += add
        self.total_frames += 1
        #print("TRON info: loop took ", add, " ms || AVG: ", self.total_ms/ self.total_frames)


class TronProgram:
    def __init__(self):
        if not glfw.init():
            print("(!) TRON FATAL ERROR: Failed to init GLFW!")
            sys.exit(1)

    def new_window(self, **kwargs):
        global main_context

        main_context.windows.append(TronWindow(**kwargs))

    def main_loop(self):
        global main_context

        glEnable(GL_DEPTH_TEST)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_BLEND)

        while True:
            for window in main_context.windows:
                window.draw()

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

