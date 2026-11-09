# -*- coding: utf-8 -*-
"""LAPS: ielīmē Blender > Scripting > New un nospied Run Script / Alt+P.

Blender 4.x / 5.x; tikai Blender iebūvētais Python, bez papildinājumiem.
Izveido 2 PETG plāksnes un 5 maināmas starplikas, eksportē atsevišķus
STL milimetros un saglabā projekta kopiju. Tēraudu, sietu un skrūves pērk.
Darbojas jaunā ainā; esošos lietotāja objektus nedzēš.

STL: plate_A.stl un plate_B.stl drukā PA VIENAM, starplikas pēc vajadzības.
1–5 mm ir MITRĀS celulozes sprauga; sauso biezumu nosaka eksperimentos.
Šis ir fiziski nepārbaudīts prototips, nevis sertificēta spēka prese.
"""

import bpy
import bmesh
import math
import os
import struct
import json
from pathlib import Path
from mathutils import Vector

# -------- IESTATĪJUMI: izmēri MILIMETROS --------
OUTPUT_DIR = Path(os.environ.get('LAPS_OUTPUT_DIR', str(Path.home() / 'LAPS_prototips'))).expanduser()
EXPORT_STL = True
SAVE_BLEND = True
WET_GAPS_MM = (1, 2, 3, 4, 5)
MESH_THICKNESS_MM = 0.20  # VIENA sieta izmērīts saspiestais biezums

OUTER_X_MM = 130.0
OUTER_Y_MM = 100.0
OUTER_RADIUS_MM = 6.0
PLATE_HEIGHT_MM = 12.0
CAVITY_X_MM = 85.0
CAVITY_Y_MM = 55.0
CAVITY_RADIUS_MM = 3.0
BOLT_DIAMETER_MM = 6.6
DRAIN_DIAMETER_MM = 2.0
GROOVE_WIDTH_MM = 1.6
GROOVE_DEPTH_MM = 1.2
BOLT_POINTS_MM = ((-53, -38), (0, -38), (53, -38),
                  (-53, 0), (53, 0),
                  (-53, 38), (0, 38), (53, 38))
DRAIN_X_MM = tuple(range(-35, 36, 7))
DRAIN_Y_MM = tuple(range(-21, 22, 7))
CIRCLE_SEGMENTS = 64
CORNER_SEGMENTS = 16
SCENE_NAME = 'LAPS_Prototips'
TAG = 'LAPS_pulp_prototype_generated_v1'


def validate_settings():
    if MESH_THICKNESS_MM < 0 or not WET_GAPS_MM or any(g <= 0 for g in WET_GAPS_MM):
        raise ValueError('Sieta biezumam jābūt >=0, celulozes spraugām >0.')
    if len(set(WET_GAPS_MM)) != len(WET_GAPS_MM):
        raise ValueError('WET_GAPS_MM nedrīkst atkārtot vienu spraugu.')
    if not 0 < GROOVE_DEPTH_MM < PLATE_HEIGHT_MM:
        raise ValueError('Drenāžas rievas dziļumam jābūt mazākam par plāksnes biezumu.')
    if not 0 < OUTER_RADIUS_MM < min(OUTER_X_MM, OUTER_Y_MM)/2:
        raise ValueError('Nepareizs ārējais stūra rādiuss.')
    if not 0 < CAVITY_RADIUS_MM < min(CAVITY_X_MM, CAVITY_Y_MM)/2:
        raise ValueError('Nepareizs dobuma stūra rādiuss.')
    if CAVITY_X_MM >= OUTER_X_MM or CAVITY_Y_MM >= OUTER_Y_MM:
        raise ValueError('Dobumam jābūt mazākam par ārējo kontūru.')
    # The supplied bolt/drain pattern is tied to the original footprint.
    # Prevent misleading parametric changes that leave holes outside a plate.
    for x,y in BOLT_POINTS_MM:
        r=BOLT_DIAMETER_MM/2
        if abs(x)+r >= OUTER_X_MM/2-OUTER_RADIUS_MM or abs(y)+r >= OUTER_Y_MM/2-OUTER_RADIUS_MM:
            raise ValueError('Skrūvju caurumi pārāk tuvu malai; jāmaina arī to koordinātas.')
        if abs(x)-r < CAVITY_X_MM/2 and abs(y)-r < CAVITY_Y_MM/2:
            raise ValueError('Skrūves caurums iekrīt celulozes dobumā.')
    for x in DRAIN_X_MM:
        for y in DRAIN_Y_MM:
            if abs(x)+DRAIN_DIAMETER_MM/2 >= CAVITY_X_MM/2-CAVITY_RADIUS_MM or abs(y)+DRAIN_DIAMETER_MM/2 >= CAVITY_Y_MM/2-CAVITY_RADIUS_MM:
                raise ValueError('Drenāžas režģis vairs neatbilst dobumam.')


