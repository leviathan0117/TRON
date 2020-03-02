import glfw
import pyrr
import math

import context
import keyboard_handling


class TronCamera:
    def __init__(self):
        self.id = len(context.main_context.cameras)

        self.camera_pos = pyrr.Vector3([0.0, 0.0, 0.0])
        self.camera_front = pyrr.Vector3([0.0, 0.0, -1.0])
        self.camera_up = pyrr.Vector3([0.0, 1.0, 0.0])
        self.camera_right = pyrr.Vector3([1.0, 0.0, 0.0])

        self.mouse_sensitivity = 0.25
        self.movement_speed = 0.1
        self.yaw = 0.0
        self.pitch = 0.0

        self.first_mouse = True
        self.lastX = None
        self.lastY = None

        self.camera_projection_matrix = None
        self.camera_view_matrix = None

    def get_view_matrix(self):
        return pyrr.matrix44.create_look_at(self.camera_pos, self.camera_pos + self.camera_front, self.camera_up)

    def process_keyboard(self):
        if keyboard_handling.keys[glfw.KEY_W]:
            self.camera_pos += self.camera_front * self.movement_speed
        if keyboard_handling.keys[glfw.KEY_S]:
            self.camera_pos -= self.camera_front * self.movement_speed
        if keyboard_handling.keys[glfw.KEY_A]:
            self.camera_pos -= self.camera_right * self.movement_speed
        if keyboard_handling.keys[glfw.KEY_D]:
            self.camera_pos += self.camera_right * self.movement_speed
        if keyboard_handling.keys[glfw.KEY_SPACE]:
            self.camera_pos += self.camera_up * self.movement_speed
        if keyboard_handling.keys[glfw.KEY_C]:
            self.camera_pos -= self.camera_up * self.movement_speed

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

    def mouse_callback(self, window, xpos, ypos):
        if self.first_mouse:
            self.lastX = xpos
            self.lastY = ypos
            self.first_mouse = False

        offset_x = xpos - self.lastX
        offset_y = self.lastY - ypos

        self.lastX = xpos
        self.lastY = ypos

        self.turn_camera(offset_x, offset_y)
