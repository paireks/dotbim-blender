import uuid
from datetime import date
from collections import defaultdict
import numpy as np
import dotbimpy
import bpy
import bmesh
import re


def triangulate_mesh(mesh):
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.to_mesh(mesh)
    bm.free()


class BlenderToDotbimConverter:
    def __init__(self, mesh_blender) -> None:
        self.mesh_blender = mesh_blender

    def convert(self, index, transform_matrix):
        mesh_blender = self.mesh_blender
        active_color_attribute = mesh_blender.color_attributes.active_color
        if (
            active_color_attribute
            and active_color_attribute.domain == "CORNER"
            and active_color_attribute.data_type == "FLOAT_COLOR"
        ):
            face_colors = []
            for polygon in mesh_blender.polygons:
                face_colors.extend(active_color_attribute.data[polygon.loop_start].color)
            face_colors = [int(c * 255) for c in face_colors]
        else:
            face_colors = None

        vertices = np.empty(shape=len(mesh_blender.vertices) * 3, dtype=float)
        mesh_blender.vertices.foreach_get("co", vertices)
        scale = transform_matrix.to_scale()
        for i in range(3):
            vertices[i::3] *= scale[i]

        triangulate_mesh(mesh_blender)
        faces = np.empty(shape=len(mesh_blender.polygons) * 3, dtype=int)
        mesh_blender.polygons.foreach_get("vertices", faces)

        self.mesh_dotbim = dotbimpy.Mesh(mesh_id=index, coordinates=vertices.tolist(), indices=faces.tolist())
        self.face_colors = face_colors


def get_all_ui_props(obj):
    items = obj.items()
    rna_properties = {prop.identifier for prop in obj.bl_rna.properties if prop.is_runtime}
    for k, v in items:
        if k in rna_properties:
            continue
        yield (k, v)


def export_objects(objs, filepath, author="John Doe", type_from="NAME"):
    meshes = []
    elements = []

    data_users = defaultdict(list)
    depsgraph = bpy.context.evaluated_depsgraph_get()

    for obj in objs:
        if obj.type not in ("MESH", "CURVE", "FONT", "META", "SURFACE"):
            continue
        if obj.modifiers or obj.scale[0] != 1 or obj.scale[1] != 1 or obj.scale[2] != 1:
            data_users[obj].append(obj)
        else:
            data_users[obj.data].append(obj)
    for i, users in enumerate(data_users.values()):
        base_obj = users[0]
        mesh_blender = base_obj.evaluated_get(depsgraph).to_mesh()  # Apply visual modifiers, transforms, etc.
        transform_matrix = base_obj.matrix_world
        converter = BlenderToDotbimConverter(mesh_blender)
        converter.convert(i, transform_matrix)
        mesh_dotbim = converter.mesh_dotbim
        face_colors = converter.face_colors

        meshes.append(mesh_dotbim)

        for obj in users:
            r, g, b, a = obj.color
            color = dotbimpy.Color(r=int(r * 255), g=int(g * 255), b=int(b * 255), a=int(a * 255))

            guid = str(uuid.uuid4())

            info = {"Name": obj.name}
            for custom_prop_name, custom_prop_value in get_all_ui_props(obj):
                info[custom_prop_name] = str(custom_prop_value)

            matrix_world = obj.matrix_world
            obj_trans = matrix_world.to_translation()
            obj_quat = matrix_world.to_quaternion()

            rotation = dotbimpy.Rotation(qx=obj_quat.x, qy=obj_quat.y, qz=obj_quat.z, qw=obj_quat.w)

            if type_from == "COLLECTION":
                name = obj.users_collection[0].name
            else:
                name = obj.name
                # Strip the trailing ".xxx" numbers from the object name
                search = re.search("\.[0-9]+$", name)
                if search:
                    name = name[0 : search.start()]

            vector = dotbimpy.Vector(x=obj_trans.x, y=obj_trans.y, z=obj_trans.z)
            element = dotbimpy.Element(
                mesh_id=i,
                vector=vector,
                guid=guid,
                info=info,
                rotation=rotation,
                type=name,
                color=color,
                face_colors=face_colors,
            )

            elements.append(element)

    file_info = {"Author": author, "Date": date.today().strftime("%d.%m.%Y")}
    file = dotbimpy.File("1.0.0", meshes=meshes, elements=elements, info=file_info)
    file.save(filepath)


if __name__ == "__main__":
    objects = bpy.context.selected_objects
    export_objects(objs=objects, filepath=r"House.bim")
