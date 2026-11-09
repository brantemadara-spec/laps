# -*- coding: utf-8 -*-
"""LAPS Marle — self-contained Blender 4.x/5.x generator, revision C.

Run in Blender: Scripting > New > paste this complete file > Run Script.
Or: blender -b --python LAPS_Marle_Blender.py
No add-ons, CAD imports or external Python packages are required.

Two IDENTICAL PETG plates: 130 x 100 x 10 mm, R6, four corner M6 clearances.
Each plate has 345 square 2 x 2 mm cells on a 3.6 mm pitch and a complete
rear crosshatch of 15 row and 23 column drainage channels, 1.6 x 1.2 mm.
Use purchased plain cotton GAUZE inside the opening at each pulp face.
Choose ONE calibration base from .2/.4/.6/.8 mm according to the measured
compressed gauze thickness. Stack the .5/1/1.5 mm shims as required.
The illustrated .4 mm total gauze allowance is an assumption to be measured.
Wet gap = measured ring stack minus measured compressed total gauze allowance.
Final dry thickness requires experimental calibration.

The project contains native editable Boolean construction, validated closed
print meshes and a 12-object print catalogue. Existing user objects are kept.
The catalogue is not a printer bed: export/print each selected part separately.
No hinge or steel backers. Four metal M6 x 40 bolts, four nuts, eight washers.
This thinner prototype is for gentle hand closure and has no tested load rating.
"""
import bpy
import bmesh
import math
import os
import json
import struct
from pathlib import Path
from mathutils import Vector, Quaternion

# ---------------- EDITABLE PARAMETERS (mm) ----------------
# For a portable desktop run, choose your own writable output folder here.
OUTPUT_DIR = Path(os.environ.get('LAPS_MARLE_OUTPUT_DIR', str(Path.home() / 'LAPS_Marle_Blender'))).expanduser()
SAVE_BLEND = True
EXPORT_STL = True                         # Native independent STL exports
KEEP_NATIVE_CONSTRUCTION = True           # Hidden source meshes + live Booleans
OUTER_X_MM, OUTER_Y_MM = 130.0, 100.0
OUTER_RADIUS_MM = 6.0
PLATE_HEIGHT_MM = 10.0
CAVITY_X_MM, CAVITY_Y_MM = 85.0, 55.0
CAVITY_RADIUS_MM = 3.0
BOLT_DIAMETER_MM = 6.6
BOLT_POINTS_MM = ((-53,-38),(53,-38),(-53,38),(53,38))
CELL_X_COUNT, CELL_Y_COUNT = 23, 15
CELL_WIDTH_MM = 2.0
CELL_PITCH_MM = 3.6                       # clear ribs = 1.6 mm
GROOVE_WIDTH_MM, GROOVE_DEPTH_MM = 1.6, 1.2
SHIM_HEIGHTS_MM = (0.5, 1.0, 1.5)
SHIM_QUANTITY = 2
CALIBRATION_BASE_HEIGHTS_MM = (0.2, 0.4, 0.6, 0.8)  # Physical bases; choose ONE
GAUZE_TOTAL_COMPRESSED_EXAMPLE_MM = 0.4   # Example only; measure your actual gauze
# For a custom measured allowance, edit one base height above (e.g. .6 -> .7).
CORNER_SEGMENTS, CIRCLE_SEGMENTS = 16, 64
SCENE_NAME = 'LAPS Marle | Print parts'
TAG = 'LAPS_Marle_native_generator_revC'

STATE = {}

def validate_settings():
    if CELL_X_COUNT != 23 or CELL_Y_COUNT != 15:
        raise ValueError('This released pattern is 23 x 15. Revise drainage routes if changing the count.')
    if not 0 < CELL_WIDTH_MM < CELL_PITCH_MM:
        raise ValueError('Cells must leave positive ribs.')
    if not 0 < GROOVE_DEPTH_MM < PLATE_HEIGHT_MM:
        raise ValueError('Rear grooves must not cut the full plate thickness.')
    if any(h <= 0 for h in CALIBRATION_BASE_HEIGHTS_MM + SHIM_HEIGHTS_MM):
        raise ValueError('All ring heights must be positive.')
    if CAVITY_X_MM >= OUTER_X_MM or CAVITY_Y_MM >= OUTER_Y_MM:
        raise ValueError('The pulp opening must fit inside the plate.')
    for x,y in BOLT_POINTS_MM:
        r = BOLT_DIAMETER_MM / 2
        if abs(x)+r >= OUTER_X_MM/2 or abs(y)+r >= OUTER_Y_MM/2:
            raise ValueError('A bolt hole lies outside the plate.')
        if abs(x)-r < CAVITY_X_MM/2 and abs(y)-r < CAVITY_Y_MM/2:
            raise ValueError('A bolt hole overlaps the card opening.')