def make_scene():
    old=bpy.data.scenes.get(SCENE_NAME)
    if old and old.get('generator') != TAG:
        raise RuntimeError('Aina LAPS_Prototips jau pastāv un nav šī skripta radīta. Pārdēvē to.')
    if old:
        # Remove only objects explicitly marked by this generator.
        for obj in list(old.objects):
            if obj.get('generator') == TAG:
                mesh=obj.data if obj.type=='MESH' else None
                bpy.data.objects.remove(obj,do_unlink=True)
                if mesh and mesh.users==0:
                    bpy.data.meshes.remove(mesh)
        scene=old
    else:
        scene=bpy.data.scenes.new(SCENE_NAME)
    scene['generator']=TAG
    if bpy.context.window:
        bpy.context.window.scene=scene
    scene.unit_settings.system='METRIC'
    scene.unit_settings.scale_length=0.001
    scene.unit_settings.length_unit='MILLIMETERS'
    scene['units_note']='1 mesh coordinate = 1 mm; STL is written in mm.'
    return scene


def mesh_obj(scene,name,vertices,faces):
    mesh=bpy.data.meshes.new(name+'_mesh')
    mesh.from_pydata(vertices,[],faces)
    mesh.update()
    obj=bpy.data.objects.new(name,mesh)
    scene.collection.objects.link(obj)
    obj['generator']=TAG
    return obj


def rounded_contour(width,height,radius):
    pts=[]
    # Counter-clockwise contour; includes cardinal endpoints for exact bounds.
    for cx,cy,start in ((width/2-radius,height/2-radius,0),
                        (-width/2+radius,height/2-radius,90),
                        (-width/2+radius,-height/2+radius,180),
                        (width/2-radius,-height/2+radius,270)):
        for i in range(CORNER_SEGMENTS+1):
            angle=math.radians(start+90*i/CORNER_SEGMENTS)
            pts.append((cx+radius*math.cos(angle),cy+radius*math.sin(angle)))
    return pts


def extrude_contour(scene,name,pts,z0,z1):
    n=len(pts)
    vertices=[(x,y,z) for z in (z0,z1) for x,y in pts]
    faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]
    faces.extend((i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n))
    return mesh_obj(scene,name,vertices,faces)


def rounded_solid(scene,name,width,height,radius,z0,z1):
    return extrude_contour(scene,name,rounded_contour(width,height,radius),z0,z1)


def cylinder_cutters(scene,name,holes,z0,z1):
    # Disjoint closed cutters in one mesh; a single exact Boolean per hole set.
    vertices=[]; faces=[]
    n=CIRCLE_SEGMENTS
    for x,y,diameter in holes:
        base=len(vertices)
        for z in (z0,z1):
            vertices.extend((round(x+diameter/2*math.cos(2*math.pi*i/n),10),
                             round(y+diameter/2*math.sin(2*math.pi*i/n),10),z) for i in range(n))
        faces.append(tuple(base+i for i in reversed(range(n))))
        faces.append(tuple(base+n+i for i in range(n)))
        faces.extend((base+i,base+(i+1)%n,base+(i+1)%n+n,base+i+n) for i in range(n))
    return mesh_obj(scene,name,vertices,faces)


def box_cutter(scene,name,x0,x1,y0,y1,z0,z1):
    return extrude_contour(scene,name,[(x0,y0),(x1,y0),(x1,y1),(x0,y1)],z0,z1)


def subtract(scene,obj,cutter):
    for selected in list(bpy.context.selected_objects):selected.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active=obj
    modifier=obj.modifiers.new('LAPS_cut','BOOLEAN')
    modifier.operation='DIFFERENCE';modifier.solver='EXACT';modifier.object=cutter
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    # Weld numerical duplicates left by Boolean face bridges. This does not
    # fill holes: the final closed-mesh check must still pass independently.
    bm=bmesh.new();bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=0.00001)
    bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=0.0000001)
    bm.to_mesh(obj.data);bm.free();obj.data.update()
    mesh=cutter.data
    bpy.data.objects.remove(cutter,do_unlink=True)
    if mesh.users==0:bpy.data.meshes.remove(mesh)


