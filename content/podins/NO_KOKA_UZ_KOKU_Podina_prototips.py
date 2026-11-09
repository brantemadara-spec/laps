import bpy
import math
from mathutils import Vector
import bmesh

# ============================================================
# NO KOKA UZ KOKU — UNIVERSĀLĀ SPIEDFORMA V4.1 — SLĪPĀS AUSTIŅAS
# Ar maināmiem 3/4/5 mm serdeņiem un pārplūdes kameru
# Visi izmēri milimetros
# ============================================================

# ---------- PODIŅŠ ----------
POT_H = 70.0
POT_TOP_OD = 90.0
POT_BOTTOM_OD = 65.0
POT_BOTTOM_T = 4.0
WALL_OPTIONS = (3.0, 4.0, 5.0)

# ---------- ĀRĒJĀ FORMA ----------
MOLD_WALL = 10.0
MOLD_TOP_OD = POT_TOP_OD + 2.0 * MOLD_WALL       # 110
MOLD_BOTTOM_OD = POT_BOTTOM_OD + 2.0 * MOLD_WALL # 85

# ---------- PĀRPLŪDES KAMERA ----------
OVERFLOW_H = 12.0
OVERFLOW_ID = 102.0
OVERFLOW_OD = 124.0
OVERFLOW_SKIRT_H = 3.0
OVERFLOW_SKIRT_ID = MOLD_TOP_OD + 0.8
TRIM_Z = POT_H

# ---------- SERDEŅA AUGŠDAĻA ----------
STOP_D = 118.0
STOP_T = 6.0
PRESS_PAD_D = 32.0
PRESS_PAD_H = 10.0

# ---------- SALIKŠANAS TOLERANCES ----------
PIN_D = 5.0
PIN_HOLE_D = 5.6
PIN_EXTEND = 6.0
PIN_OVERLAP = 2.0

M6_CLEARANCE = 6.8
M12_CLEARANCE = 13.5
M12_NUT_AF = 19.5
M12_NUT_DEPTH = 5.5

# ---------- SĀNU AUSIS ----------
EAR_X = 12.0
EAR_Y = 18.0
EAR_Z = 16.0
# V4.1: lokāli uzlabotas sānu austiņas drukai vertikālā orientācijā.
# Apakšējās pārejas ir 45° pret XY drukas galdu; M6 augšējā
# cauruma daļa ir 45° jumtiņš, saglabājot Ø6,8 mm apaļo vietu.
EAR_HOLE_Z = (34.0, 54.0)
EAR_OUTWARD_OFFSET = 7.0
EAR_RAMP_RUN = 24.0
EAR_RAMP_OVERLAP = 0.25
# Sānu stiprinājumiem: DIN125 M6 Ø12 paplāksnes (ne Ø18).
# Pārējās V4 pamatnes, STOP un kameras kļūdas vēl jālabo.

# ---------- PAMATNE / AUGŠĒJĀ PLĀKSNE ----------
BASE_D = 150.0
BASE_T = 10.0

TOP_D = 150.0
TOP_T = 10.0

ROD_RADIUS = 65.0
ROD_HOLE_D = 6.8

# ---------- SIETS ----------
SIEVE_D = 62.0
SIEVE_T = 1.4
SIEVE_HOLE_D = 2.6

# ---------- VENTILĀCIJA ----------
VENT_D = 2.2
VENT_Z = 56.0
VENT_COUNT = 8

# ---------- PAMATNES LIGZDA ----------
MOLD_SEAT_DEPTH = 2.5
MOLD_SEAT_OUTER_D = MOLD_BOTTOM_OD + 0.8
MOLD_SEAT_INNER_D = POT_BOTTOM_OD - 0.8


# ============================================================
# BLENDER VIENĪBAS
# ============================================================

scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.length_unit = 'MILLIMETERS'
scene.unit_settings.scale_length = 0.001


# ============================================================
# PALĪGFUNKCIJAS
# ============================================================

def ensure_object_mode():

    if (
        bpy.context.object is not None
        and bpy.context.object.mode != 'OBJECT'
    ):

        bpy.ops.object.mode_set(
            mode='OBJECT'
        )