def make_scene():
    old = bpy.data.scenes.get(SCENE_NAME)
    if old and old.get('generator') != TAG:
        raise RuntimeError('The target scene name already belongs to the user. Rename SCENE_NAME.')
    if old:
        # Only remove geometry explicitly owned by this generator.
        for obj in list(old.objects):
            if obj.get('generator') == TAG:
                data = obj.data
                bpy.data.objects.remove(obj, do_unlink=True)
                if data and data.users == 0 and isinstance(data, bpy.types.Mesh):
                    bpy.data.meshes.remove(data)
        for collection in list(old.collection.children):
            if collection.get('generator') == TAG:
                bpy.data.collections.remove(collection)
        scene = old
    else:
        scene = bpy.data.scenes.new(SCENE_NAME)
    scene['generator'] = TAG
    if bpy.context.window:
        bpy.context.window.scene = scene
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.scale_length = 0.001
    scene.unit_settings.length_unit = 'MILLIMETERS'
    scene['units_note'] = '1 mesh coordinate = 1 millimetre. STL coordinates are millimetres.'
    scene['layout_note'] = 'Catalogue layout. Print one 130 x 100 mm plate at a time; choose individual STLs.'
    scene['gap_note'] = 'Choose ONE calibration base. WET gap = measured ring-stack height minus measured compressed total gauze allowance. .4 mm is an example, not a measured fabric property; measure dry thickness experimentally.'
    scene['print_note'] = 'PETG, .4 nozzle, plates .2 layer / 6 walls / 100% infill; rings .10 mm layer. Drain grooves down: inspect bridging and outlet clearance. Measure actual ring heights. Keep contact faces smooth; do not use fuzzy skin there.'
    return scene


def new_collection(scene, name):
    collection = bpy.data.collections.new(name)
    collection['generator'] = TAG
    scene.collection.children.link(collection)
    return collection


def mesh_obj(name, vertices, faces, collection=None):
    mesh = bpy.data.meshes.new(name + '_mesh')
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    (collection or STATE['print_collection']).objects.link(obj)
    obj['generator'] = TAG
    return obj


def rounded_contour(width, height, radius):
    pts = []
    for cx,cy,start in ((width/2-radius,height/2-radius,0),
                        (-width/2+radius,height/2-radius,90),
                        (-width/2+radius,-height/2+radius,180),
                        (width/2-radius,-height/2+radius,270)):
        for i in range(CORNER_SEGMENTS+1):
            angle = math.radians(start + 90*i/CORNER_SEGMENTS)
            pts.append((cx+radius*math.cos(angle),cy+radius*math.sin(angle)))
    return pts


def extrude_contour(name, pts, z0, z1, collection=None):
    n = len(pts)
    vertices = [(x,y,z) for z in (z0,z1) for x,y in pts]
    faces = [tuple(reversed(range(n))), tuple(range(n,2*n))]
    faces.extend((i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n))
    return mesh_obj(name, vertices, faces, collection)


def rounded_solid(name, width, height, radius, z0, z1):
    return extrude_contour(name, rounded_contour(width,height,radius), z0,z1)


def boxes_cutter(name, boxes):
    # Disjoint closed boxes in one mesh; one native exact Boolean for 345 cells.
    vertices, faces = [], []
    for x0,x1,y0,y1,z0,z1 in boxes:
        base = len(vertices)
        vertices.extend(((x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),
                         (x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)))
        faces.extend(tuple(base+i for i in face) for face in
                     ((3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)))
    return mesh_obj(name, vertices, faces, STATE['construction_collection'])


def box_cutter(name, x0,x1,y0,y1,z0,z1):
    return boxes_cutter(name, ((x0,x1,y0,y1,z0,z1),))


