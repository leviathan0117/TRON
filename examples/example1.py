import sys
import numpy

sys.path.insert(1, '../')
import TRON

TRON.main_context.path_to_res_folder = "../"

my_program = TRON.TronProgram()

cam_id = my_program.new_camera()

cam2_id = my_program.new_camera()

my_window = my_program.new_window(cam_id, name="TEST", width=1280, height=720)
my_window.add_camera(cam2_id)

fh = TRON.TronFileHandler()
fh.load_mtl("../res/objects/uh60.mtl", "../res/textures/uh60/")
s = fh.load_obj("../res/objects/uh60.obj")
helicopter = TRON.TronObject(s)
helicopter.rotation_array = numpy.array([3.14 / 2, 0, -3.14 / 2], numpy.float32)
helicopter.instance_array = numpy.array([10, -1, 0], numpy.float32)

l = TRON.TronDirectionalLight()
l.describe([0, 10, 0], [1, 1, 1], [0.1, 1, 1], [0.5, 0.2, 1])
#l.hided = 1
l2 = TRON.TronDirectionalLight()
l2.describe([-10.0, 10, 2.5], [1, 1, 1], [0.1, 1, 1], [0.5, 0.2, 1])
l2.hided = 1

angle, speed, acceleration, angle2 = 0, 0, 0, 0

fps = TRON.FPS(1)

for i in range(len(TRON.main_context.structures[s].subobjects)):
    print(TRON.main_context.structures[s].subobjects[i].name, i)

state = 0
state2 = 1

def user_function():
    global angle, s, speed, acceleration, fps, state, state2, angle2

    fps.update_and_print()

    rotation_array = numpy.array([0, angle, 0], numpy.float32)
    TRON.main_context.structures[s].subobjects[8].rotation_array = rotation_array

    if TRON.keyboard_handling.keys[TRON.glfw.KEY_P] == 1 and state == 0:
        state = 1
        if state2:
            my_window.choose_camera(iterator=1)
            state2 = 0
        else:
            my_window.choose_camera(iterator=0)
            state2 = 1

    elif TRON.keyboard_handling.keys[TRON.glfw.KEY_P] == 0 and state == 1:
        state = 0

    helicopter.rotation_array = numpy.array([3.14 / 2, 0, -3.14 / 2 - angle2], numpy.float32)

    angle += speed
    if speed < 0.3:
        speed += acceleration
        acceleration += 0.000001
    else:
        angle2 += 0.005
        if angle2 > 0.2:
            angle2 = 0.2


TRON.main_context.windows[0].user_function = user_function

my_program.main_loop()
