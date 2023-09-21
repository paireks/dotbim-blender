import bpy
from dotbimpy import File
from collections import defaultdict


def convert_dotbim_mesh_to_blender(dotbim_mesh, mesh_id):
    vertices = [
        (dotbim_mesh.coordinates[counter], dotbim_mesh.coordinates[counter + 1], dotbim_mesh.coordinates[counter + 2])
        for counter in range(0, len(dotbim_mesh.coordinates), 3)
    ]
    faces = [
        (dotbim_mesh.indices[counter], dotbim_mesh.indices[counter + 1], dotbim_mesh.indices[counter + 2])
        for counter in range(0, len(dotbim_mesh.indices), 3)
    ]

    mesh = bpy.data.meshes.new(f"Mesh {mesh_id}")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()

    return mesh


def transfer_face_colors(obj, elt):
    if bpy.app.version >= (3, 6, 0):
        obj.data = obj.data.copy()  # Blender meshes don't support separate sets of attributes
        face_colors = [c / 255.0 for c in elt.face_colors]
        new_attr = obj.data.color_attributes.new("face_colors", "FLOAT_COLOR", "CORNER")
        for i in range(0, len(face_colors) - 1, 4):
            polygon = obj.data.polygons[i // 4]
            for corner_idx in polygon.loop_indices:
                new_attr.data[corner_idx].color = (
                    face_colors[i],
                    face_colors[i + 1],
                    face_colors[i + 2],
                    face_colors[i + 3],
                )
    else:
        print("Face Colors are not (yet) supported for Version < 3.6.0")


def import_from_file(filepath):
    scene = bpy.context.scene
    file = File.read(filepath)
    meshes_users = defaultdict(list)

    for elt in file.elements:
        meshes_users[elt.mesh_id].append(elt)
    for mesh_id, elts in meshes_users.items():
        dotbim_mesh = next((m for m in file.meshes if m.mesh_id == mesh_id), None)
        mesh = convert_dotbim_mesh_to_blender(dotbim_mesh, mesh_id)
        for elt in elts:
            obj = bpy.data.objects.new(elt.type, mesh)
            obj.location = [elt.vector.x, elt.vector.y, elt.vector.z]
            obj.rotation_mode = "QUATERNION"
            obj.rotation_quaternion = [elt.rotation.qw, elt.rotation.qx, elt.rotation.qy, elt.rotation.qz]
            for item in elt.info.items():
                obj[item[0][0:62]] = item[1]
            obj.color = [elt.color.r / 255.0, elt.color.g / 255.0, elt.color.b / 255.0, elt.color.a / 255.0]
            scene.collection.objects.link(obj)

            if hasattr(elt, "face_colors"):
                transfer_face_colors(obj, elt)


if __name__ == "__main__":
    import_from_file(r'House.bim')  # Change your path there