def cylinder_cutters(name, holes, z0, z1):
    vertices, faces = [], []
    n = CIRCLE_SEGMENTS
    for x,y,d in holes:
        base = len(vertices)
        for z in (z0,z1):
            vertices.extend((x+d/2*math.cos(2*math.pi*i/n),y+d/2*math.sin(2*math.pi*i/n),z) for i in range(n))
        faces.extend((tuple(base+i for i in reversed(range(n))),tuple(base+n+i for i in range(n))))
        faces.extend((base+i,base+(i+1)%n,base+(i+1)%n+n,base+i+n) for i in range(n))
    return mesh_obj(name, vertices, faces, STATE['construction_collection'])


def construction_master(obj):
    if not KEEP_NATIVE_CONSTRUCTION:
        return None
    master = bpy.data.objects.new('EDITABLE | ' + obj.name, obj.data.copy())
    STATE['construction_collection'].objects.link(master)
    master['generator'] = TAG
    master['editing_note'] = 'Native profile plus editable exact Boolean cutters. Manual edits affect this master only. For reproducible print regeneration, edit parameters in the embedded source and run it again.'
    master.hide_render = True
    master.hide_set(True)
    STATE['masters'][obj.name] = master
    return master


def clean_mesh(obj):
    # Micrometre-level welding is much smaller than the smallest printed feature.
    # Never fill holes or use a voxel remesh: those could change the drain sizes.
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=0.00001)
    bmesh.ops.dissolve_degenerate(bm, edges=list(bm.edges), dist=0.0000001)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()


def boolean_apply(obj, cutter, label, operation='DIFFERENCE'):
    for selected in list(bpy.context.selected_objects):
        selected.select_set(False)
    obj.hide_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    modifier = obj.modifiers.new(label, 'BOOLEAN')
    modifier.operation = operation
    modifier.solver = 'EXACT'
    modifier.object = cutter
    master = STATE['masters'].get(obj.name)
    if master:
        source_mod = master.modifiers.new(label, 'BOOLEAN')
        source_mod.operation = operation
        source_mod.solver = 'EXACT'
        source_mod.object = cutter
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    clean_mesh(obj)
    if master:
        # Move all preserved cutters into native construction, even cavity cuts.
        for col in list(cutter.users_collection):
            if col != STATE['construction_collection']:
                col.objects.unlink(cutter)
        if cutter.name not in STATE['construction_collection'].objects:
            STATE['construction_collection'].objects.link(cutter)
        cutter.hide_render = True
        cutter.hide_set(True)
        cutter['editing_note'] = 'Boolean cutter; hidden from print layout. It remains editable in Native construction.'
    else:
        data = cutter.data
        bpy.data.objects.remove(cutter, do_unlink=True)
        if data.users == 0:
            bpy.data.meshes.remove(data)


def subtract(obj,cutter,label):
    return boolean_apply(obj,cutter,label,'DIFFERENCE')


def union(obj,cutter,label):
    return boolean_apply(obj,cutter,label,'UNION')


def bolt_holes(obj, height):
    subtract(obj, cylinder_cutters(obj.name+' | four corner M6 clearance holes',
             [(x,y,BOLT_DIAMETER_MM) for x,y in BOLT_POINTS_MM], -1,height+1), '4 x diameter 6.6 mm')


def make_plate():
    obj = rounded_solid('marle_plate_PRINT_2', OUTER_X_MM,OUTER_Y_MM,OUTER_RADIUS_MM,0,PLATE_HEIGHT_MM)
    construction_master(obj)
    bolt_holes(obj,PLATE_HEIGHT_MM)
    h = CELL_WIDTH_MM/2
    boxes = []
    for j in range(CELL_Y_COUNT):
        y = (j-(CELL_Y_COUNT-1)/2)*CELL_PITCH_MM
        for i in range(CELL_X_COUNT):
            x = (i-(CELL_X_COUNT-1)/2)*CELL_PITCH_MM
            boxes.append((x-h,x+h,y-h,y+h,-1,PLATE_HEIGHT_MM+1))
    subtract(obj,boxes_cutter('345 | 2x2 mm through cells',boxes),'345 square drainage cells; ribs 1.6 mm')
    half = GROOVE_WIDTH_MM/2
    row_boxes = []
    for j in range(CELL_Y_COUNT):
        y = (j-(CELL_Y_COUNT-1)/2)*CELL_PITCH_MM
        row_boxes.append((-OUTER_X_MM/2-1,OUTER_X_MM/2+1,y-half,y+half,-0.1,GROOVE_DEPTH_MM))
    subtract(obj,boxes_cutter('Rear drainage | 15 full-width rows',row_boxes),'15 rear rows 1.6 wide x 1.2 deep')
    column_boxes = []
    for i in range(CELL_X_COUNT):
        x = (i-(CELL_X_COUNT-1)/2)*CELL_PITCH_MM
        column_boxes.append((x-half,x+half,-OUTER_Y_MM/2-1,OUTER_Y_MM/2+1,-0.1,GROOVE_DEPTH_MM))
    subtract(obj,boxes_cutter('Rear drainage | 23 full-height columns',column_boxes),'23 rear columns 1.6 wide x 1.2 deep')
    obj['drain_cells'] = CELL_X_COUNT*CELL_Y_COUNT
    obj['cell_dimensions_mm'] = [CELL_WIDTH_MM,CELL_WIDTH_MM]
    obj['rib_width_mm'] = CELL_PITCH_MM-CELL_WIDTH_MM
    obj['bolt_holes'] = len(BOLT_POINTS_MM)
    obj['rear_full_width_row_count'] = CELL_Y_COUNT
    obj['rear_full_height_column_count'] = CELL_X_COUNT
    obj['rear_groove_dimensions_mm'] = [GROOVE_WIDTH_MM,GROOVE_DEPTH_MM]
    obj['print_orientation'] = 'Rear grooves on bed, flat pressing face uppermost.'
    obj['print_quantity'] = 2
    return obj