def bolt_holes(scene,obj,height):
    holes=[(x,y,BOLT_DIAMETER_MM) for x,y in BOLT_POINTS_MM]
    subtract(scene,obj,cylinder_cutters(scene,'bolt_cutters',holes,-1,height+1))


def finish_mesh(obj,expected_dimensions):
    bm=bmesh.new();bm.from_mesh(obj.data)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bmesh.ops.triangulate(bm,faces=list(bm.faces))
    bad=sum(not e.is_manifold for e in bm.edges)
    if bad:
        bm.free()
        raise RuntimeError(f'{obj.name}: {bad} vaļējas/nekorektas malas; STL eksports apturēts.')
    volume=bm.calc_volume(signed=True)
    if volume<=0:
        bm.free();raise RuntimeError(f'{obj.name}: nekorekta tilpuma orientācija.')
    bm.to_mesh(obj.data);bm.free();obj.data.update()
    actual=[max(v.co[i] for v in obj.data.vertices)-min(v.co[i] for v in obj.data.vertices) for i in range(3)]
    if any(abs(a-b)>0.001 for a,b in zip(actual,expected_dimensions)):
        raise RuntimeError(f'{obj.name}: nepareizi izmēri {actual}.')
    obj['dimensions_mm']=actual
    obj['volume_mm3']=volume
    obj['print_material']='PETG'
    obj['print_quantity']=1
    obj['closed_mesh_check']=True
    return {'name':obj.name,'dimensions_mm':actual,'volume_mm3':volume,'closed_mesh':True,'triangles':len(obj.data.polygons)}


def make_plate(scene):
    obj=rounded_solid(scene,'Plate_A_PETG_130x100x12mm',OUTER_X_MM,OUTER_Y_MM,OUTER_RADIUS_MM,0,PLATE_HEIGHT_MM)
    bolt_holes(scene,obj,PLATE_HEIGHT_MM)
    holes=[(x,y,DRAIN_DIAMETER_MM) for y in DRAIN_Y_MM for x in DRAIN_X_MM]
    subtract(scene,obj,cylinder_cutters(scene,'drain_cutters',holes,-1,PLATE_HEIGHT_MM+1))
    half=GROOVE_WIDTH_MM/2
    for y in DRAIN_Y_MM:
        if y:
            subtract(scene,obj,box_cutter(scene,'back_groove',-OUTER_X_MM/2-1,OUTER_X_MM/2+1,y-half,y+half,-0.1,GROOVE_DEPTH_MM))
    # Centre row branches around the mid-side bolt bearing areas.
    branch_x=46.0
    subtract(scene,obj,box_cutter(scene,'middle_groove',-branch_x-half,branch_x+half,-half,half,-0.1,GROOVE_DEPTH_MM))
    for x in (-branch_x,branch_x):
        subtract(scene,obj,box_cutter(scene,'outlet_groove',x-half,x+half,-OUTER_Y_MM/2-1,half,-0.1,GROOVE_DEPTH_MM))
    obj['drain_holes']=len(holes);obj['bolt_holes']=len(BOLT_POINTS_MM)
    obj['print_orientation']='Z=0: drenāžas rievas uz galda; gludā preses virsma uz augšu.'
    return obj


def gap_label(n):return f'{n:g}'


def make_ring(scene,gap):
    height=gap+2*MESH_THICKNESS_MM
    obj=rounded_solid(scene,f'Starplika_{gap_label(gap)}mm_mitra_h{height:g}mm',OUTER_X_MM,OUTER_Y_MM,OUTER_RADIUS_MM,0,height)
    inner=rounded_solid(scene,'cavity_cutter',CAVITY_X_MM,CAVITY_Y_MM,CAVITY_RADIUS_MM,-1,height+1)
    subtract(scene,obj,inner);bolt_holes(scene,obj,height)
    obj['nominal_wet_pulp_gap_mm']=gap
    obj['mesh_thickness_each_mm']=MESH_THICKNESS_MM
    obj['actual_ring_height_mm']=height
    return obj


def write_stl_mm(obj,path):
    # Direct binary writer avoids differing STL add-ons/export-unit settings.
    # Object layout positions are intentionally excluded. Each part is at Z=0.
    mesh=obj.data;mesh.calc_loop_triangles()
    lower_z=min(v.co.z for v in mesh.vertices)
    with path.open('wb') as stream:
        stream.write(b'LAPS individual part; numeric coordinates in millimetres'.ljust(80,b' '))
        stream.write(struct.pack('<I',len(mesh.loop_triangles)))
        for triangle in mesh.loop_triangles:
            vertices=[Vector(mesh.vertices[i].co) for i in triangle.vertices]
            normal=(vertices[1]-vertices[0]).cross(vertices[2]-vertices[0]).normalized()
            numbers=list(normal)
            for v in vertices:numbers.extend((v.x,v.y,v.z-lower_z))
            stream.write(struct.pack('<12fH',*numbers,0))


