import glfw

curX = -1
curY = -1
offset_x = 0
offset_y = 0

def mouse_callback(window, xpos, ypos):
    global curX, curY, offset_x, offset_y

    if curY != -1:
        offset_x = xpos - curX
        offset_y = curY - ypos

    curX = xpos
    curY = ypos

def drop_state():
    global offset_x, offset_y

    offset_x = 0
    offset_y = 0