def make_ring(height, compensation=False):
    name = f'marle_base_{height:.1f}mm_PRINT_1' if compensation else f'marle_shim_{height:.1f}mm_PRINT_2'
    obj = rounded_solid(name,OUTER_X_MM,OUTER_Y_MM,OUTER_RADIUS_MM,0,height)
    construction_master(obj)
    cutter = rounded_solid('Card opening | 85x55 R3 mm',CAVITY_X_MM,CAVITY_Y_MM,CAVITY_RADIUS_MM,-1,height+1)
    subtract(obj,cutter,'Card opening 85x55 R3 mm')
    bolt_holes(obj,height)
    obj['ring_height_mm'] = height
    obj['nominal_wet_gap_contribution_mm'] = 0 if compensation else height
    obj['print_quantity'] = 1 if compensation else SHIM_QUANTITY
    if compensation:
        obj['gauze_allowance_note'] = 'Select ONE base by measuring total compressed gauze thickness; this is its physical height, not a guaranteed fabric allowance.'
    return obj



def finish_mesh(obj, expected_dimensions):
    clean_mesh(obj)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.triangulate(bm,faces=list(bm.faces))
    bm.verts.ensure_lookup_table()
    nonmanifold = sum(not e.is_manifold for e in bm.edges)
    loose = sum(not v.link_faces for v in bm.verts)
    components = 0
    visited = set()
    for v in bm.verts:
        if v.index in visited:
            continue
        components += 1
        stack = [v]
        visited.add(v.index)
        while stack:
            item = stack.pop()
            for e in item.link_edges:
                other = e.other_vert(item)
                if other.index not in visited:
                    visited.add(other.index)
                    stack.append(other)
    volume = bm.calc_volume(signed=True)
    if nonmanifold or loose or components != 1 or volume <= 0:
        bm.free()
        raise RuntimeError(f'{obj.name}: nonmanifold={nonmanifold}, loose={loose}, connected components={components}, signed volume={volume}. Export stopped.')
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    dims = [max(v.co[i] for v in obj.data.vertices)-min(v.co[i] for v in obj.data.vertices) for i in range(3)]
    if any(abs(a-b) > 0.001 for a,b in zip(dims,expected_dimensions)):
        raise RuntimeError(f'{obj.name}: actual dimensions {dims} differ from {expected_dimensions}.')
    obj['dimensions_mm'] = dims
    obj['volume_mm3'] = volume
    obj['closed_mesh_check'] = True
    obj['print_material'] = 'PETG'
    return {'name':obj.name,'dimensions_mm':dims,'volume_mm3':volume,'nonmanifold_edges':0,'connected_components':1,'triangles':len(obj.data.polygons),'print_quantity':obj['print_quantity']}


