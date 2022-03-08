import bpy
from dotbimpy import File
from collections import defaultdict


def convert_dotbim_mesh_to_blender(dotbim_mesh):
    vertices = [
        (dotbim_mesh.coordinates[counter], dotbim_mesh.coordinates[counter + 1], dotbim_mesh.coordinates[counter + 2])
        for counter in range(0, len(dotbim_mesh.coordinates), 3)
    ]
    faces = [
        (dotbim_mesh.indices[counter], dotbim_mesh.indices[counter + 1], dotbim_mesh.indices[counter + 2])
        for counter in range(0, len(dotbim_mesh.indices), 3)
    ]

    mesh = bpy.data.meshes.new("dotbim_properties")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()

    return mesh


def import_from_file(filepath):
    scene = bpy.context.scene
    file = File.read(filepath)
    meshes_users = defaultdict(list)

    for elt in file.elements:
        meshes_users[elt.mesh_id].append(elt)
    for mesh_id, elts in meshes_users.items():
        dotbim_mesh = next((m for m in file.meshes if m.mesh_id == mesh_id), None)
        mesh = convert_dotbim_mesh_to_blender(dotbim_mesh)
        for elt in elts:
            obj = bpy.data.objects.new(elt.type, mesh)
            obj.location = [elt.vector.x, elt.vector.y, elt.vector.z]
            obj.rotation_mode = "QUATERNION"
            obj.rotation_quaternion = [elt.rotation.qw, elt.rotation.qx, elt.rotation.qy, elt.rotation.qz]
            for item in elt.info.items():
                obj[item[0][0:62]] = item[1]
            obj.color = [elt.color.r / 255.0, elt.color.g / 255.0, elt.color.b / 255.0, elt.color.a / 255.0]
            scene.collection.objects.link(obj)


if __name__ == "__main__":
    import_from_file(r'House.bim')  # Change your path there
