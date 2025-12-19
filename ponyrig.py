# SPDX-License-Identifier: GPL-3.0-or-later
"""
This file is to draw PonyRig panel in the 3D View's Sidebar.
Some code taken from CloudRig.
"""

bl_info = {
    "name": "PonyRig",
    "author":"ainerpony",
    "blender": (4,4,3),
    "location": "3D Viewport > PonyRig Panel",
    "category": "PonyRig"
}


import bpy, re, ast
from bpy.types import (
    PropertyGroup,
    Collection,
    Context,
    Panel,
    UIList,
    Object,
    UILayout,
    Operator,
)
from bpy.props import (
    PointerProperty,
    StringProperty,
    IntProperty,
    BoolProperty,
    CollectionProperty,
)


RIG_ID = 'ponyrig_twilight'

bone_collections = (
    'Main Controls',
    'Tweak Controls',
    'Face',
    'Hairs',
    'Properties', 
    'Rigging', 
)
prop_limbs = (
    "L_foreLeg_options", "R_foreLeg_options",
    "L_hindLeg_options", "R_hindLeg_options",
)
prop_hairs = (
    "mane_options", "tail_options",
)
bone_alias = {
    "L_foreLeg_options":"L ForeLeg", "R_foreLeg_options":"R ForeLeg",
    "L_hindLeg_options":"L HindLeg", "R_hindLeg_options":"R HindLeg",
    "mane_options":"Mane", "tail_options":"Tail"
}
"""FK Bones which associated with prop bone"""
bone_affect = {
    "L_foreLeg_options": [f"L_foreLeg_FKJnt{i}" for i in range(1,5)],
    "R_foreLeg_options": [f"R_foreLeg_FKJnt{i}" for i in range(1,5)],

    "L_hindLeg_options": [f"L_hindLeg_FKJnt{i}" for i in range(1,5)],
    "R_hindLeg_options": [f"R_hindLeg_FKJnt{i}" for i in range(1,5)],

    "mane_options": [f"mane_bndJnt{i}_FK" for i in range(1,5)]+
                    ["mane_bndJnt_FK", "mane02End_FK", "mane01End_IK1"]+
                    [f"mane0{i}End_IK1" for i in range(1, 5)],
    "tail_options": ["tailBase_bndJnt1_FK"]+[f"tail_bndJnt{i}_FK" for i in range(1,10)],
}


def get_ponyrig(rig_id:str=RIG_ID) -> Object | None:
    """Get ponyrig by searching object with property: rig_id"""

    for rig in bpy.data.objects:
        if rig.get(rig_id) and rig.type == 'ARMATURE':
            return rig
        
    return None


class PonyRig_OutlineItem(PropertyGroup):
    """Store outline objects and collections"""

    name: StringProperty(options={'LIBRARY_EDITABLE'}, override={'LIBRARY_OVERRIDABLE'})                                           # type: ignore
    is_collection: bpy.props.BoolProperty(default=False, options={'LIBRARY_EDITABLE'}, override={'LIBRARY_OVERRIDABLE'})           # type: ignore
    object_ref: PointerProperty(type=Object, options={'LIBRARY_EDITABLE'}, override={'LIBRARY_OVERRIDABLE'})                       # type: ignore
    collection_ref: PointerProperty(type=Collection, options={'LIBRARY_EDITABLE'}, override={'LIBRARY_OVERRIDABLE'})               # type: ignore


class PonyRig_RigPreferences(PropertyGroup):
    """Store properties below into rig.ponyrig_pref"""

    active_index: IntProperty(options={'LIBRARY_EDITABLE'}, override={'LIBRARY_OVERRIDABLE'})                                      # type: ignore
    outline_items: CollectionProperty(type=PonyRig_OutlineItem, options={'LIBRARY_EDITABLE'}, override={'LIBRARY_OVERRIDABLE'})    # type: ignore


class PonyRigPanel:
    bl_space_type = 'VIEW_3D'
    bl_category = 'PonyRig'
    bl_region_type = 'UI'


