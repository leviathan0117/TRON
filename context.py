import shader_handling

class TronContext:
    def __init__(self):
        self.materials = []
        self.textures = []
        self.structures = []
        self.structures2D = []

        self.windows = []
        self.cameras = []

        self.objects = []
        self.objects2D = []
        self.lights = []
        self.num_active_lights = 0

        self.shader_texture = shader_handling.TronShader()
        self.shader_common = shader_handling.TronShader()
        self.shader_common_2d = shader_handling.TronShader()

        self.current_window = None
        self.current_camera = None

        self.path_to_res_folder = ""

    def activate(self):
        self.load_shaders()

    def load_shaders(self):
        self.shader_common_2d.compile_shader(
            self.path_to_res_folder + "res/shaders/common_object_2d_vertex_shader.glsl",
            self.path_to_res_folder + "res/shaders/common_object_2d_fragment_shader.glsl")
        self.shader_texture.compile_shader(
            self.path_to_res_folder + "res/shaders/textured_object_vertex_shader.glsl",
            self.path_to_res_folder + "res/shaders/textured_object_fragment_shader.glsl")
        self.shader_common.compile_shader(
            self.path_to_res_folder + "res/shaders/common_object_vertex_shader.glsl",
            self.path_to_res_folder + "res/shaders/common_object_fragment_shader.glsl")


main_context = TronContext()