def clear_scene():

    ensure_object_mode()

    bpy.ops.object.select_all(
        action='SELECT'
    )

    bpy.ops.object.delete(
        use_global=False
    )


def set_active(obj):

    ensure_object_mode()

    bpy.ops.object.select_all(
        action='DESELECT'
    )

    obj.select_set(True)

    bpy.context.view_layer.objects.active = obj


def add_cylinder(
    name,
    diameter,
    height,
    z0=0.0,
    vertices=96
):

    bpy.ops.mesh.primitive_cylinder_add(

        vertices=vertices,

        radius=diameter / 2.0,

        depth=height,

        end_fill_type='NGON',

        location=(
            0.0,
            0.0,
            z0 + height / 2.0
        )
    )

    obj = bpy.context.object

    obj.name = name

    return obj


def add_frustum(
    name,
    bottom_d,
    top_d,
    height,
    z0=0.0,
    vertices=128
):

    bpy.ops.mesh.primitive_cone_add(

        vertices=vertices,

        radius1=bottom_d / 2.0,

        radius2=top_d / 2.0,

        depth=height,

        end_fill_type='NGON',

        location=(
            0.0,
            0.0,
            z0 + height / 2.0
        )
    )

    obj = bpy.context.object

    obj.name = name

    return obj


def add_cube(
    name,
    dims,
    loc
):

    bpy.ops.mesh.primitive_cube_add(
        size=2.0,
        location=loc
    )

    obj = bpy.context.object

    obj.name = name

    obj.dimensions = dims

    set_active(obj)

    bpy.ops.object.transform_apply(
        location=False,
        rotation=False,
        scale=True
    )

    return obj


def add_cylinder_between(
    name,
    diameter,
    p1,
    p2,
    vertices=64
):

    p1 = Vector(p1)
    p2 = Vector(p2)

    direction = p2 - p1

    length = direction.length

    midpoint = (
        p1 + p2
    ) / 2.0


    bpy.ops.mesh.primitive_cylinder_add(

        vertices=vertices,

        radius=diameter / 2.0,

        depth=length,

        end_fill_type='NGON',

        location=midpoint
    )


    obj = bpy.context.object

    obj.name = name


    obj.rotation_mode = 'QUATERNION'

    obj.rotation_quaternion = (
        direction.to_track_quat(
            'Z',
            'Y'
        )
    )


    return obj


def add_yz_prism(name, x0, x1, yz_points):
    """Slēgta prizma ar atklāti definētu YZ profilu; izmēri mm."""
    count = len(yz_points)
    verts = [(x, y, z) for x in (x0, x1) for y, z in yz_points]
    faces = [tuple(reversed(range(count))), tuple(range(count, 2 * count))]
    faces += [(i, (i + 1) % count, (i + 1) % count + count, i + count) for i in range(count)]
    mesh = bpy.data.meshes.new(name + '_MESH')
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def add_m6_teardrop(name, y, z):
    """Ø6,8 mm apaļā daļa + 45° jumtiņš; ass paralēla X."""
    cutter = add_cylinder_between(name, M6_CLEARANCE, (-20, y, z), (20, y, z), vertices=64)
    radius = M6_CLEARANCE / 2.0
    tangent = radius / math.sqrt(2.0)
    roof = add_yz_prism(name + '_45_ROOF', -20, 20, [
        (y - tangent, z + tangent),
        (y + tangent, z + tangent),
        (y, z + radius * math.sqrt(2.0)),
    ])
    boolean_apply(cutter, roof, 'UNION')
    return cutter


def boolean_apply(
    target,
    tool,
    operation='DIFFERENCE'
):

    if target is None or tool is None:

        raise RuntimeError(
            "Boolean: trūkst target vai tool objekta."
        )


    set_active(target)


    modifier = target.modifiers.new(
        name="BOOL_TEMP",
        type='BOOLEAN'
    )

    modifier.operation = operation

    modifier.solver = 'EXACT'

    modifier.object = tool


    bpy.context.view_layer.update()


    try:

        bpy.ops.object.modifier_apply(
            modifier=modifier.name
        )

    except Exception as error:

        raise RuntimeError(

            f"Boolean kļūda objektam "
            f"'{target.name}' ar "
            f"'{tool.name}': {error}"

        )


    if tool.name in bpy.data.objects:

        bpy.data.objects.remove(
            tool,
            do_unlink=True
        )


    if target.type == 'MESH':

        target.data.validate(
            verbose=False
        )

        target.data.update()