class PONY_PT_MAIN(PonyRigPanel, Panel):
    bl_label = 'Settings'

    def draw_viewport_prop(self, rig:Object, prop_owner_name:str, prop_name:str, layout:UILayout):
        """Draw viewport quality controller"""

        if rig != None:
            prop_owner = rig.pose.bones.get(prop_owner_name)
        else:
            return

        try:
            prop_val = prop_owner.path_resolve(f'["{prop_name}"]')
            text = ['Performance', 'Default', 'Render']
            layout.prop(prop_owner, f'["{prop_name}"]', text=f"Viewport Quality: {text[prop_val]}", slider=True)
        except ValueError:
            layout.alert = True
            layout.label(text=f"Missing property in '{prop_owner_name}': '{prop_name}'  ")

    def draw_config_solid_shading(self,context:Context, layout:UILayout):
        if hasattr(context.space_data, "shading"):
            shading = context.space_data.shading
        else:
            return

        def target_shade_settings(shading) -> bool:
            """Check if the solid shader settings are as expected"""

            shade_config = {
                "light": "MATCAP",
                "show_backface_culling": True,
                "color_type": "TEXTURE",
                "show_cavity": True,
                "cavity_type": "WORLD",
            }

            for attr, value in shade_config.items():
                if getattr(shading, attr) != value:
                    return False
            return True

        if shading.type == "SOLID" and not target_shade_settings(shading):
            layout.operator('view3d.ponyrig_config_solid_shading', text="", icon='FILE_REFRESH')

    def draw_show_in_front_option(self, rig:Object, layout:UILayout):
        icon = "CHECKBOX_HLT" if rig.show_in_front else "CHECKBOX_DEHLT"
        layout.prop(rig, "show_in_front", icon=icon)

    def draw_backface_culling_option(self, context:Context, layout:UILayout):
        if hasattr(context.space_data, "shading"):
            shading = context.space_data.shading
            icon = "CHECKBOX_HLT" if shading.show_backface_culling else "CHECKBOX_DEHLT"
            layout.prop(shading, "show_backface_culling", icon=icon)

    def draw(self, context):
        layout = self.layout
        rig = get_ponyrig()

        if rig:
            row = layout.row()
            self.draw_viewport_prop(rig, "properties", "Quality", layout=row)
            self.draw_config_solid_shading(context, row)

            row = layout.row()
            self.draw_show_in_front_option(rig, row)
            self.draw_backface_culling_option(context, row)
        else:
            self.draw_backface_culling_option(context, layout.row())
            row = layout.row()
            row.alert = True
            row.label(text=f"Can't find rig with property: '{RIG_ID}', check if it exist or is set to false.", icon='ERROR')

    @classmethod
    def poll(cls, context):
        return True


class PONY_PT_bone_collections(PonyRigPanel, Panel):
    bl_parent_id = 'PONY_PT_MAIN'
    bl_label = 'Bone Collections'
    rig = get_ponyrig()

    def draw_ponyrig_collections(self, armature:Object, coll_name:str, layout:UILayout):
        """Match and draw collections from given collection name. """

        data = armature.data
        coll = data.collections_all.get(coll_name)

        if coll:
            column = layout.column()
            icon = 'HIDE_OFF' if coll.is_visible else 'HIDE_ON'
            column.prop(
                coll, "is_visible", 
                text=coll.name, toggle=True, 
                icon=icon, translate=False
            )

            """Draw child collections inside a sub-box"""
            if coll.is_visible and len(coll.children) != 0:
                box = column.box()
                sub_column = box.column()
                row = sub_column.row()
                n = 1

                for sub_coll in coll.children:
                    n += 1
                    if n != 2 and n % 2 == 0:     # Start a new line after drawing two props.
                        row = sub_column.row()

                    icon = 'HIDE_OFF' if sub_coll.is_visible else 'HIDE_ON'
                    row.prop(
                        sub_coll, "is_visible", 
                        text=sub_coll.name, toggle=True, 
                        icon=icon, translate=False
                    )
        else:
            row = layout.row()
            row.alert = True
            row.label(
                text=f"Missing collection: '{coll_name}'", icon="ERROR")

    def draw(self, context):
        armature = get_ponyrig()

        """Draw bone collecitons from tuple: 'bone_collections' """
        for collection in bone_collections:
            self.draw_ponyrig_collections(armature, collection, self.layout)

    @classmethod
    def poll(cls, context):
        return get_ponyrig()


