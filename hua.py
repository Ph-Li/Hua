import rhinoscriptsyntax as rss
from math import pi, sin, cos, tan

# Parameters (mm)
CORE_RADIUS = 6.25
BEAM_HEIGHT = 5
BEAM_WIDTH = 3
BEAM_LENGTH = 56.25
BEAM_HALF_LENGTH = BEAM_LENGTH / 2
COLUMN_DIAMETER = 9

#             | \   / |
#       |\____| |___| |____/|
#       |_____| |___| |_____|    <-- layer 5
#         |\__|_|___|_|__/|
#         |_______________|    <-- layer 4
# |\________|_|__|_|__|_|________/|
# |_______________________________|    <-- layer 3
#     |\____|_|__|_|__|_|____/|
#     |_______________________|    <-- layer 2
#         |\_____|_|_____/|
#         |_______________|    <-- layer 1
#                | |
#                | |
#                | |
#                | |
#          ______| |______
#         /_______________\    <-- base

# Comment out parts you don't want to build.
BUILD_TARGET = (
    # 'base',
    # 'layer1',
    # 'layer2',
    'layer3',
    # 'layer4',
    'layer5',
)
# or just uncomment the following line to build them all.
# BUILD_TARGET = 'all'

# Add junctions between base and upper layers.
ADD_JUNCTION = True
# Remove draft curves used for extruding.
REMOVE_DRAFT = True


# Utility functions

def extrude_crv_along_line(curve_id, origin, vector):
    _srf = rss.AddPlanarSrf(curve_id)
    _crv = rss.AddLine(origin, rss.PointAdd(origin, vector))
    srf = rss.ExtrudeSurface(_srf, _crv)
    rss.DeleteObjects((_srf, _crv))
    return srf


def add_box(origin, x_vector, y_vector, z_vector):
    _srf = rss.AddSrfPt((
        origin,
        rss.PointAdd(origin, x_vector),
        rss.PointAdd(origin, rss.VectorAdd(x_vector, y_vector)),
        rss.PointAdd(origin, y_vector)
    ))
    _crv = rss.AddLine(origin, rss.PointAdd(origin, z_vector))
    box = rss.ExtrudeSurface(_srf, _crv)
    rss.DeleteObjects((_srf, _crv))
    return box


def quad_rotate_point(point, center_point=(0, 0, 0), axis=(0, 0, 1)):
    _vec = rss.PointSubtract(point, center_point)
    return [
        point,
        rss.PointAdd(center_point, rss.VectorRotate(_vec, 90.0, axis)),
        rss.PointAdd(center_point, rss.VectorRotate(_vec, 180.0, axis)),
        rss.PointAdd(center_point, rss.VectorRotate(_vec, -90.0, axis)),
    ]


def quad_rotate_object(object_id, center_point=(0, 0, 0), axis=None):
    _rotated = rss.RotateObject(
        object_id, center_point, 180.0, axis, copy=True)
    return [object_id, _rotated] + rss.RotateObjects((object_id, _rotated), center_point, 90.0, axis, copy=True)


def quad_mirror_object(object_id):
    _mirror = rss.MirrorObject(object_id, (0, -1, 0), (0, 1, 0), copy=True)
    return [object_id, _mirror] + rss.MirrorObjects((object_id, _mirror), (-1, 0, 0), (1, 0, 0), copy=True)


# Part 0: Base
if BUILD_TARGET == 'all' or 'base' in BUILD_TARGET:
    base_btm_origin = (BEAM_HALF_LENGTH, BEAM_HALF_LENGTH, 0)
    base_btm_pts = quad_rotate_point(base_btm_origin)
    base_top_pts = quad_rotate_point(rss.PointAdd(
        base_btm_origin,
        (-BEAM_HEIGHT * tan(pi/3), -BEAM_HEIGHT * tan(pi/3), BEAM_HEIGHT))
    )

    base = rss.BooleanUnion((
        rss.JoinSurfaces(
            [rss.AddSrfPt(base_btm_pts), rss.AddSrfPt(base_top_pts)]
            + quad_rotate_object(rss.AddSrfPt((
                base_btm_pts[0],
                base_btm_pts[1],
                base_top_pts[0],
                base_top_pts[1]
            ))),
            delete_input=True
        ),
        rss.AddCylinder((0, 0, 0), 107.5, CORE_RADIUS)
    ))


