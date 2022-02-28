import bpy
import dotbimpy
import numpy as np
import bmesh
import uuid
from collections import defaultdict


def triangulate_mesh(mesh):
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.to_mesh(mesh)
    bm.free()


def convert_blender_mesh_to_dotbim(blender_mesh, index):
    vertices = np.empty(shape=len(blender_mesh.vertices) * 3, dtype=float)
    blender_mesh.vertices.foreach_get("co", vertices)

    triangulate_mesh(blender_mesh)
    faces = np.empty(shape=len(blender_mesh.polygons) * 3, dtype=int)
    blender_mesh.polygons.foreach_get("vertices", faces)

    return dotbimpy.Mesh(mesh_id=index, coordinates=vertices.tolist(), indices=faces.tolist())


def get_all_ui_props(obj):
    items = obj.items()
    rna_properties = {prop.identifier for prop in obj.bl_rna.properties if prop.is_runtime}
    for k, v in items:
        if k in rna_properties:
            continue
        yield (k, v)


def export_objects(objs, filepath):
    meshes = []
    elements = []

    data_users = defaultdict(list)
    depsgraph = bpy.context.evaluated_depsgraph_get()

    for obj in objs:
        if obj.type not in ("MESH", "CURVE", "FONT", "META", "SURFACE"):
            continue
        if obj.modifiers:
            data_users[obj].append(obj)
        else:
            data_users[obj.data].append(obj)
    for i, (_, users) in enumerate(data_users.items()):
        mesh = convert_blender_mesh_to_dotbim(users[0].evaluated_get(depsgraph).data, i)
        meshes.append(mesh)

        for obj in users:
            r, g, b, a = obj.color
            color = dotbimpy.Color(r=r * 255, g=g * 255, b=b * 255, a=a * 255)

            guid = str(uuid.uuid4())

            info = {"Name": obj.name}
            for custom_prop_name, custom_prop_value in get_all_ui_props(obj):
                info[custom_prop_name] = str(custom_prop_value)

            matrix_world = obj.matrix_world
            obj_trans = matrix_world.to_translation()
            obj_quat = matrix_world.to_quaternion()

            rotation = dotbimpy.Rotation(qx=obj_quat.x, qy=obj_quat.y, qz=obj_quat.z, qw=obj_quat.w)
            type = "Structure"
            vector = dotbimpy.Vector(x=obj_trans.x, y=obj_trans.y, z=obj_trans.z)
            element = dotbimpy.Element(
                mesh_id=i, vector=vector, guid=guid, info=info, rotation=rotation, type=type, color=color
            )

            elements.append(element)

    file_info = {"Author": "John Doe", "Date": "28.09.1999"}

    file = dotbimpy.File("1.0.0", meshes=meshes, elements=elements, info=file_info)
    file.save(filepath)


if __name__ == "__main__":
    objects = bpy.context.selected_objects
    export_objects(objs=objects, filepath=r'House.bim')