class POSE_OT_snap_bake(Operator):
    """
    Snap and bake FK bones to IK bones or FK to itself.
    TODO: Snap IK to FK
    """

    bl_idname = 'pose.ponyrig_snap_bake'
    bl_label = 'Snap & Bake Bones'
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    do_bake: BoolProperty(name="Bake", default=False)  # type: ignore
    frame_start: IntProperty(name="Start Frame")       # type: ignore
    frame_end: IntProperty(name="End Frame")           # type: ignore
    key_before_start: BoolProperty(
        name="Key Before Start",
        description="Insert a keyframe of the original values one frame before the bake range. This is to avoid undesired interpolation towards the bake",
    )                                                  # type: ignore
    key_after_end: BoolProperty(
        name="Key After End",
        description="Insert a keyframe of the original values one frame after the bake range. This is to avoid undesired interpolation after the bake",
    )                                                  # type: ignore

    prop_owner_name: StringProperty(
        description="Bone with FK/IK or something similar switch property"
    )                                                  # type: ignore
    prop_name: StringProperty(
        description="Flip this prop value after snapping"
    )                                                  # type: ignore
    affect_bones: StringProperty(
        description="'List[str]' of FK bone for snapping FK to IK"
    )                                                  # type: ignore

    def get_matrix(self, rig:Object, bone_list:list[str]) -> list:
        """Stores the current view transformation matrix of each bone"""
        snap_matrix = []

        for bone_name in bone_list:
            bone = rig.pose.bones.get(bone_name)
            snap_matrix.append(bone.matrix.copy())

        return snap_matrix

    def snap_bones_to_matrix(self, rig:Object, bones:list[str], snap_matix:list):
        for i, bone_name in enumerate(bones):
            bone = rig.pose.bones.get(bone_name)
            bone.matrix = snap_matix[i]
            bpy.context.view_layer.update()
            bone.matrix = snap_matix[i]

    @classmethod
    def keyframe_bones(self, rig:Object, bone_map:list[str]|list[list], keying_set:list[str], frame:int):
        """Keyframe the given attributes for each bone at the specified frame"""

        for bone in bone_map:
            if type(bone) == str:
                pose_bone = rig.pose.bones.get(bone)
            elif type(bone) == list:
                pose_bone = rig.pose.bones.get(bone[0])

            """Check if prop_id contains rotation property and change it to pose bone's current rotation_mode"""
            rot_index = next((i for i, s in enumerate(keying_set) if re.compile(r"^rotation.*").match(s)), None)
            if rot_index != None:
                if pose_bone.rotation_mode in ['QUATERNION', 'AXIS_ANGLE']:
                    keying_set[rot_index] = f"rotation_{pose_bone.rotation_mode.lower()}"
                else:
                    keying_set[rot_index] = "rotation_euler"

            """Insert keyframe"""
            for prop in keying_set:
                pose_bone.keyframe_insert(data_path=f"{prop}", frame=frame)

    def execute(self, context):
        rig = get_ponyrig()
        affect_bones = ast.literal_eval(self.affect_bones)                     # convert '[str]' to [str]
        prop_owner = rig.pose.bones.get(self.prop_owner_name)
        prop_name = self.prop_name                                             # format: "FK/IK"
        prop_val = prop_owner.path_resolve(f'["{prop_name}"]')
        keying_set = ["location", "scale", "rotation_quaternion"]
        snap_matrix = self.get_matrix(rig, affect_bones)                       # Get current matrix before snapping

        if self.prop_name == "FK/IK" and prop_val == 0: return {'CANCELLED'}   # Snap IK to FK isn't support yet.

        if self.do_bake:
            active_frame = context.scene.frame_current

            if self.key_before_start:
                context.scene.frame_set(self.frame_start-1)
                frame_current = context.scene.frame_current

                prop_owner.keyframe_insert(f'["{prop_name}"]', frame=frame_current)
                self.keyframe_bones(rig, affect_bones, keying_set, frame_current)

                context.scene.frame_set(active_frame)
            if self.key_after_end:
                prop_owner.keyframe_insert(f'["{prop_name}"]', frame=self.frame_end+1)
                self.keyframe_bones(rig, affect_bones, keying_set, self.frame_end+1)

            for frame in range(self.frame_start, self.frame_end+1):
                """Baking"""
                context.scene.frame_set(frame)

                prop_owner[prop_name] = float(prop_val == 0.0)
                self.snap_bones_to_matrix(rig, affect_bones, snap_matrix)
                self.keyframe_bones(rig, affect_bones, keying_set, frame)
                prop_owner.keyframe_insert(f'["{prop_name}"]', frame=frame)

            context.scene.frame_set(active_frame)
        else:
            prop_owner[prop_name] = float(prop_val == 0.0)
            self.snap_bones_to_matrix(rig, affect_bones, snap_matrix)

        return {'FINISHED'}

    def invoke(self, context, event):
        self.frame_start = context.scene.frame_current
        self.frame_end = context.scene.frame_current
        self.do_bake = False
        self.key_before_start = True
        self.key_after_end = True

        return context.window_manager.invoke_props_dialog(self)

    def draw_affected_bones(self, rig:Object, bone_map:list[str], prop_name:str, layout:UILayout):
        prop_owner = rig.pose.bones.get(self.prop_owner_name)

        if (self.prop_name == "FK/IK" and prop_owner[prop_name] > 0) or (self.prop_name != "FK/IK"):
            column = layout.column(align=True)
            column.label(text="Snapped bones:")

            for from_bone in bone_map:
                column.label(text=f"{' '*10} {from_bone} -> {from_bone}")

    def draw(self, context):
        layout = self.layout
        rig = get_ponyrig()
        bone_map = ast.literal_eval(self.affect_bones)

        """Referenced from CloudRig"""
        layout.prop(self, 'do_bake')
        split = layout.split(factor=0.1)
        split.row()
        col = split.column()
        if self.do_bake:
            time_row = col.row(align=True)
            time_row.prop(self, 'frame_start')
            time_row.prop(self, 'frame_end')
            fix_row = col.row(align=True)
            fix_row.prop(self, 'key_before_start')
            fix_row.prop(self, 'key_after_end')

        self.draw_affected_bones(rig, bone_map, prop_name=self.prop_name, layout=layout)