def copy_object(
    obj,
    new_name
):

    new_obj = obj.copy()

    new_obj.data = obj.data.copy()

    bpy.context.collection.objects.link(
        new_obj
    )

    new_obj.name = new_name

    return new_obj


def radius_at_z(
    bottom_d,
    top_d,
    z,
    height
):

    r0 = bottom_d / 2.0

    r1 = top_d / 2.0


    return (
        r0
        +
        (r1 - r0)
        *
        (z / height)
    )


def make_hex_prism(
    name,
    across_flats,
    height,
    z0=0.0
):

    radius = (
        across_flats
        /
        (
            2.0
            *
            math.cos(
                math.radians(30.0)
            )
        )
    )


    bpy.ops.mesh.primitive_cylinder_add(

        vertices=6,

        radius=radius,

        depth=height,

        end_fill_type='NGON',

        location=(
            0.0,
            0.0,
            z0 + height / 2.0
        )
    )


    obj = bpy.context.object

    obj.name = name

    return obj


def core_diameter_at_z(
    wall_mm,
    z
):

    # Ārējās podiņa formas koniskums
    outer_d = (
        POT_BOTTOM_OD
        +
        (
            POT_TOP_OD
            -
            POT_BOTTOM_OD
        )
        *
        (
            z / POT_H
        )
    )


    # Serdenis ir par 2 x sienas biezumu mazāks
    return (
        outer_d
        -
        2.0 * wall_mm
    )


# ============================================================
# TĪRA SCĒNA
# ============================================================

clear_scene()


# ============================================================
# 01 + 02 — DIVDAĻĪGA ĀRĒJĀ FORMA
# ============================================================

shell = add_frustum(

    "MOLD_FULL",

    MOLD_BOTTOM_OD,

    MOLD_TOP_OD,

    POT_H
)


# Izgriežam podiņa ārējo ģeometriju

cavity = add_frustum(

    "POT_CAVITY",

    POT_BOTTOM_OD,

    POT_TOP_OD,

    POT_H + 2.0,

    z0=-1.0
)


boolean_apply(
    shell,
    cavity,
    'DIFFERENCE'
)


# ============================================================
# VENTILĀCIJAS CAURUMI
# ============================================================

inner_r = radius_at_z(

    POT_BOTTOM_OD,

    POT_TOP_OD,

    VENT_Z,

    POT_H
)


outer_r = radius_at_z(

    MOLD_BOTTOM_OD,

    MOLD_TOP_OD,

    VENT_Z,

    POT_H
)


for i in range(VENT_COUNT):

    angle = (
        2.0
        *
        math.pi
        *
        i
        /
        VENT_COUNT
        +
        math.radians(22.5)
    )


    direction = Vector((

        math.cos(angle),

        math.sin(angle),

        0.0

    ))


    p1 = direction * (
        inner_r - 1.0
    )


    p2 = direction * (
        outer_r + 3.0
    )


    p1.z = VENT_Z

    p2.z = VENT_Z


    vent = add_cylinder_between(

        f"VENT_{i}",

        VENT_D,

        p1,

        p2,

        vertices=32
    )


    boolean_apply(

        shell,

        vent,

        'DIFFERENCE'
    )


# ============================================================
# SADALĀM FORMU DIVĀS DAĻĀS
# ============================================================

left = copy_object(
    shell,
    "01_MOLD_LEFT"
)


right = copy_object(
    shell,
    "02_MOLD_RIGHT"
)


left_box = add_cube(

    "LEFT_HALF_BOX",

    (
        400.0,
        400.0,
        200.0
    ),

    (
        -200.0,
        0.0,
        POT_H / 2.0
    )
)


boolean_apply(
    left,
    left_box,
    'INTERSECT'
)


right_box = add_cube(

    "RIGHT_HALF_BOX",

    (
        400.0,
        400.0,
        200.0
    ),

    (
        200.0,
        0.0,
        POT_H / 2.0
    )
)


