from pathlib import Path
import os.path
import bpy
from bpy_extras.io_utils import ImportHelper, ExportHelper
from . import dotbim_to_blender
from . import blender_to_dotbim


bl_info = {
    "name": "dotbim",
    "author": "paireks, Gorgious56",
    "version": (1, 0),
    "blender": (2, 90, 0),
    "location": "",
    "description": "Exporter / Importer for lightweight dotbim format",
    "warning": "",
    "doc_url": "https://github.com/paireks/dotbim",
    "category": "Import-Export",
}


class DOTBIM_OT_import(bpy.types.Operator, ImportHelper):
    bl_idname = "dotbim.import"
    bl_label = "Import objects"

    filter_glob: bpy.props.StringProperty(
        default="*.bim",
        options={"HIDDEN"},
        maxlen=255,
    )
    files: bpy.props.CollectionProperty(
        type=bpy.types.OperatorFileListElement,
        options={"HIDDEN", "SKIP_SAVE"},
    )

    def execute(self, context):
        folder = Path(self.filepath)
        if not os.path.isdir(folder):
            folder = folder.parent
        for file in self.files:
            dotbim_to_blender.import_from_file(f"{folder / file.name}")
        return {"FINISHED"}


class DOTBIM_OT_export(bpy.types.Operator, ExportHelper):
    bl_idname = "dotbim.export"
    bl_label = "Export objects"

    filename_ext = ".bim"
    filter_glob: bpy.props.StringProperty(
        default="*.bim",
        options={"HIDDEN"},
        maxlen=255,
    )

    export_filter: bpy.props.EnumProperty(
        name="Export",
        description="Choose which objects to export",
        items=(
            ("SELECTED", "Selected", "Export all selected objects"),
            ("SCENE", "Scene", "Export all objects in the current scene"),
        ),
        default="SELECTED",
    )

    def execute(self, context):
        blender_to_dotbim.export_objects(
            objs=context.selected_objects if self.export_filter == "SELECTED" else context.scene.objects,
            filepath=self.filepath,
        )
        return {"FINISHED"}


def menu_func_import(self, context):
    self.layout.operator(DOTBIM_OT_import.bl_idname, text="dotbim (.bim)")


def menu_func_export(self, context):
    self.layout.operator(DOTBIM_OT_export.bl_idname, text="dotbim (.bim)")


def register():
    bpy.utils.register_class(DOTBIM_OT_import)
    bpy.utils.register_class(DOTBIM_OT_export)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    bpy.utils.unregister_class(DOTBIM_OT_import)
    bpy.utils.unregister_class(DOTBIM_OT_export)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