class PONY_PT_bone_properties(PonyRigPanel, Panel):
    """Bone Properties Panel"""

    bl_parent_id = 'PONY_PT_MAIN'
    bl_label = 'FK/IK Switch'

    def draw_bone_props(self, armature:Object, prop_owner:list[str], prop_name:str, layout:UILayout, snap_bake:bool=False):
        bones = armature.pose.bones
        box = layout.box()
        row = box.row()
        n = 1

        for bone_name in prop_owner:
            n += 1
            if n != 2 and n % 2 == 0:
                row = box.row()

            pose_bone = bones.get(bone_name)
            if pose_bone:
                try:
                    pose_bone.path_resolve(f'["{prop_name}"]') # Property existence check.
                    sub_row = row.row(align=True)
                    sub_row.prop(pose_bone, f'["{prop_name}"]', text=bone_alias[bone_name], slider=True, translate=False)

                    if snap_bake:
                        """Draw 'Snap & Bake' operator at the end of each slider"""
                        op = sub_row.operator('pose.ponyrig_snap_bake', text="", icon='FILE_REFRESH')
                        op.prop_owner_name = bone_name
                        op.prop_name = prop_name
                        op.affect_bones = f"{bone_affect[bone_name]}"

                except ValueError:
                    sub_row = row.row(align=True)
                    sub_row.alert = True
                    sub_row.label(text=f"Missing property in '{bone_name}': '{prop_name}'", icon="ERROR")

            else:
                row.alert = True
                row.label(text=f"Missing prop bone: '{bone_name}'", icon="ERROR")

    def draw(self, context):
        layout = self.layout
        armature = get_ponyrig()

        if armature.type == 'ARMATURE':
            self.draw_bone_props(armature, prop_limbs, "FK/IK", layout, snap_bake=True)
            self.draw_bone_props(armature, prop_hairs, "FK/IK", layout, snap_bake=True)

    @classmethod
    def poll(cls, context):
        return get_ponyrig()