boolean_apply(
    right,
    right_box,
    'INTERSECT'
)


bpy.data.objects.remove(
    shell,
    do_unlink=True
)


# ============================================================
# POZICIONĒŠANAS TAPAS / LIGZDAS
# ============================================================

pin_z = 35.0


pin_outer_r = radius_at_z(

    MOLD_BOTTOM_OD,

    MOLD_TOP_OD,

    pin_z,

    POT_H
)


pin_y_abs = (
    pin_outer_r - 5.0
)


for i, y in enumerate(

    (
        pin_y_abs,
        -pin_y_abs
    )

):


    pin = add_cylinder_between(

        f"ALIGN_PIN_{i}",

        PIN_D,

        (
            -PIN_OVERLAP,
            y,
            pin_z
        ),

        (
            PIN_EXTEND,
            y,
            pin_z
        ),

        vertices=48
    )


    boolean_apply(
        left,
        pin,
        'UNION'
    )


    socket = add_cylinder_between(

        f"ALIGN_SOCKET_{i}",

        PIN_HOLE_D,

        (
            -0.5,
            y,
            pin_z
        ),

        (
            PIN_EXTEND + 0.8,
            y,
            pin_z
        ),

        vertices=48
    )


    boolean_apply(
        right,
        socket,
        'DIFFERENCE'
    )


# ============================================================
# SĀNU M6 SKRŪVJU AUSIS
# ============================================================

ear_index = 0
for z in EAR_HOLE_Z:
    local_outer_r = radius_at_z(MOLD_BOTTOM_OD, MOLD_TOP_OD, z, POT_H)
    for sign in (1.0, -1.0):
        y = sign * (local_outer_r + EAR_OUTWARD_OFFSET)
        y_outer = local_outer_r + EAR_OUTWARD_OFFSET + EAR_Y / 2.0
        y_root = y_outer - EAR_RAMP_RUN
        z_bottom = z - EAR_Z / 2.0
        z_root = z_bottom - EAR_RAMP_RUN
        assert z_root >= 0.0, '45° balsts nedrīkst iziet zem formas pamatnes'
        for obj, x0, x1, center_x, side in (
            (left, -EAR_X, 0.0, -EAR_X / 2.0, 'L'),
            (right, 0.0, EAR_X, EAR_X / 2.0, 'R'),
        ):
            ear = add_cube(f'EAR_{side}_{ear_index}', (EAR_X, EAR_Y, EAR_Z), (center_x, y, z))
            boolean_apply(obj, ear, 'UNION')
            ramp = add_yz_prism(f'EAR_45_SUPPORT_{side}_{ear_index}', x0, x1, [
                (sign * y_root, z_root),
                (sign * y_outer, z_bottom),
                (sign * y_outer, z_bottom + EAR_RAMP_OVERLAP),
                (sign * y_root, z_bottom + EAR_RAMP_OVERLAP),
            ])
            boolean_apply(obj, ramp, 'UNION')
        ear_index += 1

# Pēc VISIEM austiņu savienojumiem atjauno dobumu un ligzdas.
# Tas neļauj jaunajiem balstiem iestiepties podiņa masā vai aizpildīt tapu ligzdas.
for obj, side in ((left, 'L'), (right, 'R')):
    cavity_recut = add_frustum('CAVITY_RECUT_' + side, POT_BOTTOM_OD, POT_TOP_OD, POT_H + 2.0, z0=-1.0)
    boolean_apply(obj, cavity_recut, 'DIFFERENCE')
for i, y in enumerate((pin_y_abs, -pin_y_abs)):
    socket = add_cylinder_between(f'ALIGN_SOCKET_RECUT_{i}', PIN_HOLE_D,
        (-0.5, y, pin_z), (PIN_EXTEND + 0.8, y, pin_z), vertices=48)
    boolean_apply(right, socket, 'DIFFERENCE')
for z in EAR_HOLE_Z:
    local_outer_r = radius_at_z(MOLD_BOTTOM_OD, MOLD_TOP_OD, z, POT_H)
    for sign in (1.0, -1.0):
        y = sign * (local_outer_r + EAR_OUTWARD_OFFSET)
        for obj, side in ((left, 'L'), (right, 'R')):
            hole = add_m6_teardrop('M6_SIDE_' + side, y, z)
            boolean_apply(obj, hole, 'DIFFERENCE')