# Part 1: Layer 1

# PLANE_HEIGHT: Height where the layer is placed
PLANE_HEIGHT = 62.5

if BUILD_TARGET == 'all' or 'layer1' in BUILD_TARGET:
    beam_origin = (BEAM_HALF_LENGTH, CORE_RADIUS, PLANE_HEIGHT)
    beam_path = rss.AddPolyline((
        beam_origin,
        rss.PointAdd(beam_origin, (0, 0, 8)),
        rss.PointAdd(beam_origin, (-5, 0, BEAM_HEIGHT)),
        rss.PointAdd(beam_origin, (-BEAM_LENGTH + 5, 0, BEAM_HEIGHT)),
        rss.PointAdd(beam_origin, (-BEAM_LENGTH, 0, 8)),
        rss.PointAdd(beam_origin, (-BEAM_LENGTH, 0, 0)),
        beam_origin
    ))
    layer1 = rss.BooleanUnion(
        quad_rotate_object(
            extrude_crv_along_line(
                beam_path,
                beam_origin,
                (0, BEAM_WIDTH, 0)
            )))

    if ADD_JUNCTION:
        # Original `base` is deleted during the boolean union, re-binding name `base` for later reference.
        base = rss.BooleanUnion(
            base + quad_rotate_object(
                rss.AddCylinder((CORE_RADIUS, 0, PLANE_HEIGHT), 3, 0.8)
            ))
        diff = rss.BooleanDifference(layer1, base, delete_input=False)
        rss.DeleteObject(layer1)
        layer1 = diff

    if REMOVE_DRAFT:
        rss.DeleteObject(beam_path)


# Part 2: Layer 2
PLANE_HEIGHT = 75

BEAM_LENGTH = 80
BEAM_HALF_LENGTH = BEAM_LENGTH / 2

if BUILD_TARGET == 'all' or 'layer2' in BUILD_TARGET:
    beam_origin = (CORE_RADIUS, BEAM_HALF_LENGTH, PLANE_HEIGHT)
    beam_path = rss.AddPolyline((
        beam_origin,
        rss.PointAdd(beam_origin, (0, 0, 8)),
        rss.PointAdd(beam_origin, (0, -5, BEAM_HEIGHT)),
        rss.PointAdd(beam_origin, (0, -BEAM_LENGTH + 5, BEAM_HEIGHT)),
        rss.PointAdd(beam_origin, (0, -BEAM_LENGTH, 8)),
        rss.PointAdd(beam_origin, (0, -BEAM_LENGTH, 0)),
        beam_origin
    ))
    beam = extrude_crv_along_line(beam_path, beam_origin, (BEAM_WIDTH, 0, 0))
    beam_copy = rss.RotateObject(
        rss.CopyObject(beam, (11, 0, 0)), (0, 0, 0), 90.0)
    layer2 = rss.BooleanUnion(
        [beam, beam_copy]
        + rss.RotateObjects(
            (beam, beam_copy),
            (0, 0, 0),
            180.0,
            copy=True
        ))

    if ADD_JUNCTION:
        # Original `base` is deleted during the boolean union, re-binding name `base` for later reference.
        base = rss.BooleanUnion(
            base + quad_mirror_object(
                rss.AddCylinder((CORE_RADIUS, 1, PLANE_HEIGHT), 3, 0.8)
            )
        )
        slot = add_box(
            (CORE_RADIUS, 4, PLANE_HEIGHT),
            (-1, 0, 0),
            (0, -8, 0),
            (0, 0, 5)
        )
        layer2 = rss.BooleanUnion(
            layer2
            + [slot, rss.MirrorObject(slot, (0, -1, 0), (0, 1, 0), copy=True)]
        )
        diff = rss.BooleanDifference(layer2, base, delete_input=False)
        rss.DeleteObject(layer2)
        layer2 = diff

    if REMOVE_DRAFT:
        rss.DeleteObject(beam_path)