class PONY_PT_fk_properties(PonyRigPanel, Panel):
    bl_parent_id = 'PONY_PT_MAIN'
    bl_label = 'FK'

    def draw_fk_prop(self, rig:Object, prop_owner:str, prop_name:str, affect_bone:str, text:str, layout:UILayout):
        pose_bone = rig.pose.bones.get(prop_owner)
        row = layout.row(align=True)

        if pose_bone is None:
            row.alert = True
            row.label(text=f'Missing property owner: "{prop_owner}"', icon="ERROR")
            return

        try:
            pose_bone.path_resolve(f'["{prop_name}"]')
            row.prop(pose_bone, f'["{prop_name}"]', text=text, slider=True, translate=False)

            op = row.operator('pose.ponyrig_snap_bake', text="", icon='FILE_REFRESH')
            op.prop_owner_name = pose_bone.name
            op.prop_name = prop_name
            op.affect_bones = f"['{affect_bone}']"
        except ValueError:
            row.alert = True
            row.label(text=f'Missing property: "{prop_name}", owner: "{prop_owner}"', icon="ERROR")
            return

    def draw(self, context):
        rig = get_ponyrig()
        layout = self.layout
        prop = {
            ('properties', 'head_hinge', 'head_ctrl', 'Head'),
            ('tail_options', 'tail_hinge', 'tailBase_bndJnt1_FK', 'Tail')
        }

        row = layout.row()
        row.label(text="Hinge", translate=False)

        for owner, prop, affect_bone, text in prop:
            self.draw_fk_prop(rig, owner, prop, affect_bone, text, layout)

    @classmethod
    def poll(cls, context):
        return get_ponyrig()


def draw_bone_property(
    layout: UILayout, 
    rig: Object, 
    prop_owner_name: str, 
    prop_name: str, 
    slider_name="", 
    texts=[], 
    icon_true="CHECKBOX_HLT", 
    icon_false='CHECKBOX_DEHLT'
):
    prop_owner = rig.pose.bones.get(prop_owner_name)
    if prop_owner is None:
        layout.alert = True
        layout.label(text=f'Missing property owner: "{prop_owner_name}"', icon="ERROR")
        return
    try:
        prop_value = prop_owner.path_resolve(f'["{prop_name}"]')
    except ValueError:
        layout.alert = True
        layout.label(text=f'Missing property: "{prop_name}", owner: "{prop_owner_name}"', icon="ERROR")
        return

    if len(texts) > 0 and type(prop_value) == int:
        text = slider_name + ": " + texts[prop_value]
        layout.prop(prop_owner, f'["{prop_name}"]', text=text, slider=True)
    elif type(prop_value) == float:
        layout.prop(prop_owner, f'["{prop_name}"]', text=slider_name, slider=True)
    elif type(prop_value) == bool:
        icon = icon_true if prop_value else icon_false
        layout.prop(prop_owner, f'["{prop_name}"]', text=slider_name, toggle=True, icon=icon)
    else:
        layout.prop(prop_owner, f'["{prop_name}"]', text=slider_name)


class PONY_PT_face_properties(PonyRigPanel, Panel):
    bl_parent_id = 'PONY_PT_MAIN'
    bl_label = 'Face'

    def draw(self, context):
        layout = self.layout
        zipper_prop = {
            ("L_lipCorner_ctrl", "L_zipper_lip", "L Lip Zipper"),
            ("R_lipCorner_ctrl", "R_zipper_lip", "R Lip Zipper")
        }

        """Draw eyetarget properties"""
        draw_bone_property(
            layout.box(),
            get_ponyrig(),
            prop_owner_name='properties',
            prop_name='eye_target_parents',
            slider_name="Eye Target Parent",
            texts=['Master', 'Head', 'COG']
        )

        """Draw lip zipper properties"""
        column = layout.box().column()
        for owner, prop, text in zipper_prop:
            draw_bone_property(
                layout=column,
                rig=get_ponyrig(),
                prop_owner_name=owner,
                prop_name=prop,
                slider_name=text
            )


class PONY_UL_collections(UIList):
    """Draw outline items in a UIList"""

    def draw_item(self, context, layout, data, item, icon, active_data, active_property, index, flt_flag):
        if item.is_collection:
            obj = item.collection_ref
        else:
            obj = item.object_ref

        if obj:
            row = layout.row(align=True)
            obj_name = obj.get("alias") if obj.get("alias") else obj.name
            row.label(text=f"{obj_name} Outline", icon="MOD_SOLIDIFY", translate=False)

            row.prop(obj, "hide_viewport", text="", toggle=True, emboss=False)
            row.prop(obj, "hide_render", text="", toggle=True, emboss=False)


