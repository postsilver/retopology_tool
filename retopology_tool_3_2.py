bl_info = {
    "name": "Retopology Tool",
    "author": "posthuman",
    "version": (3, 2),
    "blender": (4, 3, 2),
    "location": "View3D > Sidebar > Retopo",
    "description": "Game-optimized retopology using a 0-1 intensity slider, with LOD generation plus fallback decimation",
    "category": "Object",
}

import bpy
from bpy.types import Operator, Panel, PropertyGroup
from bpy.props import (
    FloatProperty,
    BoolProperty,
    EnumProperty,
    PointerProperty,
    FloatVectorProperty,
    IntProperty
)

def get_selected_mesh_stats(context):
    """Return (vertices, edges, faces, tris) for the active MESH object."""
    obj = context.active_object
    if obj and obj.type == 'MESH':
        mesh = obj.data
        tris = sum(len(poly.vertices) - 2 for poly in mesh.polygons)
        return len(mesh.vertices), len(mesh.edges), len(mesh.polygons), tris
    return (0, 0, 0, 0)


def intensity_to_facecount(intensity):
    """
    Convert a 0..1 slider value into an approximate face count for Quadriflow.
    
    - 0.0 => ~500 triangles => ~250 quad faces
    - 1.0 => ~30,000 triangles => ~15,000 quad faces
    """
    tri_min = 500
    tri_max = 30000
    tri_target = tri_min + (tri_max - tri_min) * intensity
    # Quadriflow is quad-based, so approximate by dividing triangles by 2
    face_target = int(tri_target / 2)
    return max(50, face_target)


class GAME_RETOPO_Settings(PropertyGroup):
    """
    Property group for storing add-on settings in the Scene.
    """

    retopo_intensity: FloatProperty(
        name="Retopo Intensity",
        description="0 => ~500 tris, 1 => ~30k tris",
        min=0.0,
        max=1.0,
        default=0.5
    )
    
    preserve_sharp: BoolProperty(
        name="Preserve Sharp Edges",
        default=True
    )
    
    lod_levels: IntProperty(
        name="LOD Levels",
        description="Number of LODs to generate (including the base retopo)",
        min=1,
        max=5,
        default=3
    )
    
    lod_reduction: FloatVectorProperty(
        name="LOD Reduction",
        description="Reduction factors for each LOD step (base is LOD0)",
        size=5,
        min=0.05,
        max=1.0,
        default=(1.0, 0.5, 0.3, 0.2, 0.1)
    )
    
    auto_uvs: BoolProperty(
        name="Transfer UVs",
        description="Automatically copy UVs from the previous LOD (or original mesh for LOD0)",
        default=True
    )
    
    lod_preset: EnumProperty(
        name="LOD Preset",
        description="Choose a quick set of LOD reduction factors",
        items=[
            ('CUSTOM', "Custom", "Manual reduction factors"),
            ('GAME', "Game", "50%, 30%, 15%, 10%, 5%"),
            ('CINEMA', "Cinema", "80%, 60%, 40%, 25%, 15%")
        ],
        default='GAME'
    )

    debug_face_counts: BoolProperty(
        name="Debug Face Counts",
        description="Print mesh face counts before/after Quadriflow and Decimate",
        default=False
    )