# Mikroskopisku Boolean šķembu apvienošana tikai abām pārveidotajām pusēm.
# 0,0001 mm ir ievērojami mazāk par drukas pielaidēm; nepieļauj
# float32 STL triangulācijas sabrukšanu gandrīz sakritušās virsotnēs.
for obj in (left, right):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=0.0001)
    bmesh.ops.triangulate(bm, faces=list(bm.faces), quad_method='BEAUTY', ngon_method='EAR_CLIP')
    bmesh.ops.dissolve_degenerate(bm, edges=list(bm.edges), dist=0.0001)
    # Divi koplanāro šķembu sakārtošanas cikli; ģeometriskās plaknes nemainās.
    for _cleanup_pass in range(2):
        bmesh.ops.dissolve_limit(bm, angle_limit=0.00001, use_dissolve_boundaries=False,
            verts=list(bm.verts), edges=list(bm.edges), delimit=set())
        bmesh.ops.triangulate(bm, faces=list(bm.faces), quad_method='BEAUTY', ngon_method='BEAUTY')
        bmesh.ops.dissolve_degenerate(bm, edges=list(bm.edges), dist=0.0001)
    # Exact Boolean var radīt pretēji vērstu, sakritušu nulles tilpuma seju pāri.
    # Dzēš tikai abus precīzi vienādā virsotņu kopā esošos pretējos poligonus.
    bm.verts.index_update()
    bm.normal_update()
    _face_groups = {}
    for _face in bm.faces:
        _key = tuple(sorted(_vert.index for _vert in _face.verts))
        _face_groups.setdefault(_key, []).append(_face)
    _opposite_duplicates = []
    for _faces in _face_groups.values():
        if len(_faces) == 2 and _faces[0].normal.dot(_faces[1].normal) < -0.999999:
            _opposite_duplicates.extend(_faces)
    if _opposite_duplicates:
        bmesh.ops.delete(bm, geom=_opposite_duplicates, context='FACES_ONLY')
    _wire_edges = [_edge for _edge in bm.edges if not _edge.link_faces]
    if _wire_edges:
        bmesh.ops.delete(bm, geom=_wire_edges, context='EDGES')
    _loose_verts = [_vert for _vert in bm.verts if not _vert.link_edges]
    if _loose_verts:
        bmesh.ops.delete(bm, geom=_loose_verts, context='VERTS')
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    obj['BOOLEAN_CLEANUP_MM'] = 0.0001

left['EAR_UPDATE'] = 'V4.1: 45-degree lower ramps, teardrop M6 roofs, flush split faces'
right['EAR_UPDATE'] = left['EAR_UPDATE']
left['EAR_HOLE_Z_MM'] = list(EAR_HOLE_Z)
right['EAR_HOLE_Z_MM'] = list(EAR_HOLE_Z)
left['EAR_WASHER_OD_MM'] = 12.0
right['EAR_WASHER_OD_MM'] = 12.0

left["PRINT_PART"] = True
right["PRINT_PART"] = True


# ============================================================
# 03 — PĀRPLŪDES GREDZENS / KAMERA
# ============================================================

overflow = add_cylinder(

    "03_OVERFLOW_COLLAR",

    OVERFLOW_OD,

    OVERFLOW_H,

    z0=0.0
)


# Izgriežam kameras centru

overflow_inner = add_cylinder(

    "OVERFLOW_INNER",

    OVERFLOW_ID,

    OVERFLOW_H + 2.0,

    z0=-1.0
)


boolean_apply(

    overflow,

    overflow_inner,

    'DIFFERENCE'
)


# ============================================================
# APAKŠĒJAIS CENTRĒŠANAS SVĀRKS
#
# Tas uzslīd uz ārējās formas augšējās daļas,
# lai pārplūdes kamera būtu centrēta.
# ============================================================

skirt = add_cylinder(

    "OVERFLOW_SKIRT",

    OVERFLOW_OD,

    OVERFLOW_SKIRT_H,

    z0=-OVERFLOW_SKIRT_H
)