class PONY_PT_magic_outline(PonyRigPanel, Panel):
    """Magic Aura and Outline Control Panel"""

    bl_label = 'Magic & Outline Control'

    def draw_magic_panel(self, context, collection_id:str, bone_id:str, bone_prop_id:list[list], layout:UILayout):
        rig = get_ponyrig()
        magic_collection = None
        prop_bone = rig.pose.bones.get(bone_id) if rig.type == 'ARMATURE' else None

        """Find collection with given colletion_id"""
        for collection in bpy.data.collections:
            if collection.get(collection_id):
                magic_collection = collection
                break

        """Draw viewport and render display attributes"""
        if magic_collection:
            box = layout.box()
            column = box.column(align=False)

            row = column.row()
            row.label(text="Magic Aura", icon="PMARKER_SEL")

            row = row.box().row()
            row.prop(magic_collection, "hide_viewport", text="", toggle=True, emboss=False)
            row.prop(magic_collection, "hide_render", text="", toggle=True, emboss=False)
        else:
            row = layout.row()
            row.alert = True
            row.label(text=f"Missing collection with property: '{collection_id}'", icon="ERROR")

            return

        """Draw bone properties"""
        if prop_bone and not magic_collection.hide_viewport:
            for prop_list in bone_prop_id:
                box = column.column().box()
                row = box.row()

                for n, prop in enumerate(prop_list):
                    if n != 0 and n %2 == 0:
                        row = box.row()

                    if prop_bone.get(prop) != None:
                        if type(prop_bone.get(prop)) == bool:
                            icon = "HIDE_OFF" if prop_bone.get(prop) else "HIDE_ON"
                            row.prop(prop_bone, f'["{prop}"]', text=prop, toggle=True, translate=False, icon=icon)
                        else:
                            row.prop(prop_bone, f'["{prop}"]', text=prop)
                    else:
                        row.alert = True
                        row.label(text=f"Missing property: '{prop}'", icon="ERROR")
                        row = row.row()
                        row.alert = False
        elif prop_bone == None:
            row = layout.row()
            row.alert = True
            row.label(text=f"Missing bone with name: '{bone_id}'", icon="ERROR")
        else:
            return

    def draw_outline(self, context, outline_coll_id:str, layout:UILayout):
        rig = get_ponyrig()
        master_coll = None

        """Find the main outline collection and draw."""
        for i in bpy.data.collections:
            if i.get(f"{outline_coll_id}"):
                master_coll = i
                break

        if master_coll != None:
            box = layout.box()
            column = box.column(align=False)
            row = column.row()

            """Draw Main Outline Collection"""
            row.label(text="Outlines", icon="MOD_SOLIDIFY", translate=False)
            row = row.box().row()

            if rig:
                """Draw update buttom when active object type is AEMATURE"""
                op = row.operator('pose.ponyrig_update_outline_items', text="", icon='FILE_REFRESH', emboss=False)
                op.collection_id = outline_coll_id

            row.prop(master_coll, "hide_viewport", text="", toggle=True, emboss=False)
            row.prop(master_coll, "hide_render", text="", toggle=True, emboss=False)

            """Draw Child Element"""
            if not master_coll.hide_viewport and not master_coll.hide_render and len(rig.ponyrig_prefs.outline_items) != 0:
                row = column.row()
                row.template_list(
                    "PONY_UL_collections", "Outline Collections List",
                    rig.ponyrig_prefs, "outline_items",
                    rig.ponyrig_prefs, "active_index"
                )
        else:
            row = layout.row()
            row.alert = True
            row.label(text=f"Can't find collection with property: '{outline_coll_id}'", icon="ERROR")

    def draw(self, context):
        self.draw_magic_panel(
            context, 
            collection_id="magic_master", 
            bone_id="magic_ctrl", 
            bone_prop_id=[["Points", "Sparkles", "Opacity", "Power"], ["Amplitude", "Frequency", "Speed", "Roughness"]],
            layout=self.layout
        )

        self.draw_outline(context, outline_coll_id='outline_master', layout=self.layout)

    @classmethod
    def poll(cls, context):
        return get_ponyrig()


