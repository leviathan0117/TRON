import sys
import numpy

sys.path.insert(1, '../')
import TRON
TRON.path_to_res_folder = "../"

my_window = TRON.Program()
my_window.create_window(name="Example 2", width=1920, height=1080)

helicopter = TRON.Object("res/textures/uh60/", "res/objects/uh60.obj")

object_array_size = 1

instance_array = numpy.zeros((object_array_size, 3))
for x in range(0, object_array_size, 1):
    instance_array[x][0] = 5
    instance_array[x][1] = 0
    instance_array[x][2] = x * 2
instance_array = numpy.array(instance_array, numpy.float32).flatten()

resize_array = numpy.zeros(object_array_size, numpy.float32)
for x in range(0, object_array_size, 1):
    resize_array[x] = 1

a1 = 0
a2 = 0
a3 = -3.14/2


def user_function():
    global a1, a2, a3

    if TRON.keys[TRON.glfw.KEY_R]:
        a1 += 0.1
    if TRON.keys[TRON.glfw.KEY_F]:
        a1 -= 0.1
    if TRON.keys[TRON.glfw.KEY_T]:
        a2 += 0.1
    if TRON.keys[TRON.glfw.KEY_G]:
        a2 -= 0.1
    if TRON.keys[TRON.glfw.KEY_Y]:
        a3 += 0.1
    if TRON.keys[TRON.glfw.KEY_H]:
        a3 -= 0.1

    rotation_array = numpy.zeros((object_array_size, 3))
    for i in range(0, object_array_size, 1):
        # Rotations IN THE WAY THEY'RE APPLIED!!!
        # local pitch
        rotation_array[x][0] = a1
        # local yaw
        rotation_array[x][1] = a2
        # local roll
        rotation_array[x][2] = a3

    rotation_array = numpy.array(rotation_array, numpy.float32).flatten()

    helicopter.draw(rotation_array, instance_array, resize_array)


my_window.background_color_r = 0.5
my_window.background_color_g = 0.5
my_window.background_color_b = 0.5

my_window.window_loop(user_function)