skirt_inner = add_cylinder(

    "OVERFLOW_SKIRT_INNER",

    OVERFLOW_SKIRT_ID,

    OVERFLOW_SKIRT_H + 1.0,

    z0=(
        -OVERFLOW_SKIRT_H
        -
        0.5
    )
)


boolean_apply(

    skirt,

    skirt_inner,

    'DIFFERENCE'
)


boolean_apply(

    overflow,

    skirt,

    'UNION'
)


# ============================================================
# PĀRPLŪDES KAMERAS GAISA ATVERES
# ============================================================

for i in range(6):


    angle = (
        2.0
        *
        math.pi
        *
        i
        /
        6.0
    )


    direction = Vector((

        math.cos(angle),

        math.sin(angle),

        0.0

    ))


    p1 = direction * (
        OVERFLOW_ID / 2.0 - 1.0
    )


    p2 = direction * (
        OVERFLOW_OD / 2.0 + 2.0
    )


    p1.z = (
        OVERFLOW_H * 0.65
    )


    p2.z = (
        OVERFLOW_H * 0.65
    )


    vent = add_cylinder_between(

        f"OVERFLOW_VENT_{i}",

        2.0,

        p1,

        p2,

        vertices=32
    )


    boolean_apply(

        overflow,

        vent,

        'DIFFERENCE'
    )


overflow["PRINT_PART"] = True

overflow["DESCRIPTION"] = (
    "Pārplūdes kamera liekajai masai"
)


# ============================================================
# 04 / 05 / 06 — MAINĀMIE SERDEŅI
# ============================================================

def make_core(
    wall_mm,
    object_name
):


    # Serdenis sākas 4 mm virs podiņa apakšas
    core_z0 = POT_BOTTOM_T


    # Serdenis turpinās līdz pārplūdes kameras augšai
    core_body_h = (

        POT_H
        +
        OVERFLOW_H
        -
        POT_BOTTOM_T

    )


    bottom_d = core_diameter_at_z(

        wall_mm,

        POT_BOTTOM_T
    )


    top_d = core_diameter_at_z(

        wall_mm,

        POT_H + OVERFLOW_H
    )


    core = add_frustum(

        object_name,

        bottom_d,

        top_d,

        core_body_h,

        z0=core_z0
    )


    # ========================================================
    # STOP GREDZENS
    #
    # Kad tas pieskaras pārplūdes kameras augšai,
    # serde vairs nevar tikt spiesta zemāk.
    # ========================================================

    stop = add_cylinder(

        f"{object_name}_STOP",

        STOP_D,

        STOP_T,

        z0=(
            POT_H
            +
            OVERFLOW_H
        )
    )


    boolean_apply(

        core,

        stop,

        'UNION'
    )


    # ========================================================
    # SPIEDIENA BALSTS
    # ========================================================

    pad = add_cylinder(

        f"{object_name}_PAD",

        PRESS_PAD_D,

        PRESS_PAD_H,

        z0=(
            POT_H
            +
            OVERFLOW_H
            +
            STOP_T
        )
    )


    boolean_apply(

        core,

        pad,

        'UNION'
    )


    core["PRINT_PART"] = True

    core["WALL_THICKNESS_MM"] = wall_mm

    core["CORE_D_AT_POT_BOTTOM_MM"] = (
        bottom_d
    )

    core["CORE_D_AT_TRIM_PLANE_MM"] = (
        core_diameter_at_z(
            wall_mm,
            POT_H
        )
    )

    core["CORE_D_AT_OVERFLOW_TOP_MM"] = (
        top_d
    )


    return core


core3 = make_core(
    3.0,
    "04_CORE_3MM"
)


core4 = make_core(
    4.0,
    "05_CORE_4MM"
)


core5 = make_core(
    5.0,
    "06_CORE_5MM"
)


# ============================================================
# 07 — PAMATNE
# ============================================================

base = add_cylinder(

    "07_BASE",

    BASE_D,

    BASE_T
)


# ============================================================
# GREDZENVEIDA LIGZDA ĀRĒJAI FORMAI
# ============================================================

seat_outer = add_cylinder(

    "SEAT_OUTER",

    MOLD_SEAT_OUTER_D,

    MOLD_SEAT_DEPTH + 0.5,

    z0=(
        BASE_T
        -
        MOLD_SEAT_DEPTH
    )
)


