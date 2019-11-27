import sys
import numpy

sys.path.insert(1, '../')
import TRON
TRON.path_to_res_folder = "../"

my_window = TRON.Program()
my_window.create_window(name="Example 1", width=1920, height=1080)

cubes = TRON.TexturedCubes()

angle = 0
cube_array_size = 20

instance_array = numpy.zeros((cube_array_size ** 3, 3))
for x in range(0, cube_array_size, 1):
    for y in range(0, cube_array_size, 1):
        for z in range(0, cube_array_size, 1):
            instance_array[x * cube_array_size ** 2 + y * cube_array_size + z][0] = z * 2
            instance_array[x * cube_array_size ** 2 + y * cube_array_size + z][1] = y * 2
            instance_array[x * cube_array_size ** 2 + y * cube_array_size + z][2] = x * 2
instance_array = numpy.array(instance_array, numpy.float32).flatten()

resize_array = numpy.zeros(cube_array_size ** 3, numpy.float32)
for x in range(0, cube_array_size, 1):
    for y in range(0, cube_array_size, 1):
        for z in range(0, cube_array_size, 1):
            resize_array[x * cube_array_size ** 2 + y * cube_array_size + z] = 0.1 + (x + y + z) / cube_array_size / 3 * 0.4


def user_function():
    global angle, cubes

    angle += 0.01

    rotation_array = numpy.zeros((cube_array_size ** 3, 3))
    for x in range(0, cube_array_size, 1):
        for y in range(0, cube_array_size, 1):
            for z in range(0, cube_array_size, 1):
                rotation_array[x * cube_array_size ** 2 + y * cube_array_size + z][0] = x * angle
                rotation_array[x * cube_array_size ** 2 + y * cube_array_size + z][1] = y * angle
                rotation_array[x * cube_array_size ** 2 + y * cube_array_size + z][2] = z * angle
    rotation_array = numpy.array(rotation_array, numpy.float32).flatten()

    cubes.draw(rotation_array, instance_array, resize_array)


my_window.window_loop(user_function)