class POSE_OT_update_outline_items(Operator):
    """Get outline items from collection with given outline_id property and store it into context.object.ponyrig_prefs.outline_items"""

    bl_idname = 'pose.ponyrig_update_outline_items'
    bl_label = 'Update Outline Items'
    bl_options = {'REGISTER', 'UNDO'}

    collection_id: StringProperty(default='outline_master',
                                  description="Collection with this property will consider as outline collection and draw the items from it to the list below",
                                  override={'LIBRARY_OVERRIDABLE'})                                # type: ignore
    rig_id: StringProperty(default=RIG_ID, 
                           description="Defind which rig should use to store outline items",
                           override={'LIBRARY_OVERRIDABLE'})                                       # type: ignore

    @classmethod
    def run_update(self, rig:Object, collction_id:str) -> bool:
        ponyrig_prefs = rig.ponyrig_prefs
        outline_coll = None

        for collection in bpy.data.collections:
            if collection.get(f'{collction_id}'):
                outline_coll = collection
                break
        if outline_coll == None:
            return False

        ponyrig_prefs.outline_items.clear()

        for child_col in outline_coll.children:
            item = ponyrig_prefs.outline_items.add()

            item.name = child_col.name
            item.is_collection = True
            item.collection_ref = child_col

        for child_obj in outline_coll.objects:
            item = ponyrig_prefs.outline_items.add()

            item.name = child_obj.name
            item.is_collection = False
            item.object_ref = child_obj

        return True

    def execute(self, context):
        outline_id = self.collection_id
        rig = get_ponyrig()

        if rig and self.run_update(rig, outline_id):
            self.report({'INFO'}, f"Updated and store outline items into object: '{rig.name}'.")
        elif rig == None:
            self.report({'INFO'}, f"Can't find rig with rig id: '{self.rig_id}', check if it exist or is set to false.")
        else:
            self.report({'INFO'}, f"Can't find collection with property: '{outline_id}', check if it exist or is set to false.")

        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout

        column = layout.column()
        column.prop(self, 'rig_id', text="Rig ID")
        column.prop(self, 'collection_id', text="Collection ID")


class OBJECT_OT_config_solid_shading(Operator):
    """Try to make character look right in solid shading mode"""

    bl_idname = 'view3d.ponyrig_config_solid_shading'
    bl_label = 'Correct Solid Shaing Settings'
    bl_options = {'REGISTER'}

    def config_solid_shading(self, context:Context, shade_config:dict) -> set:
        if hasattr(context.space_data, "shading") and context.space_data.shading.type == 'SOLID':
            shading = context.space_data.shading
        else:
            return {'CANCELLED'}

        for attr, value in shade_config.items():
            setattr(shading, attr, value)

        return {'FINISHED'}

    def execute(self, context):
        shader_config = {
            "light": "MATCAP",
            "show_backface_culling": True,
            "color_type": "TEXTURE",
            "show_cavity": True,
            "cavity_type": "WORLD",
        }

        return self.config_solid_shading(context, shader_config)


classes = (
    PonyRig_OutlineItem, 
    PonyRig_RigPreferences, 
    PONY_UL_collections, 
    PONY_PT_MAIN, 
    POSE_OT_snap_bake, 
    POSE_OT_update_outline_items,
    PONY_PT_bone_collections, 
    PONY_PT_bone_properties,
    PONY_PT_fk_properties,
    PONY_PT_face_properties,
    PONY_PT_magic_outline, 
    OBJECT_OT_config_solid_shading, 
)


def register():
    unregister()

    for cls in classes:
        bpy.utils.register_class(cls)

    Object.ponyrig_prefs = PointerProperty(type=PonyRig_RigPreferences, override={'LIBRARY_OVERRIDABLE'})
    if get_ponyrig():
        try:
            POSE_OT_update_outline_items.run_update(get_ponyrig(), collction_id='outline_master')
        except TypeError:
            """happens when object is link type"""
            pass

def unregister():
    for cls in classes:
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass

    try:
        del bpy.types.Object.ponyrig_prefs
    except AttributeError:
        pass


run_from_vscode = True
if __name__ == '__main__' or run_from_vscode:
    register()
