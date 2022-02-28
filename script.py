import bpy
from dotbimpy import File


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


scene = bpy.context.scene
file = File.read(r'House.bim')  # Change your path there

for i in file.elements:
    dotbim_mesh = next((x for x in file.meshes if x.mesh_id == i.mesh_id), None)
    mesh = convert_dotbim_mesh_to_blender(dotbim_mesh)
    object = bpy.data.objects.new(i.type, mesh)
    object.location = [i.vector.x, i.vector.y, i.vector.z]
    object.rotation_mode = "QUATERNION"
    object.rotation_quaternion = [i.rotation.qw, i.rotation.qx, i.rotation.qy, i.rotation.qz]
    for item in i.info.items():
        object[item[0]] = item[1]
    object.color = [i.color.r / 255.0, i.color.g / 255.0, i.color.b / 255.0, i.color.a / 255.0]
    scene.collection.objects.link(object)
