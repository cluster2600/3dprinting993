#!/usr/bin/env python3
"""Construit un B-Rep exterieur F40 par contours locaux du scan 935.

Contrairement au proxy F39, aucun rectangle ou noyau elliptique global n'est
utilise. Le corps est lofté entre les profils de creux et chaque ailette est
extrudee depuis son propre profil de pic mesure sur le stock Poisson F36.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

import gmsh
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgb
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np
import trimesh


PHASE = "F40"
CORE_LEVELS = [0.0, 3.0, 8.25, 14.25, 19.5, 24.75, 30.5, 35.75, 41.25, 47.25, 52.5, 58.5, 63.75, 70.25, 75.75, 82.0]
FIN_LEVELS = [6.0, 11.25, 16.5, 22.25, 27.75, 33.0, 39.0, 44.25, 49.5, 55.5, 60.25, 67.5, 73.25, 78.75]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def signed_area(points: np.ndarray) -> float:
    xy = np.asarray(points, dtype=float)[:, :2]
    return 0.5 * float(np.dot(xy[:, 0], np.roll(xy[:, 1], -1)) - np.dot(xy[:, 1], np.roll(xy[:, 0], -1)))


def largest_section_loop(mesh: trimesh.Trimesh, z: float) -> np.ndarray:
    section = mesh.section(plane_origin=np.asarray([0.0, 0.0, z]), plane_normal=np.asarray([0.0, 0.0, 1.0]))
    require(section is not None, f"section_absente_z_{z}")
    loops = []
    for raw in section.discrete:
        points = np.asarray(raw, dtype=float)
        if len(points) > 2 and np.linalg.norm(points[0] - points[-1]) < 1.0e-6:
            points = points[:-1]
        if len(points) >= 8:
            loops.append(points)
    require(bool(loops), f"boucle_fermee_absente_z_{z}")
    selected = max(loops, key=lambda value: abs(signed_area(value)))
    if signed_area(selected) < 0.0:
        selected = selected[::-1]
    return selected


def resample_closed(points: np.ndarray, count: int, smoothing_passes: int = 8) -> np.ndarray:
    xy = np.asarray(points, dtype=float)[:, :2].copy()
    for _ in range(smoothing_passes):
        xy = 0.15 * np.roll(xy, 1, axis=0) + 0.70 * xy + 0.15 * np.roll(xy, -1, axis=0)
    closed = np.vstack((xy, xy[0]))
    lengths = np.linalg.norm(np.diff(closed, axis=0), axis=1)
    cumulative = np.concatenate(([0.0], np.cumsum(lengths)))
    require(cumulative[-1] > 0.0, "contour_degenere")
    targets = np.linspace(0.0, cumulative[-1], count, endpoint=False)
    output = np.column_stack(
        (
            np.interp(targets, cumulative, closed[:, 0]),
            np.interp(targets, cumulative, closed[:, 1]),
        )
    )
    # Meme origine parametrique sur tous les profils : point le plus proche du
    # coin +x/-y, plus stable qu'un angle autour d'un centre concave.
    score = output[:, 0] - 0.25 * output[:, 1]
    output = np.roll(output, -int(np.argmax(score)), axis=0)
    return output


def contour_wire(occ: object, points_xy: np.ndarray, z: float) -> int:
    tags = [occ.addPoint(float(x), float(y), float(z)) for x, y in points_xy]
    curve = occ.addBSpline(tags + [tags[0]], degree=3)
    return occ.addWire([curve], checkClosed=True)


def profile_sequence(mesh: trimesh.Trimesh, contour_points: int, fin_thickness: float) -> list[tuple[float, np.ndarray, str]]:
    profiles = [(z, resample_closed(largest_section_loop(mesh, z), contour_points), "core") for z in CORE_LEVELS]
    for z in FIN_LEVELS:
        points = resample_closed(largest_section_loop(mesh, z), contour_points)
        profiles.append((z - 0.5 * fin_thickness, points, "fin_lower"))
        profiles.append((z + 0.5 * fin_thickness, points, "fin_upper"))
    profiles.sort(key=lambda item: item[0])
    return profiles


def canonicalize_step(path: Path) -> None:
    payload = path.read_text(encoding="utf-8")
    payload, count = re.subn(
        r"(FILE_NAME\([^,]+,')[^']+(')",
        r"\g<1>1970-01-01T00:00:00\g<2>",
        payload,
        count=1,
    )
    require(count == 1, "horodatage_STEP_absent")
    path.write_text(payload, encoding="utf-8", newline="\n")


def build_occ(mesh: trimesh.Trimesh, contour_points: int, fin_thickness: float) -> tuple[list[tuple[int, int]], dict]:
    occ = gmsh.model.occ
    profiles = profile_sequence(mesh, contour_points, fin_thickness)
    fin_areas: list[float] = []
    for z in FIN_LEVELS:
        points = resample_closed(largest_section_loop(mesh, z), contour_points)
        fin_areas.append(abs(signed_area(points)))
    wires = [contour_wire(occ, points, z) for z, points, _ in profiles]
    # Un seul loft monobloc reproduit les expansions locales des ailettes. Cela
    # évite les unions booléennes coûteuses entre quatorze volumes complexes et
    # conserve une correspondance explicite avec chaque coupe du scan.
    solid = occ.addThruSections(wires, makeSolid=True, makeRuled=True)
    require(any(dim == 3 for dim, _ in solid), "loft_corps_sans_volume")
    occ.synchronize()
    volumes = gmsh.model.getEntities(3)
    require(len(volumes) == 1 and bool(solid), f"BRep_exterieur_non_monobloc:{len(volumes)}")
    profile_report = {
        "core_levels_obj_units": CORE_LEVELS,
        "fin_levels_obj_units": FIN_LEVELS,
        "contour_points_per_level": contour_points,
        "fin_thickness_obj_units_from_scan_section_screen": fin_thickness,
        "fin_profile_areas_obj_units2": fin_areas,
        "loft_profile_count": len(profiles),
        "global_ellipse_used": False,
        "global_box_used": False,
    }
    return solid, profile_report


def profile_surface_mesh(mesh: trimesh.Trimesh, contour_points: int, fin_thickness: float) -> trimesh.Trimesh:
    """Tessellation directe des memes profils, pour preuve visuelle rapide."""

    from shapely.geometry import Polygon

    profiles = profile_sequence(mesh, contour_points, fin_thickness)
    rings = [np.column_stack((points, np.full(len(points), z))) for z, points, _ in profiles]
    vertices = np.vstack(rings)
    faces: list[list[int]] = []
    count = contour_points
    for level in range(len(rings) - 1):
        lower = level * count
        upper = (level + 1) * count
        for index in range(count):
            nxt = (index + 1) % count
            faces.append([lower + index, lower + nxt, upper + nxt])
            faces.append([lower + index, upper + nxt, upper + index])

    cap_vertices: list[np.ndarray] = []
    cap_faces: list[np.ndarray] = []
    for z, points, reverse in ((profiles[0][0], profiles[0][1], True), (profiles[-1][0], profiles[-1][1], False)):
        planar_vertices, planar_faces = trimesh.creation.triangulate_polygon(Polygon(points))
        offset = len(vertices) + sum(len(value) for value in cap_vertices)
        cap_vertices.append(np.column_stack((planar_vertices, np.full(len(planar_vertices), z))))
        oriented = planar_faces[:, ::-1] if reverse else planar_faces
        cap_faces.append(oriented + offset)
    vertices = np.vstack([vertices] + cap_vertices)
    all_faces = np.vstack([np.asarray(faces, dtype=np.int64)] + cap_faces)
    result = trimesh.Trimesh(vertices=vertices, faces=all_faces, process=True, validate=True)
    result.merge_vertices()
    result.remove_unreferenced_vertices()
    if result.volume < 0.0:
        result.invert()
    require(result.is_watertight and result.is_winding_consistent, "tessellation_profils_non_etanche")
    return result


def tessellate_step(step_path: Path, linear_deflection: float = 0.8, angular_deflection: float = 0.25) -> trimesh.Trimesh:
    """Tesselle le STEP avec OpenCASCADE, sans remaillage géométrique Gmsh."""

    from OCP.BRep import BRep_Tool
    from OCP.BRepMesh import BRepMesh_IncrementalMesh
    from OCP.IFSelect import IFSelect_RetDone
    from OCP.STEPControl import STEPControl_Reader
    from OCP.TopAbs import TopAbs_FACE, TopAbs_REVERSED
    from OCP.TopExp import TopExp_Explorer
    from OCP.TopLoc import TopLoc_Location
    from OCP.TopoDS import TopoDS

    reader = STEPControl_Reader()
    require(reader.ReadFile(str(step_path)) == IFSelect_RetDone, "lecture_STEP_OCCT_echouee")
    reader.TransferRoots()
    shape = reader.OneShape()
    mesher = BRepMesh_IncrementalMesh(shape, linear_deflection, False, angular_deflection, True)
    mesher.Perform()
    require(mesher.IsDone(), "tessellation_STEP_OCCT_echouee")
    vertices: list[list[float]] = []
    faces: list[list[int]] = []
    explorer = TopExp_Explorer(shape, TopAbs_FACE)
    while explorer.More():
        face = TopoDS.Face_s(explorer.Current())
        location = TopLoc_Location()
        triangulation = BRep_Tool.Triangulation_s(face, location)
        if triangulation is not None:
            offset = len(vertices)
            transform = location.Transformation()
            for index in range(1, triangulation.NbNodes() + 1):
                point = triangulation.Node(index).Transformed(transform)
                vertices.append([point.X(), point.Y(), point.Z()])
            reversed_face = face.Orientation() == TopAbs_REVERSED
            for index in range(1, triangulation.NbTriangles() + 1):
                a, b, c = triangulation.Triangle(index).Get()
                triangle = [offset + a - 1, offset + b - 1, offset + c - 1]
                faces.append(triangle[::-1] if reversed_face else triangle)
        explorer.Next()
    result = trimesh.Trimesh(vertices=np.asarray(vertices), faces=np.asarray(faces), process=True, validate=True)
    result.merge_vertices()
    result.remove_unreferenced_vertices()
    require(result.is_watertight and result.is_winding_consistent, "tessellation_STEP_non_etanche")
    if result.volume < 0.0:
        result.invert()
    return result


def configure_mesh(mesh_size: float) -> None:
    gmsh.option.setNumber("Mesh.MeshSizeMin", 0.45 * mesh_size)
    gmsh.option.setNumber("Mesh.MeshSizeMax", mesh_size)
    gmsh.option.setNumber("Mesh.Algorithm", 6)
    gmsh.option.setNumber("Mesh.Algorithm3D", 1)
    gmsh.option.setNumber("Mesh.Optimize", 1)


def point_to_closed_polyline(points: np.ndarray, polyline: np.ndarray) -> np.ndarray:
    points_xy = np.asarray(points, dtype=float)[:, :2]
    start = np.asarray(polyline, dtype=float)
    end = np.roll(start, -1, axis=0)
    segment = end - start
    denominator = np.sum(segment * segment, axis=1)
    batches: list[np.ndarray] = []
    for offset in range(0, len(points_xy), 1000):
        query = points_xy[offset : offset + 1000, None, :]
        fraction = np.sum((query - start[None, :, :]) * segment[None, :, :], axis=2) / denominator[None, :]
        fraction = np.clip(fraction, 0.0, 1.0)
        projection = start[None, :, :] + fraction[:, :, None] * segment[None, :, :]
        batches.append(np.min(np.linalg.norm(query - projection, axis=2), axis=1))
    return np.concatenate(batches)


def scan_deviation(
    reference: trimesh.Trimesh,
    candidate: trimesh.Trimesh,
    contour_points: int,
) -> dict:
    points, _ = trimesh.sample.sample_surface(reference, 100_000, seed=940)
    # Le B-Rep courant est volontairement l'exterieur a ailettes seulement. La
    # baie supérieure, le deck et les alésages sont des surfaces fonctionnelles
    # encore à reconstruire; les mélanger à cette métrique serait trompeur.
    selected = points[
        (points[:, 2] >= 0.0)
        & (points[:, 2] <= 82.0)
        & ((np.abs(points[:, 0]) >= 50.0) | (points[:, 1] <= -60.0) | (points[:, 1] >= 60.0))
    ]
    _, distances, _ = trimesh.proximity.closest_point(candidate, selected)
    distances = np.asarray(distances, dtype=float)
    require(bool(np.all(np.isfinite(distances))), "ecarts_scan_non_finis")
    contour_distances = []
    for z in CORE_LEVELS + FIN_LEVELS:
        raw = largest_section_loop(reference, z)
        fitted = resample_closed(raw, contour_points)
        contour_distances.append(point_to_closed_polyline(raw, fitted))
    section_values = np.concatenate(contour_distances)
    return {
        "method": "one_way_sampled_external_side_skin_reference_stock_to_F40_outer_BRep_surface",
        "selection_rule": "0<=z<=82 and (abs(x)>=50 or y<=-60 or y>=60); deck_top_bay_and_internal_functional_surfaces_excluded",
        "sample_count_total": len(points),
        "sample_count_selected": len(distances),
        "mean_obj_units": float(np.mean(distances)),
        "median_obj_units": float(np.median(distances)),
        "p95_obj_units": float(np.quantile(distances, 0.95)),
        "p99_obj_units": float(np.quantile(distances, 0.99)),
        "maximum_obj_units": float(np.max(distances)),
        "threshold_p95_obj_units": 2.0,
        "screen_passed": bool(np.quantile(distances, 0.95) <= 2.0),
        "section_contours": {
            "method": "raw_largest_section_loop_to_resampled_closed_BSpline_control_polyline",
            "level_count": len(CORE_LEVELS) + len(FIN_LEVELS),
            "sample_count": len(section_values),
            "mean_obj_units": float(np.mean(section_values)),
            "median_obj_units": float(np.median(section_values)),
            "p95_obj_units": float(np.quantile(section_values, 0.95)),
            "p99_obj_units": float(np.quantile(section_values, 0.99)),
            "maximum_obj_units": float(np.max(section_values)),
            "threshold_p95_obj_units": 1.5,
            "screen_passed": bool(np.quantile(section_values, 0.95) <= 1.5),
        },
        "metrology_certification": False,
    }


def add_mesh(axis, mesh: trimesh.Trimesh, colour: str, alpha: float = 1.0, maximum_faces: int = 500_000) -> None:
    faces = mesh.faces
    normals = mesh.face_normals
    if len(faces) > maximum_faces:
        selection = np.linspace(0, len(faces) - 1, maximum_faces, dtype=int)
        faces = faces[selection]
        normals = normals[selection]
    light = np.asarray([0.25, -0.45, 0.86], dtype=float)
    light /= np.linalg.norm(light)
    intensity = np.clip(0.45 + 0.55 * np.maximum(normals @ light, 0.0), 0.42, 1.0)
    base = np.asarray(to_rgb(colour), dtype=float)
    colours = np.column_stack((intensity[:, None] * base[None, :], np.full(len(intensity), alpha)))
    axis.add_collection3d(Poly3DCollection(mesh.vertices[faces], facecolors=colours, edgecolor="none"))


def set_view(axis, mesh: trimesh.Trimesh, elevation: float, azimuth: float, title: str) -> None:
    centre = mesh.bounds.mean(axis=0)
    radius = 0.58 * float(np.ptp(mesh.bounds, axis=0).max())
    axis.set_xlim(centre[0] - radius, centre[0] + radius)
    axis.set_ylim(centre[1] - radius, centre[1] + radius)
    axis.set_zlim(centre[2] - 0.42 * radius, centre[2] + 0.58 * radius)
    axis.set_box_aspect((1.0, 1.35, 0.72))
    axis.view_init(elev=elevation, azim=azimuth)
    axis.set_axis_off()
    axis.set_title(title, color="white", fontsize=12, fontweight="bold")


def render_preview(reference: trimesh.Trimesh, candidate: trimesh.Trimesh, report: dict, output: Path) -> None:
    figure = plt.figure(figsize=(16, 9), facecolor="#07121a")
    figure.suptitle("Culasse 917 F40 — B-Rep extérieur verrouillé sur le scan 935", color="white", fontsize=21, fontweight="bold")
    figure.text(
        0.5,
        0.935,
        "14 AILETTES ISSUES DE LEURS PROPRES COUPES · STEP MONOBLOC · AUCUNE ELLIPSE GLOBALE",
        ha="center",
        color="#f5c562",
        fontsize=10.5,
        fontweight="bold",
    )
    views = ((22.0, -52.0, "Vue admission / deck"), (18.0, 132.0, "Vue échappement"))
    for index, (elevation, azimuth, title) in enumerate(views, start=1):
        axis = figure.add_subplot(1, 3, index, projection="3d", facecolor="#10212c")
        add_mesh(axis, candidate, "#c6903d")
        set_view(axis, candidate, elevation, azimuth, title)

    axis = figure.add_subplot(1, 3, 3, projection="3d", facecolor="#10212c")
    points = reference.vertices
    if len(points) > 30_000:
        points = points[np.linspace(0, len(points) - 1, 30_000, dtype=int)]
    axis.scatter(points[:, 0], points[:, 1], points[:, 2], s=0.12, color="#dce6eb", alpha=0.22, depthshade=False)
    add_mesh(axis, candidate, "#d39a42", alpha=0.78)
    set_view(axis, candidate, 13.0, -92.0, "Superposition au stock scan-conforme")
    deviation = report["scan_deviation"]
    figure.text(
        0.5,
        0.032,
        f"Peau latérale stock→B-Rep : médiane {deviation['median_obj_units']:.2f} · P95 {deviation['p95_obj_units']:.2f}; profils P95 {deviation['section_contours']['p95_obj_units']:.2f} unités OBJ — fonctions 4V non encore intégrées",
        ha="center",
        color="#f0b0a9",
        fontsize=10.5,
        fontweight="bold",
    )
    figure.subplots_adjust(left=0.015, right=0.985, bottom=0.075, top=0.90, wspace=0.02)
    figure.savefig(output, dpi=180, facecolor=figure.get_facecolor())
    plt.close(figure)


def build(
    stock_path: Path,
    contract_path: Path,
    output: Path,
    contour_points: int,
    fin_thickness: float,
    mesh_size: float,
    volume_mesh: bool,
) -> dict:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    require(contract.get("phase") == PHASE, "contrat_non_F40")
    stock = trimesh.load_mesh(stock_path, process=True)
    require(isinstance(stock, trimesh.Trimesh) and stock.is_watertight, "stock_F36_non_etanche")
    output.mkdir(parents=True, exist_ok=True)
    step_path = output / "917-head-935-scan-locked-outer-f40.step"
    stl_path = output / "917-head-935-scan-locked-outer-f40.local.stl"
    msh_path = output / "917-head-935-scan-locked-outer-f40.local.msh"

    gmsh.initialize()
    try:
        gmsh.option.setNumber("General.Terminal", 0)
        gmsh.option.setNumber("Geometry.Tolerance", 1.0e-6)
        gmsh.option.setNumber("Geometry.OCCFixSmallEdges", 1)
        gmsh.option.setNumber("Geometry.OCCFixSmallFaces", 1)
        gmsh.model.add("f40_scan_locked_outer")
        _, profiles = build_occ(stock, contour_points, fin_thickness)
        gmsh.write(str(step_path))
        canonicalize_step(step_path)

        gmsh.clear()
        gmsh.model.add("f40_scan_locked_outer_reimport")
        gmsh.model.occ.importShapes(str(step_path), highestDimOnly=True)
        gmsh.model.occ.synchronize()
        volumes = gmsh.model.getEntities(3)
        require(len(volumes) == 1, f"reimport_STEP_volumes:{len(volumes)}")
        tag = volumes[0][1]
        volume = float(gmsh.model.occ.getMass(3, tag))
        surface_area = float(sum(gmsh.model.occ.getMass(dim, entity) for dim, entity in gmsh.model.getEntities(2)))
        bounds = gmsh.model.getBoundingBox(3, tag)
        if volume_mesh:
            configure_mesh(mesh_size)
            gmsh.model.mesh.generate(3)
            gmsh.write(str(stl_path))
            gmsh.write(str(msh_path))
            surface_nodes = gmsh.model.mesh.getNodes()[0]
            surface_types, surface_tags, _ = gmsh.model.mesh.getElements(2)
            surface_elements = sum(len(tags) for tags in surface_tags)
            nodes = gmsh.model.mesh.getNodes()[0]
            element_types, element_tags, _ = gmsh.model.mesh.getElements(3)
            volume_elements = sum(len(tags) for tags in element_tags)
            all_tags = [int(value) for tags in element_tags for value in tags]
            quality = np.asarray(gmsh.model.mesh.getElementQualities(all_tags, "minSICN"), dtype=float)
        else:
            surface_nodes = np.asarray([], dtype=int)
            surface_types = []
            surface_elements = 0
            nodes = np.asarray([], dtype=int)
            element_types = []
            volume_elements = 0
            quality = np.asarray([], dtype=float)
    finally:
        gmsh.finalize()

    if volume_mesh:
        candidate = trimesh.load_mesh(stl_path, process=True)
        tessellation_method = "gmsh_volume_mesh_boundary"
    else:
        candidate = tessellate_step(step_path)
        candidate.export(stl_path)
        surface_nodes = np.arange(len(candidate.vertices), dtype=int)
        surface_types = [2]
        surface_elements = len(candidate.faces)
        tessellation_method = "OpenCASCADE_STEP_surface_tessellation"
    deviation = scan_deviation(stock, candidate, contour_points)
    report = {
        "schema_version": "1.0.0",
        "phase": PHASE,
        "status": (
            "scan_contour_locked_outer_BRep_built_STEP_reimported_and_volume_meshed"
            if volume_mesh
            else "scan_contour_locked_outer_BRep_built_STEP_reimported_surface_tessellated"
        ),
        "source": {"path": str(stock_path), "sha256": sha256(stock_path), "classification": "local_scan_derived_not_committed"},
        "profiles": profiles,
        "geometry": {
            "solid_count": 1,
            "bounds_obj_units": {"minimum": list(bounds[:3]), "maximum": list(bounds[3:])},
            "volume_obj_units3": volume,
            "surface_area_obj_units2": surface_area,
            "fin_count": len(FIN_LEVELS),
        },
        "surface_mesh": {
            "method": tessellation_method,
            "nodes": len(surface_nodes),
            "elements": surface_elements,
            "element_types": [int(value) for value in surface_types],
        },
        "volume_mesh": {
            "executed": volume_mesh,
            "nodes": len(nodes),
            "volume_elements": volume_elements,
            "element_types": [int(value) for value in element_types],
            "minimum_minSICN": float(np.min(quality)) if len(quality) else None,
            "p01_minSICN": float(np.quantile(quality, 0.01)) if len(quality) else None,
            "elements_minSICN_le_0": int(np.sum(quality <= 0.0)),
        },
        "scan_deviation": deviation,
        "files": {
            "step": {"path": step_path.name, "sha256": sha256(step_path), "bytes": step_path.stat().st_size},
            "surface_stl_local": {"path": stl_path.name, "sha256": sha256(stl_path), "bytes": stl_path.stat().st_size},
            "volume_mesh_local": (
                {"path": msh_path.name, "sha256": sha256(msh_path), "bytes": msh_path.stat().st_size}
                if volume_mesh
                else None
            ),
        },
        "release": {
            "outer_geometry_screen_passed": deviation["screen_passed"] and deviation["section_contours"]["screen_passed"],
            "functional_geometry_present": False,
            "metal_print_authorized": False,
            "engine_start_authorized": False,
        },
    }
    (output / "917-head-935-scan-locked-outer-f40-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    render_preview(stock, candidate, report, output / "917-head-935-scan-locked-outer-f40.png")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stock", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--contour-points", type=int, default=96)
    parser.add_argument("--fin-thickness", type=float, default=1.5)
    parser.add_argument("--mesh-size", type=float, default=3.0)
    parser.add_argument("--volume-mesh", action="store_true")
    args = parser.parse_args()
    require(args.contour_points >= 48, "contour_points_trop_faible")
    require(0.8 <= args.fin_thickness <= 2.5, "epaisseur_ailette_hors_ecran")
    report = build(
        args.stock,
        args.contract,
        args.output,
        args.contour_points,
        args.fin_thickness,
        args.mesh_size,
        args.volume_mesh,
    )
    print(json.dumps({"status": report["status"], "geometry": report["geometry"], "scan_deviation": report["scan_deviation"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