seat_inner = add_cylinder(

    "SEAT_INNER",

    MOLD_SEAT_INNER_D,

    MOLD_SEAT_DEPTH + 1.5,

    z0=(
        BASE_T
        -
        MOLD_SEAT_DEPTH
        -
        0.5
    )
)


boolean_apply(

    seat_outer,

    seat_inner,

    'DIFFERENCE'
)


boolean_apply(

    base,

    seat_outer,

    'DIFFERENCE'
)


# ============================================================
# SIETA LIGZDA
# ============================================================

sieve_recess = add_cylinder(

    "SIEVE_RECESS",

    SIEVE_D + 0.8,

    SIEVE_T + 0.4,

    z0=(
        BASE_T
        -
        SIEVE_T
    )
)


boolean_apply(

    base,

    sieve_recess,

    'DIFFERENCE'
)


# ============================================================
# DRENĀŽAS CAURUMI
# ============================================================

drain_positions = [

    (
        0.0,
        0.0
    )

]


for radius, count in (

    (
        14.0,
        6
    ),

    (
        25.0,
        8
    )

):


    for i in range(count):


        angle = (
            2.0
            *
            math.pi
            *
            i
            /
            count
        )


        drain_positions.append((

            radius
            *
            math.cos(angle),

            radius
            *
            math.sin(angle)

        ))


for i, (
    x,
    y
) in enumerate(
    drain_positions
):


    hole = add_cylinder_between(

        f"DRAIN_{i}",

        5.0,

        (
            x,
            y,
            -1.0
        ),

        (
            x,
            y,
            BASE_T + 1.0
        ),

        vertices=32
    )


    boolean_apply(

        base,

        hole,

        'DIFFERENCE'
    )


# ============================================================
# PAMATNES 4 x M6 VĪTŅSTIEŅU CAURUMI
# ============================================================

for i in range(4):


    angle = math.radians(
        45.0
        +
        90.0 * i
    )


    x = (
        ROD_RADIUS
        *
        math.cos(angle)
    )


    y = (
        ROD_RADIUS
        *
        math.sin(angle)
    )


    hole = add_cylinder_between(

        f"BASE_ROD_HOLE_{i}",

        ROD_HOLE_D,

        (
            x,
            y,
            -1.0
        ),

        (
            x,
            y,
            BASE_T + 1.0
        ),

        vertices=48
    )


    boolean_apply(

        base,

        hole,

        'DIFFERENCE'
    )


base["PRINT_PART"] = True


# ============================================================
# 08 — SIETIŅŠ
# ============================================================

sieve = add_cylinder(

    "08_SIEVE",

    SIEVE_D,

    SIEVE_T
)


sieve_holes = [

    (
        0.0,
        0.0
    )

]


for radius, count in (

    (
        12.0,
        6
    ),

    (
        24.0,
        12
    )

):


    for i in range(count):


        angle = (
            2.0
            *
            math.pi
            *
            i
            /
            count
        )


        sieve_holes.append((

            radius
            *
            math.cos(angle),

            radius
            *
            math.sin(angle)

        ))


for i, (
    x,
    y
) in enumerate(
    sieve_holes
):


    hole = add_cylinder_between(

        f"SIEVE_HOLE_{i}",

        SIEVE_HOLE_D,

        (
            x,
            y,
            -1.0
        ),

        (
            x,
            y,
            SIEVE_T + 1.0
        ),

        vertices=24
    )


    boolean_apply(

        sieve,

        hole,

        'DIFFERENCE'
    )


sieve["PRINT_PART"] = True


# ============================================================
# 09 — AUGŠĒJĀ SPIEDPLĀKSNE
# ============================================================

top = add_cylinder(

    "09_TOP_PLATE",

    TOP_D,

    TOP_T
)


# ============================================================
# CENTRĀLAIS M12 CAURUMS
# ============================================================

centre_hole = add_cylinder_between(

    "TOP_M12_HOLE",

    M12_CLEARANCE,

    (
        0.0,
        0.0,
        -1.0
    ),

    (
        0.0,
        0.0,
        TOP_T + 1.0
    ),

    vertices=64
)


