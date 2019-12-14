import sys
import numpy as np
import random

sys.path.insert(1, '../')
import TRON
TRON.path_to_res_folder = "../"

my_window = TRON.Program()
my_window.create_window(name="Example 2", width=1920, height=1080)
helicopter = TRON.Object("res/textures/uh60/", "res/objects/uh60.obj")
instance_array = np.array([10, -1, 0], np.float32)
resize_array = np.array([1], np.float32)
rotation_array = np.array([3.14/2, 0, -3.14/2], np.float32)


angle = 3.14 / 2

light_source = TRON.DirectionalLight()
light_source2 = TRON.DirectionalLight()
light_source3 = TRON.DirectionalLight()
light_source4 = TRON.DirectionalLight()
light_source.describe([-10.0, 10, -7.5], [1, 1, 1], [0.1, 0.3, 1])
light_source2.describe([-10.0, 10, -2.5], [1, 1, 1], [0.1, 0.3, 1])
light_source3.describe([-10.0, 10, 2.5], [1, 1, 1], [0.1, 0.3, 1])
light_source4.describe([-10.0, 10, 7.5], [1, 1, 1], [0.1, 0.3, 1])


def user_function():
    global rotation_array, angle
    angle += 0.01
    rotation_array = np.array([angle, 0, -3.14 / 2], np.float32)
    helicopter.draw(rotation_array, instance_array, resize_array)

    light_source.update_shade_map()
    light_source2.update_shade_map()
    light_source3.update_shade_map()
    light_source4.update_shade_map()


my_window.background_color_r = 0.25
my_window.background_color_g = 0.25
my_window.background_color_b = 0.25

my_window.window_loop(user_function)

