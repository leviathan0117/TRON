import sys
import numpy

sys.path.insert(1, '../')
import TRON

TRON.main_context.path_to_res_folder = "../"

bla = TRON.TronProgram()
bla.new_window(name="Example 1", width=1280, height=720)

fh = TRON.TronFileHandler()
fh.load_mtl("../res/objects/uh60.mtl", "../res/textures/uh60/")
s = fh.load_obj("../res/objects/uh60.obj")
helicopter = TRON.TronObject(s)
helicopter.rotation_array = numpy.array([3.14 / 2, 0, -3.14 / 2], numpy.float32)
helicopter.instance_array = numpy.array([10, -1, 0], numpy.float32)

l = TRON.TronDirectionalLight()
l.describe([-10.0, 10, -7.5], [1, 1, 1], [0.1, 1, 1], [0.5, 0, 1])
l2 = TRON.TronDirectionalLight()
l2.describe([-10.0, 10, 2.5], [1, 1, 1], [0.1, 1, 1], [0.5, 0, 1])

angle, speed, acceleration = 0, 0, 0

fps = TRON.FPS(1)

for i in range(len(TRON.main_context.structures[s].subobjects)):
    print(TRON.main_context.structures[s].subobjects[i].name, i)

def user_function():
    global angle, s, speed, acceleration, fps

    fps.update_and_print()

    rotation_array = numpy.array([0, angle, 0], numpy.float32)
    for i in TRON.main_context.structures[s].subobjects[8].parts:
        i.rotation_array = rotation_array

    angle += speed
    if speed < 0.1:
        speed += acceleration
        acceleration += 0.0000001

TRON.main_context.windows[0].user_function = user_function

bla.main_loop()