class GAME_RETOPO_OT_Process(Operator):
    """
    Operator that:
    - Remeshes the selected object(s) using Quadriflow with a user-specified intensity
    - Generates multiple LOD levels
    - Transfers UVs if requested
    - Organizes the LOD objects in a dedicated collection
    """
    bl_idname = "game_retopo.process"
    bl_label = "Process Retopo & LODs"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        settings = context.scene.game_retopo_settings
        selected_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        
        if not selected_objects:
            self.report({'ERROR'}, "No mesh objects selected")
            return {'CANCELLED'}

        # Apply LOD preset if not custom
        if settings.lod_preset != 'CUSTOM':
            settings.lod_reduction = self.get_preset_values(settings.lod_preset)
        
        success_count = 0
        for obj in selected_objects:
            try:
                base_lod = self.create_retopo(obj, settings)
                if not base_lod:
                    continue
                
                lods = [base_lod]
                for i in range(1, settings.lod_levels):
                    if i >= len(settings.lod_reduction):
                        self.report({'WARNING'}, f"Insufficient LOD reduction factors for {obj.name}")
                        break
                    reduction = settings.lod_reduction[i]
                    lod = self.create_lod(lods[-1], settings, reduction, i)
                    if lod:
                        lods.append(lod)
                    else:
                        break

                if len(lods) >= 1:
                    self.organize_lods(obj, lods)
                    success_count += 1

            except Exception as e:
                self.report({'WARNING'}, f"Failed on {obj.name}: {str(e)}")
                continue

        # Reselect original objects
        for ob in bpy.data.objects:
            ob.select_set(False)
        for obj in selected_objects:
            obj.select_set(True)
        context.view_layer.objects.active = selected_objects[-1] if selected_objects else None

        self.report({'INFO'}, f"Generated LODs for {success_count}/{len(selected_objects)} objects")
        return {'FINISHED'}

    def get_preset_values(self, preset):
        """Return default LOD reduction factors for a known preset."""
        if preset == 'GAME':
            return (1.0, 0.5, 0.3, 0.2, 0.1)
        elif preset == 'CINEMA':
            return (1.0, 0.8, 0.6, 0.4, 0.25)
        return (1.0, 1.0, 1.0, 1.0, 1.0)

    def create_retopo(self, obj, settings):
        """
        Create the initial LOD0 remesh from the original object,
        using retopo_intensity as an approximate face count.
        """
        # Deselect all
        for o in bpy.data.objects:
            o.select_set(False)

        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        
        if obj.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        
        # Duplicate object for LOD0
        bpy.ops.object.duplicate()
        lod0 = bpy.context.active_object
        lod0.name = f"{obj.name}_LOD0"
        
        # Basic cleanup
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='FACE')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.fill_holes(sides=0)
        
        bpy.ops.mesh.select_mode(type='VERT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=0.0001)
        
        bpy.ops.mesh.select_mode(type='FACE')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.normals_make_consistent(inside=False)
        
        # Check for non-manifold edges
        bpy.ops.mesh.select_mode(type='EDGE')
        bpy.ops.mesh.select_non_manifold()
        non_manifold_edges = [e for e in lod0.data.edges if e.select]

        if non_manifold_edges:
            self.report({'WARNING'}, f"Non-manifold edges in {lod0.name}. Attempting auto-fix...")
            if bpy.app.version >= (3, 6, 0):
                bpy.ops.mesh.select_mode(type='VERT')
                bpy.ops.mesh.select_all(action='SELECT')
                try:
                    bpy.ops.mesh.make_manifold()
                    bpy.ops.mesh.select_all(action='SELECT')
                    bpy.ops.mesh.normals_make_consistent(inside=False)
                except (RuntimeError, AttributeError):
                    pass
            else:
                bpy.ops.mesh.delete(type='EDGE_FACE')
                bpy.ops.mesh.select_mode(type='FACE')
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.mesh.fill_holes(sides=0)
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.mesh.normals_make_consistent(inside=False)

        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')

        # Quadriflow retopology
        target_faces = intensity_to_facecount(settings.retopo_intensity)
        try:
            before_faces = len(lod0.data.polygons)
            ret = bpy.ops.object.quadriflow_remesh(
                mode='FACES',
                target_faces=target_faces,
                use_preserve_sharp=settings.preserve_sharp
            )
            after_faces = len(lod0.data.polygons)
            
            if settings.debug_face_counts:
                print(f"[DEBUG] LOD0 Quadriflow: before={before_faces}, after={after_faces}, ret={ret}")

            if after_faces < target_faces * 0.8:
                self.report(
                    {'WARNING'}, 
                    f"LOD0: Quadriflow produced {after_faces} faces (target ~{target_faces})."
                )

            # Transfer UVs from original to LOD0 if auto_uvs is true and the source has UVs
            if settings.auto_uvs:
                self.transfer_uvs(obj, lod0)

            return lod0

        except Exception as e:
            self.report({'WARNING'}, f"Retopo failed on {lod0.name}: {str(e)}")
            bpy.data.objects.remove(lod0, do_unlink=True)
            return None

    def create_lod(self, prev_lod, settings, reduction, lod_index):
        """
        Duplicate the previous LOD, retopologize it further with a lower face count,
        then optionally transfer UVs from the previous LOD.
        """
        for o in bpy.data.objects:
            o.select_set(False)
        
        prev_lod.select_set(True)
        bpy.context.view_layer.objects.active = prev_lod

        current_faces = len(prev_lod.data.polygons)
        target = max(50, int(current_faces * reduction))

        bpy.ops.object.duplicate()
        lod = bpy.context.active_object
        lod.name = f"{prev_lod.name.rsplit('_', 1)[0]}_LOD{lod_index}"
        
        try:
            before_faces = len(lod.data.polygons)
            
            bpy.ops.object.quadriflow_remesh(
                mode='FACES',
                target_faces=target,
                use_preserve_sharp=settings.preserve_sharp
            )

            after_faces = len(lod.data.polygons)
            if settings.debug_face_counts:
                print(f"[DEBUG] LOD{lod_index} Quadriflow: "
                      f"before={before_faces}, after={after_faces}, target={target}")

            # If Quadriflow overshoots, apply decimate fallback
            if after_faces > target:
                self.report(
                    {'INFO'}, 
                    f"{lod.name}: Quadriflow overshot target, decimating to {target} faces."
                )
                self.decimate_fallback(lod, target, settings, before_faces)
            elif after_faces >= before_faces * 0.9:
                self.report(
                    {'INFO'}, 
                    f"{lod.name}: Quadriflow didn't reduce enough, decimating to {target} faces."
                )
                self.decimate_fallback(lod, target, settings, before_faces)

        except Exception as e:
            self.report({'WARNING'}, f"Failed to create LOD{lod_index} on {prev_lod.name}: {str(e)}")
            bpy.data.objects.remove(lod, do_unlink=True)
            return None

        if settings.auto_uvs:
            self.transfer_uvs(prev_lod, lod)

        return lod

    def decimate_fallback(self, obj, target, settings, before_faces):
        """
        If Quadriflow doesn't get close to the desired face count,
        use a Decimate modifier to approximate it.
        """
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        if obj.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        
        current_faces = len(obj.data.polygons)
        desired_ratio = max(0.01, min(1.0, target / float(current_faces)))
        mod = obj.modifiers.new("Decimate_Fallback", "DECIMATE")
        mod.ratio = desired_ratio
        bpy.ops.object.modifier_apply(modifier=mod.name)

        if settings.debug_face_counts:
            print(f"[DEBUG] Decimate fallback on {obj.name}: "
                  f"before={current_faces}, after={len(obj.data.polygons)}")

    def transfer_uvs(self, source, target):
        """
        Transfer UV data from 'source' to 'target' via Blender's data_transfer operator.
        If 'source' has no UVs, nothing happens.
        """
        if not source.data.uv_layers:
            return
        for ob in bpy.data.objects:
            ob.select_set(False)

        source.select_set(True)
        target.select_set(True)
        bpy.context.view_layer.objects.active = source

        try:
            bpy.ops.object.data_transfer(
                data_type='UV',
                use_create=True,
                vert_mapping='NEAREST',
                edge_mapping='NEAREST',
                loop_mapping='NEAREST_POLYNOR',
                poly_mapping='NEAREST',
                mix_mode='REPLACE'
            )
        except Exception as e:
            self.report({'WARNING'}, f"UV transfer failed: {str(e)}")

    def organize_lods(self, original, lods):
        """
        Create or reuse a '[original]_LODs' collection and move all LOD objects into it.
        Also parent each LOD to the original for convenience.
        """
        collection_name = f"{original.name}_LODs"
        if collection_name not in bpy.data.collections:
            collection = bpy.data.collections.new(collection_name)
            bpy.context.scene.collection.children.link(collection)
        
        collection = bpy.data.collections[collection_name]
        for lod in lods:
            if lod.name not in collection.objects:
                for col in lod.users_collection:
                    col.objects.unlink(lod)
                collection.objects.link(lod)
            lod.parent = original

class VIEW3D_PT_GameRetopo(Panel):
    """
    The UI panel for controlling the Retopology Tool's settings.
    """
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Retopo"
    bl_label = "Retopology Tool"

    def draw(self, context):
        layout = self.layout
        settings = context.scene.game_retopo_settings
        
        # Mesh Stats
        box = layout.box()
        box.label(text="Mesh Stats", icon='MESH_DATA')
        v, e, f, t = get_selected_mesh_stats(context)
        
        if v + e + f > 0:
            col = box.column(align=True)
            col.label(text=f"Vertices: {v:,}", icon='VERTEXSEL')
            col.label(text=f"Edges: {e:,}", icon='EDGESEL')
            col.label(text=f"Faces: {f:,}", icon='FACESEL')
            col.label(text=f"Tris: {t:,}", icon='MOD_TRIANGULATE')
        else:
            box.label(text="No mesh selected", icon='ERROR')
            
        # Retopology Intensity
        box = layout.box()
        box.label(text="Base Retopology")
        col = box.column(align=True)
        col.prop(settings, "retopo_intensity", slider=True, text="Retopo Intensity")
        col.label(text="(0 => ~500 tris, 1 => ~30k tris)")

        col.prop(settings, "preserve_sharp")

        # LOD Generation
        box = layout.box()
        box.label(text="LOD Generation")
        col = box.column(align=True)
        col.prop(settings, "lod_preset", text="Preset")
        col.prop(settings, "lod_levels")
        col.prop(settings, "auto_uvs")

        if settings.lod_preset == 'CUSTOM':
            col = box.column(align=True)
            for i in range(settings.lod_levels):
                col.prop(
                    settings, 
                    "lod_reduction", 
                    index=i, 
                    text=f"LOD{i} Reduction" if i > 0 else f"LOD{i} Base"
                )

        layout.prop(settings, "debug_face_counts", text="Debug Face Counts")
        layout.operator("game_retopo.process", icon='MOD_REMESH')

classes = (
    GAME_RETOPO_Settings,
    GAME_RETOPO_OT_Process,
    VIEW3D_PT_GameRetopo
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.game_retopo_settings = PointerProperty(type=GAME_RETOPO_Settings)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.game_retopo_settings

if __name__ == "__main__":
    register()
