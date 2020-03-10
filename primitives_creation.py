import context
import structure_handling
import numpy

def create_rectangle_struct():
    context.main_context.structures2D.append(structure_handling.TronStructure2D())
    struct = context.main_context.structures2D[-1]

    struct.subobjects.append(structure_handling.TronSubobject2D())
    struct.subobjects[0].parts.append(structure_handling.TronPart2D())

    part = struct.subobjects[0].parts[0]

    tmp_vertex_coordinates = []
    tmp_vertex_color = []

    tmp_vertex_coordinates.append([-1.0, -1.0])
    tmp_vertex_coordinates.append([-0.5, -1.0])
    tmp_vertex_coordinates.append([-0.5, -0.5])
    tmp_vertex_coordinates.append([-1.0, -1.0])
    tmp_vertex_coordinates.append([-0.5, -0.5])
    tmp_vertex_coordinates.append([-1.0, -0.5])

    tmp_vertex_color.append([1.0, 0.0, 0.0, 1.0])
    tmp_vertex_color.append([0.0, 1.0, 0.0, 1.0])
    tmp_vertex_color.append([0.0, 0.0, 1.0, 1.0])
    tmp_vertex_color.append([1.0, 0.0, 0.0, 1.0])
    tmp_vertex_color.append([0.0, 0.0, 1.0, 1.0])
    tmp_vertex_color.append([1.0, 1.0, 1.0, 1.0])

    points = []
    points.extend(tmp_vertex_coordinates[0])
    points.extend(tmp_vertex_color[0])
    points.extend(tmp_vertex_coordinates[1])
    points.extend(tmp_vertex_color[1])
    points.extend(tmp_vertex_coordinates[2])
    points.extend(tmp_vertex_color[2])
    points.extend(tmp_vertex_coordinates[3])
    points.extend(tmp_vertex_color[3])
    points.extend(tmp_vertex_coordinates[4])
    points.extend(tmp_vertex_color[4])
    points.extend(tmp_vertex_coordinates[5])
    points.extend(tmp_vertex_color[5])

    print(points)
    part.points = numpy.array(points, dtype=numpy.float32).flatten()
    print(part.points)

    part.fill_buffers()

    return struct.id