def write_stl_mm(obj,path):
    # Binary writer uses the mesh's own coordinates, not catalogue positions.
    mesh = obj.data
    mesh.calc_loop_triangles()
    min_z = min(v.co.z for v in mesh.vertices)
    with path.open('wb') as stream:
        stream.write(b'LAPS Marle revC native Blender; coordinates in millimetres'.ljust(80,b' '))
        stream.write(struct.pack('<I',len(mesh.loop_triangles)))
        for triangle in mesh.loop_triangles:
            vertices = [Vector(mesh.vertices[i].co) for i in triangle.vertices]
            normal = (vertices[1]-vertices[0]).cross(vertices[2]-vertices[0]).normalized()
            numbers = list(normal)
            for v in vertices:
                numbers.extend((v.x,v.y,v.z-min_z))
            stream.write(struct.pack('<12fH',*numbers,0))


def material(name,color):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.diffuse_color = (*color,1)
    return mat


def duplicate(obj,name,collection=None):
    dup = bpy.data.objects.new(name,obj.data.copy())
    (collection or STATE['print_collection']).objects.link(dup)
    for k in obj.keys():
        dup[k] = obj[k]
    return dup


def add_label(body, location, size=6):
    curve = bpy.data.curves.new('LAPS label','FONT')
    curve.body = body
    curve.size = size
    obj = bpy.data.objects.new('LABEL | '+body,curve)
    STATE['label_collection'].objects.link(obj)
    obj['generator'] = TAG
    obj.location = location
    obj.hide_render = True
    return obj


def embed_source():
    # When pasted into the Text Editor, the active text is the portable source.
    script_text = None
    try:
        script_path = Path(__file__)
        if script_path.is_file():
            script_text = script_path.read_text(encoding='utf-8')
    except NameError:
        pass
    if script_text is None and bpy.context.space_data and bpy.context.space_data.type == 'TEXT_EDITOR':
        script_text = bpy.context.space_data.text.as_string()
    if script_text:
        text = bpy.data.texts.get('LAPS_Marle_Blender.py') or bpy.data.texts.new('LAPS_Marle_Blender.py')
        text.clear()
        text.write(script_text)
    readme = bpy.data.texts.get('READ ME | LAPS Marle') or bpy.data.texts.new('READ ME | LAPS Marle')
    readme.clear()
    readme.write('LAPS MARLE — NATIVE BLENDER PROJECT, REVISION C\n\nAll mesh dimensions and STL numbers are millimetres.\nPrint TWO identical 130 x 100 x 10 mm PETG plates.\nEach has FOUR corner M6 clearance holes, 345 square 2 x 2 mm cells,\nand 15 x 23 rear crosshatch channels 1.6 mm wide, 1.2 mm deep.\n\nCalibration bases supplied: .2, .4, .6, .8 mm physical height (one each).\nCHOOSE ONE base according to the measured compressed total gauze allowance.\nDo not stack all four bases. Modify CALIBRATION_BASE_HEIGHTS_MM in the source\nfor a custom measured base. Plain cotton gauze is bought, not 3D printed.\nStart with one flat layer at each pulp face, cut inside the card opening;\ncheck fibre loss in runoff and remeasure allowance if adding a layer.\n\nPrint TWO each of .5, 1 and 1.5 mm physical shims.\nWet cavity = measured ring-stack height minus measured compressed total gauze.\nExamples ONLY if the chosen .4 mm base exactly compensates the actual gauze:\n.5 mm wet gap = .5 mm shim\n1 mm = 1 mm shim\n2 mm = 1.5 + .5 mm\n3 mm = 1.5 + 1.5 mm\n4 mm = 1.5 + 1.5 + 1 mm\n5 mm = 1.5 + 1.5 + 1 + 1 mm\nWet gap and final dry thickness differ; measure after consistent drying.\n\nHardware: FOUR M6 x 40 fully threaded metal bolts, FOUR M6 nuts,\nEIGHT large M6 washers nominal OD18 x 1.6 mm. Bolt heads above, nuts below.\nM6 x 35 fits only thinner measured stacks; retain full nut engagement.\nNo hinge, M4 hardware or steel plates belong to this revision.\n\nNative construction collection holds blank profiles and live exact Boolean\ncutters. It is hidden by default. Applied print meshes are closed, connected\nsolids checked before export. Export individual STL parts; catalogue positions\nare not a print bed and are not included in the native STL coordinates.\nExisting non-generator user objects are preserved in their original scene.\n\nPETG plates: .4 mm nozzle, .2 mm layers, at least six wall lines, solid infill.\nThin rings: verified .10 mm layers. Measure real ring-stack height.\nKeep gauze contact faces and spacer seats smooth, without slicer fuzzy skin.\n\nThis thinner four-corner prototype has no verified pressing-load rating.\nClose gently by hand in diagonal order, inspect for bowing, and leave drainage\noutlets and lower nuts clear of the support. Ring seating does not measure\npulp pressure; further tightening mainly loads the PETG ring/lands.\n')