boolean_apply(

    top,

    centre_hole,

    'DIFFERENCE'
)


# ============================================================
# M12 UZGRIEŽŅA LIGZDA
# ============================================================

nut_pocket = make_hex_prism(

    "M12_NUT_POCKET",

    M12_NUT_AF,

    M12_NUT_DEPTH + 0.5,

    z0=(
        TOP_T
        -
        M12_NUT_DEPTH
    )
)


boolean_apply(

    top,

    nut_pocket,

    'DIFFERENCE'
)


# ============================================================
# AUGŠĒJĀS PLĀKSNES 4 x M6 CAURUMI
# ============================================================

for i in range(4):


    angle = math.radians(
        45.0
        +
        90.0 * i
    )


    x = (
        ROD_RADIUS
        *
        math.cos(angle)
    )


    y = (
        ROD_RADIUS
        *
        math.sin(angle)
    )


    hole = add_cylinder_between(

        f"TOP_ROD_HOLE_{i}",

        ROD_HOLE_D,

        (
            x,
            y,
            -1.0
        ),

        (
            x,
            y,
            TOP_T + 1.0
        ),

        vertices=48
    )


    boolean_apply(

        top,

        hole,

        'DIFFERENCE'
    )


top["PRINT_PART"] = True


# ============================================================
# IZKĀRTOJUMS BLENDER APSKATEI
# ============================================================

left.location = (
    -120.0,
    0.0,
    0.0
)


right.location = (
    120.0,
    0.0,
    0.0
)


overflow.location = (
    0.0,
    320,
    0.0
)


core3.location = (
    -130.0,
    170.0,
    0.0
)


core4.location = (
    0.0,
    170.0,
    0.0
)


core5.location = (
    130.0,
    170.0,
    0.0
)


base.location = (
    -115.0,
    -155.0,
    0.0
)


sieve.location = (
    0.0,
    -155.0,
    0.0
)


top.location = (
    120.0,
    -155.0,
    0.0
)


# ============================================================
# OBJEKTU INFORMĀCIJA
# ============================================================

left["DESCRIPTION"] = (
    "Kreisā ārējās formas puse"
)


right["DESCRIPTION"] = (
    "Labā ārējās formas puse"
)


core3["DESCRIPTION"] = (
    "Serdenis 3 mm sienai"
)


core4["DESCRIPTION"] = (
    "Serdenis 4 mm sienai"
)


core5["DESCRIPTION"] = (
    "Serdenis 5 mm sienai"
)


base["DESCRIPTION"] = (
    "Drenāžas pamatne"
)


sieve["DESCRIPTION"] = (
    "Perforētais sietiņš"
)


top["DESCRIPTION"] = (
    "Augšējā spiedplāksne"
)


# ============================================================
# PABEIGTS
# ============================================================

bpy.ops.object.select_all(
    action='DESELECT'
)


print("")

print(
    "============================================================"
)

print(
    "NO KOKA UZ KOKU — V4.1 IZVEIDOTS"
)

print(
    "============================================================"
)

print(
    "Gala podiņa augstums (TRIM plakne): 70 mm"
)

print(
    "Pārplūdes kamera: 12 mm virs gala malas"
)

print(
    "Liekā masa tiek novadīta pārplūdes kamerā."
)

print("")

print(
    "PRINTĒJAMĀS DETAĻAS:"
)


for name in [

    "01_MOLD_LEFT",

    "02_MOLD_RIGHT",

    "03_OVERFLOW_COLLAR",

    "04_CORE_3MM",

    "05_CORE_4MM",

    "06_CORE_5MM",

    "07_BASE",

    "08_SIEVE",

    "09_TOP_PLATE"

]:

    print(
        " -",
        name
    )


print("")

print(
    "Serdeņa diametri pie podiņa augšmalas:"
)

print(
    "3 mm siena ->",
    core_diameter_at_z(
        3.0,
        70.0
    ),
    "mm"
)

print(
    "4 mm siena ->",
    core_diameter_at_z(
        4.0,
        70.0
    ),
    "mm"
)

print(
    "5 mm siena ->",
    core_diameter_at_z(
        5.0,
        70.0
    ),
    "mm"
)

print(
    "============================================================"
)