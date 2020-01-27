from OpenGL.GL import *
import numpy
import context
from PIL import Image

class TronMaterial:
    def __init__(self):
        self.id = len(context.main_context.materials)

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
        self.id = len(context.main_context.textures)
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
        glBindVertexArray(self.vao)
        if context.main_context.materials[self.material_id].texture_id is not None:
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
        self.id = len(context.main_context.structures)

        self.subobjects = []