def setup_view(scene,objects):
    for selected in list(bpy.context.selected_objects):
        selected.select_set(False)
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                space = area.spaces.active
                space.clip_start,space.clip_end = 0.1,10000
                space.shading.color_type = 'MATERIAL'
                space.region_3d.view_distance = 650
                space.region_3d.view_location = (0,-10,0)
                # Top orthographic catalogue view, all individual parts visible.
                space.region_3d.view_rotation = Quaternion((1,0,0,0))
                space.region_3d.view_perspective = 'ORTHO'


def main():
    validate_settings()
    scene = make_scene()
    STATE.update({'scene':scene,'masters':{}})
    STATE['print_collection'] = new_collection(scene,'01 | LAPS Marle — PRINT parts')
    STATE['construction_collection'] = new_collection(scene,'02 | Native editable construction — hidden')
    STATE['label_collection'] = new_collection(scene,'03 | Catalogue labels — not printable')
    print('LAPS Marle: building 345 square-cell plate with four corner holes and 15 x 23 rear channels...',flush=True)
    plate = make_plate()
    unique = [(plate,'marle_plate_PRINT_2_native.stl',(OUTER_X_MM,OUTER_Y_MM,PLATE_HEIGHT_MM))]
    for height in CALIBRATION_BASE_HEIGHTS_MM:
        base = make_ring(height,True)
        unique.append((base,f'marle_base_{height:.1f}mm_PRINT_1_native.stl',(OUTER_X_MM,OUTER_Y_MM,height)))
    for height in SHIM_HEIGHTS_MM:
        ring = make_ring(height)
        unique.append((ring,f'marle_shim_{height:.1f}mm_PRINT_2_native.stl',(OUTER_X_MM,OUTER_Y_MM,height)))
    report = []
    for obj,filename,dims in unique:
        print('LAPS Marle: validating '+obj.name,flush=True)
        report.append(finish_mesh(obj,dims))
        obj['stl_filename'] = filename
    display = []
    for obj,_,_ in unique:
        qty = obj['print_quantity']
        display.append(obj)
        for copy in range(2,qty+1):
            display.append(duplicate(obj,obj.name+f' | copy {copy}'))
    mats = (material('LAPS Marle | teal PETG',(0.11,0.50,0.43)),material('LAPS Marle | amber shims',(0.93,0.49,0.13)),material('LAPS Marle | blue calibration bases',(0.37,0.56,0.74)))
    for i,obj in enumerate(display):
        obj.location = ((i%4-1.5)*(OUTER_X_MM+20),(1-i//4)*130,0)
        obj.data.materials.clear()
        obj.data.materials.append(mats[0] if 'plate' in obj.name.lower() else mats[2] if 'base' in obj.name.lower() else mats[1])
        add_label(obj.name,(obj.location.x-64,obj.location.y-60,0),2.9)
    STATE['construction_collection'].hide_render = True
    embed_source()
    setup_view(scene,display)
    OUTPUT_DIR.mkdir(parents=True,exist_ok=True)
    if EXPORT_STL:
        stl_dir = OUTPUT_DIR/'native_stl'
        stl_dir.mkdir(exist_ok=True)
        for obj,filename,_ in unique:
            write_stl_mm(obj,stl_dir/filename)
    report_data = {'generator':TAG,'revision':'C','Blender_version':bpy.app.version_string,'units':'mm','external_CAD_dependencies':False,'square_drain_cells':345,'cell_size_mm':[2,2],'ribs_mm':1.6,'bolt_holes_per_plate':4,'rear_row_channels':15,'rear_column_channels':23,'parts':report,'print_objects':len(display),'calibration_base_policy':'Choose ONE measured base; not all four','gauze_assumption_total_mm':GAUZE_TOTAL_COMPRESSED_EXAMPLE_MM,'physical_load_tested':False}
    (OUTPUT_DIR/'native_geometry_validation.json').write_text(json.dumps(report_data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if SAVE_BLEND:
        bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT_DIR/'LAPS_Marle_Prototips.blend'),copy=True)
    print('LAPS MARLE COMPLETE: '+str(OUTPUT_DIR),flush=True)

if __name__ == '__main__':
    main()