# Part 3: Layer 3
PLANE_HEIGHT = 87.5

BEAM_HALF_LENGTH = 35.75

if BUILD_TARGET == 'all' or 'layer3' in BUILD_TARGET:
    beam_origin = (CORE_RADIUS + 11, CORE_RADIUS + 11, PLANE_HEIGHT)
    beam_path = rss.AddPolyline((
        beam_origin,
        rss.PointAdd(beam_origin, (0, 0, BEAM_HEIGHT)),
        rss.PointAdd(beam_origin, (BEAM_HALF_LENGTH - 5, 0, BEAM_HEIGHT)),
        rss.PointAdd(beam_origin, (BEAM_HALF_LENGTH, 0, 8)),
        rss.PointAdd(beam_origin, (BEAM_HALF_LENGTH, 0, 0)),
        beam_origin
    ))
    beam = extrude_crv_along_line(beam_path, beam_origin, (0, BEAM_WIDTH, 0))
    layer3 = rss.BooleanUnion(
        quad_rotate_object(
            rss.BooleanUnion((
                beam,
                rss.MirrorObject(beam, (1, 1, 0), (-1, -1, 0), copy=True),
                add_box(
                    (14.25, 14.25, PLANE_HEIGHT - 7.5),
                    (COLUMN_DIAMETER, 0, 0),
                    (0, COLUMN_DIAMETER, 0),
                    (0, 0, 22.5)
                )
            ))
        )
        + [rss.BooleanDifference(
            rss.AddCylinder((0, 0, PLANE_HEIGHT), BEAM_HEIGHT, 39),
            rss.AddCylinder((0, 0, PLANE_HEIGHT), BEAM_HEIGHT, 35.5)
        )]
    )

    if REMOVE_DRAFT:
        rss.DeleteObject(beam_path)


# Part 4: Layer 4
PLANE_HEIGHT = 102.5

if BUILD_TARGET == 'all' or 'layer4' in BUILD_TARGET:
    layer4 = rss.CopyObject(layer1, (0, 0, 40))

    if ADD_JUNCTION:
        base = rss.BooleanUnion(base + quad_rotate_object(
            rss.AddCylinder((CORE_RADIUS, 0, PLANE_HEIGHT), 3, 0.8)
        ))


# Part 5: Layer 5
PLANE_HEIGHT = 115

BEAM_LENGTH = 70
BEAM_HALF_LENGTH = BEAM_LENGTH / 2

if BUILD_TARGET == 'all' or 'layer5' in BUILD_TARGET:
    beam_origin = (BEAM_HALF_LENGTH, CORE_RADIUS + 3, PLANE_HEIGHT)
    beam_path = rss.AddPolyline((
        beam_origin,
        rss.PointAdd(beam_origin, (0, 0, 8)),
        rss.PointAdd(beam_origin, (-5, 0, BEAM_HEIGHT)),
        rss.PointAdd(beam_origin, (-BEAM_LENGTH + 5, 0, BEAM_HEIGHT)),
        rss.PointAdd(beam_origin, (-BEAM_LENGTH, 0, 8)),
        rss.PointAdd(beam_origin, (-BEAM_LENGTH, 0, 0)),
        beam_origin
    ))
    column_origin = (CORE_RADIUS, CORE_RADIUS, PLANE_HEIGHT - 7.5)
    column_path = rss.AddPolyline((
        column_origin,
        rss.PointAdd(column_origin, (COLUMN_DIAMETER, 0, 0)),
        rss.PointAdd(column_origin, (COLUMN_DIAMETER, 0, 22.5)),
        rss.PointAdd(column_origin, (0, 0, 20)),
        column_origin
    ))
    layer5 = rss.BooleanUnion(
        quad_rotate_object(
            extrude_crv_along_line(
                beam_path,
                beam_origin,
                (0, BEAM_WIDTH, 0)
            ))
        + quad_mirror_object(
            extrude_crv_along_line(
                column_path,
                column_origin,
                (0, COLUMN_DIAMETER, 0)
            ))
    )

    if REMOVE_DRAFT:
        rss.DeleteObjects((beam_path, column_path))
