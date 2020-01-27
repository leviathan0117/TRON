import context
import structure_handling
import glfw
import numpy

class TronFileHandler:
    def __init__(self):
        pass

    def load_mtl(self, file_location, texture_directory_location):
        last_it = -1

        ids = []

        for line in open(file_location, "r"):
            # delete the ending '\n'
            line = line.replace("\n", "")

            if line.startswith("#"):
                continue
            elif line.startswith("newmtl"):
                context.main_context.materials.append(structure_handling.TronMaterial())
                ids.append(context.main_context.materials[-1].id)
                last_it += 1

                value = line.split(" ")[1]
                context.main_context.materials[-1].name = value
            elif line.startswith("Ns"):
                value = line.split(" ")[1]
                context.main_context.materials[-1].ns = float(value)
            elif line.startswith("Ka"):
                values = line.split(" ")
                context.main_context.materials[-1].ka.append(float(values[1]))
                context.main_context.materials[-1].ka.append(float(values[2]))
                context.main_context.materials[-1].ka.append(float(values[3]))
            elif line.startswith("Kd"):
                values = line.split(" ")
                context.main_context.materials[-1].kd.append(float(values[1]))
                context.main_context.materials[-1].kd.append(float(values[2]))
                context.main_context.materials[-1].kd.append(float(values[3]))
            elif line.startswith("Ks"):
                values = line.split(" ")
                context.main_context.materials[-1].ks.append(float(values[1]))
                context.main_context.materials[-1].ks.append(float(values[2]))
                context.main_context.materials[-1].ks.append(float(values[3]))
            elif line.startswith("Ni"):
                value = line.split(" ")[1]
                context.main_context.materials[-1].ni = float(value)
            elif line.startswith("d"):
                value = line.split(" ")[1]
                context.main_context.materials[-1].d = float(value)
            elif line.startswith("illum"):
                value = line.split(" ")[1]
                context.main_context.materials[-1].illum = int(value)
            elif line.startswith("map_Kd"):
                value = line.split(" ")[1]
                context.main_context.materials[-1].map_kd = value

        for i in ids:
            mat = context.main_context.materials[i]
            if mat.map_kd != "":
                context.main_context.textures.append(structure_handling.TronTexture())
                context.main_context.textures[-1].load(texture_directory_location + mat.map_kd)
                mat.texture_id = context.main_context.textures[-1].id

    def load_obj(self, file_location):

        context.main_context.structures.append(structure_handling.TronStructure())
        current_object = context.main_context.structures[-1]

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
                current_object.subobjects.append(structure_handling.TronSubobject())
                current_object.subobjects[-1].name = data[1]
                state = 1

            # Subpart handling:
            if data[0] == "f" and state:
                current_object.subobjects[-1].parts.append(structure_handling.TronPart())
                for i in range(len(context.main_context.materials)):
                    if context.main_context.materials[i].name == current_material_name:
                        current_object.subobjects[-1].parts[-1].material_id = i
                        current_material = context.main_context.materials[i]
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