def color_material(name,color):
    material=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.diffuse_color=(*color,1)
    return material


def main():
    validate_settings()
    scene=make_scene()
    print('LAPS: veido plāksnes ar 77 drenāžas caurumiem...',flush=True)
    plate_a=make_plate(scene)
    objects=[plate_a]
    report=[finish_mesh(plate_a,(OUTER_X_MM,OUTER_Y_MM,PLATE_HEIGHT_MM))]
    plate_b=bpy.data.objects.new('Plate_B_PETG_130x100x12mm',plate_a.data.copy())
    scene.collection.objects.link(plate_b)
    for k in plate_a.keys():plate_b[k]=plate_a[k]
    objects.append(plate_b)
    report.append(finish_mesh(plate_b,(OUTER_X_MM,OUTER_Y_MM,PLATE_HEIGHT_MM)))
    filenames=['plate_A.stl','plate_B.stl']
    for gap in WET_GAPS_MM:
        print(f'LAPS: starplika {gap:g} mm mitrajai spraugai...',flush=True)
        ring=make_ring(scene,float(gap))
        report.append(finish_mesh(ring,(OUTER_X_MM,OUTER_Y_MM,float(gap)+2*MESH_THICKNESS_MM)))
        objects.append(ring)
        height_label=f'{float(gap)+2*MESH_THICKNESS_MM:g}'.replace('.','p')
        filenames.append(f'starplika_{gap_label(gap)}mm_mitra_h{height_label}mm.stl')
    material_plate=color_material('LAPS_PETG_plaksnes',(0.12,0.50,0.44))
    material_ring=color_material('LAPS_PETG_starplikas',(0.94,0.50,0.16))
    for i,obj in enumerate(objects):
        obj.location=((i%3-1)*(OUTER_X_MM+22),(1-i//3)*(OUTER_Y_MM+22),0)
        obj.data.materials.clear();obj.data.materials.append(material_plate if i<2 else material_ring)
        obj['stl_filename']=filenames[i]
    scene['layout_note']='Izklājums apskatei. Drukai lieto atsevišķus STL; tas nav viens printera galds.'
    scene['hardware_note']='2 tērauda plāksnes 130×100×8, 8 M6×60 pilnas vītnes skrūves, 8 M6 uzgriežņi, 16 DIN9021 paplāksnes un 2 smalkie sieti ir atsevišķi nopērkami.'
    scene['mesh_note']='Starpliku h = mitrā sprauga + 2×izmērīts saspiests sieta biezums; sākuma vērtība 0,2 mm katram.'
    OUTPUT_DIR.mkdir(parents=True,exist_ok=True)
    if EXPORT_STL:
        stl_dir=OUTPUT_DIR/'STL';stl_dir.mkdir(exist_ok=True)
        for obj,filename in zip(objects,filenames):write_stl_mm(obj,stl_dir/filename)
    (OUTPUT_DIR/'geometry_report.json').write_text(json.dumps({'units':'mm','parts':report,'stl_files':filenames,'physical_prototype_tested':False},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for selected in list(bpy.context.selected_objects):selected.select_set(False)
    for obj in objects:obj.select_set(True)
    bpy.context.view_layer.objects.active=plate_a
    # Frame generated parts and set useful clipping in every available viewport.
    if bpy.context.window:
        for screen in bpy.data.screens:
            for area in screen.areas:
                if area.type=='VIEW_3D':
                    space=area.spaces.active
                    space.clip_start=0.1;space.clip_end=10000
                    space.shading.color_type='MATERIAL'
                    region=next((r for r in area.regions if r.type=='WINDOW'),None)
                    if region and screen==bpy.context.window.screen:
                        with bpy.context.temp_override(area=area,region=region):
                            bpy.ops.view3d.view_selected(use_all_regions=False)
    if SAVE_BLEND:
        bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT_DIR/'LAPS_Prototips.blend'),copy=True)
    print('\nLAPS PABEIGTS: '+str(OUTPUT_DIR),flush=True)
    print('Drukā plate_A un plate_B pa vienam + izvēlēto starpliku. STL izmēri ir mm.',flush=True)
    print('Mainot iestatījumus, atkārtota palaišana pārraksta šī skripta izvades failus.',flush=True)


if __name__=='__main__':
    main()
