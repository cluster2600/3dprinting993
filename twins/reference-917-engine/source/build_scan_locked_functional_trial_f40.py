#!/usr/bin/env python3
"""Construit un maillage fonctionnel d'essai F40 depuis le B-Rep exterieur.

Le resultat sert a verifier la topologie des ouvertures et le packaging. Le
maitre editable reste le STEP exterieur F40 et des volumes fonctionnels
analytiques separes; ce maillage triangule n'est pas une definition de
fabrication liberee.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgb
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import trimesh

try:
    import pyvista as pv
except ImportError:  # pragma: no cover - dependance de rendu optionnelle
    pv = None

from build_scan_conforming_4v_f36 import architecture, cylinder_between, valve_axis


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main_volume(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    parts = mesh.split(only_watertight=False)
    require(bool(parts), "maillage_sans_composant")
    result = max(parts, key=lambda item: len(item.faces))
    result.remove_unreferenced_vertices()
    require(result.is_volume, "composant_principal_non_volumique")
    return result


def valve_cutters(cfg: dict) -> tuple[list[trimesh.Trimesh], list[trimesh.Trimesh]]:
    cutters: list[trimesh.Trimesh] = []
    protected: list[trimesh.Trimesh] = []
    for family in ("intake", "exhaust"):
        data = cfg[family]
        for centre in data["centres_mm"]:
            start, end = valve_axis(centre, data["tilt_y_deg"], 92.0)
            direction = end - start
            direction /= np.linalg.norm(direction)
            cutters.append(
                cylinder_between(
                    start - 4.0 * direction,
                    end,
                    data["stem_diameter_mm"] / 2.0 + 0.35,
                    64,
                )
            )
            cutters.append(
                cylinder_between(
                    start + 4.0 * direction,
                    start + 64.0 * direction,
                    data["guide_bore_diameter_mm"] / 2.0,
                    64,
                )
            )
            cutters.append(
                cylinder_between(
                    start - 1.4 * direction,
                    start + 7.0 * direction,
                    data["seat_bore_diameter_mm"] / 2.0,
                    96,
                )
            )
            protected.append(
                cylinder_between(
                    start + 36.0 * direction,
                    start + 94.0 * direction,
                    11.5,
                    64,
                )
            )
    return cutters, protected


def plug_cutters(cfg: dict) -> tuple[list[trimesh.Trimesh], list[trimesh.Trimesh]]:
    cutters: list[trimesh.Trimesh] = []
    protected: list[trimesh.Trimesh] = []
    for centre in cfg["spark_plug"]["electrode_centres_mm"]:
        start = np.asarray(centre, dtype=float) - np.asarray([0.0, 0.0, 6.0])
        end = np.asarray([centre[0] + math.copysign(13.0, centre[0]), centre[1], 86.0])
        cutters.append(cylinder_between(start, end, cfg["spark_plug"]["pilot_diameter_mm"] / 2.0, 64))
        protected.append(cylinder_between(start + 35.0 * (end - start) / np.linalg.norm(end - start), end, 9.0, 64))
    return cutters, protected


def stud_cutters(interfaces: dict) -> tuple[list[trimesh.Trimesh], list[list[float]]]:
    chamber_centre = interfaces["combustion_interface"]["chamber_step"]["center"]
    cutters = []
    centres = []
    for item in interfaces["head_stud_holes_at_C_minus_91"]:
        x = float(item["center_A_B"][0]) - float(chamber_centre[0])
        y = float(item["center_A_B"][1]) - float(chamber_centre[1])
        radius = float(item["diameter_obj_units"]) / 2.0
        cutters.append(cylinder_between(np.asarray([x, y, -3.0]), np.asarray([x, y, 86.0]), radius, 64))
        centres.append([x, y])
    return cutters, centres


def bay_cutter(protected: list[trimesh.Trimesh]) -> trimesh.Trimesh:
    floor = 49.15
    top = 88.0
    bay = trimesh.creation.cylinder(radius=50.85, height=top - floor, sections=128)
    bay.apply_translation([0.0, 0.0, 0.5 * (floor + top)])
    protection = trimesh.boolean.union(protected, engine="manifold", check_volume=True)
    require(isinstance(protection, trimesh.Trimesh) and protection.is_volume, "protection_baie_invalide")
    result = trimesh.boolean.difference([bay, protection], engine="manifold", check_volume=True)
    require(isinstance(result, trimesh.Trimesh) and result.is_volume, "decoupe_baie_invalide")
    return result


def build(outer: trimesh.Trimesh, flow: trimesh.Trimesh, interfaces: dict) -> tuple[trimesh.Trimesh, dict]:
    cfg = architecture()
    valves, valve_protection = valve_cutters(cfg)
    plugs, plug_protection = plug_cutters(cfg)
    studs, stud_centres = stud_cutters(interfaces)
    bay = bay_cutter(valve_protection + plug_protection)
    functional_cutters = [main_volume(flow), bay] + valves + plugs + studs
    combined = trimesh.boolean.union(functional_cutters, engine="manifold", check_volume=True)
    require(isinstance(combined, trimesh.Trimesh) and combined.is_volume, "union_volumes_fonctionnels_invalide")
    result = trimesh.boolean.difference([outer, combined], engine="manifold", check_volume=True)
    require(isinstance(result, trimesh.Trimesh), "soustraction_fonctionnelle_sans_maillage")
    # Manifold renvoie deja une topologie soudee. Un second merge_vertices peut
    # fusionner a tort des levres tres proches de sieges ou de puits et detruire
    # la variete obtenue par la booleenne robuste.
    result.remove_unreferenced_vertices()
    require(result.is_volume and result.is_watertight and result.is_winding_consistent, "essai_fonctionnel_non_etanche")
    topology = {
        "outer_body_count": 1,
        "result_body_count": len(result.split(only_watertight=True)),
        "cutters": {
            "gas_and_chamber": 1,
            "valve_stem_guide_and_seat": len(valves),
            "spark_plug_pilots": len(plugs),
            "head_stud_passages": len(studs),
            "valvetrain_bay": 1,
        },
        "stud_centres_obj_units": stud_centres,
        "oil_galleries_included": False,
        "thread_forms_included": False,
    }
    return result, topology


def add_mesh(axis: object, mesh: trimesh.Trimesh, colour: str, alpha: float, *, half_x: bool = False) -> None:
    faces = mesh.faces
    normals = mesh.face_normals
    if half_x:
        selected = mesh.triangles_center[:, 0] <= 0.0
        faces = faces[selected]
        normals = normals[selected]
    if len(faces) > 220_000:
        choice = np.linspace(0, len(faces) - 1, 220_000, dtype=int)
        faces = faces[choice]
        normals = normals[choice]
    light = np.asarray([0.30, -0.50, 0.81], dtype=float)
    light /= np.linalg.norm(light)
    # La tessellation est volontairement dense. Un contraste fort face par face
    # transforme visuellement les triangles en faux reliefs; l'eclairage doux
    # conserve la lecture des ouvertures sans presenter le maillage comme un
    # etat de surface usine.
    intensity = np.clip(0.78 + 0.22 * np.maximum(normals @ light, 0.0), 0.76, 1.0)
    base = np.asarray(to_rgb(colour), dtype=float)
    colours = np.column_stack((intensity[:, None] * base[None, :], np.full(len(intensity), alpha)))
    axis.add_collection3d(Poly3DCollection(mesh.vertices[faces], facecolors=colours, edgecolor="none"))


def frame(axis: object, mesh: trimesh.Trimesh, elevation: float, azimuth: float, title: str) -> None:
    centre = mesh.bounds.mean(axis=0)
    radius = 0.58 * float(np.ptp(mesh.bounds, axis=0).max())
    axis.set_xlim(centre[0] - radius, centre[0] + radius)
    axis.set_ylim(centre[1] - radius, centre[1] + radius)
    axis.set_zlim(-14.0, 88.0)
    axis.set_box_aspect((1.0, 1.45, 0.72))
    axis.view_init(elev=elevation, azim=azimuth)
    axis.set_axis_off()
    axis.set_title(title, color="white", fontsize=12, fontweight="bold")


def render_matplotlib(result: trimesh.Trimesh, flow: trimesh.Trimesh, output: Path) -> None:
    figure = plt.figure(figsize=(16, 9), facecolor="#07121a")
    figure.suptitle("Culasse 917 F40 — maillage fonctionnel d'essai scan-conforme", color="white", fontsize=21, fontweight="bold")
    figure.text(
        0.5,
        0.935,
        "CHAMBRE + Y 4V + SIÈGES + GUIDES + 2 BOUGIES + 4 GOUJONS + BAIE · ENVELOPPE EXTÉRIEURE INCHANGÉE",
        ha="center",
        color="#f4c161",
        fontsize=9.5,
        fontweight="bold",
    )
    axis = figure.add_subplot(1, 3, 1, projection="3d", facecolor="#10212c")
    add_mesh(axis, result, "#c89242", 1.0)
    frame(axis, result, 22.0, -54.0, "Vue admission / deck")

    axis = figure.add_subplot(1, 3, 2, projection="3d", facecolor="#10212c")
    add_mesh(axis, result, "#c89242", 0.55, half_x=True)
    visible = flow.submesh(
        [np.where((flow.triangles_center[:, 2] >= 15.0) & (flow.triangles_center[:, 2] <= 62.0))[0]],
        append=True,
        repair=False,
    )
    add_mesh(axis, visible, "#8c63c7", 0.42, half_x=True)
    frame(axis, result, 16.0, -24.0, "Demi-coupe X ≤ 0")

    axis = figure.add_subplot(1, 3, 3, projection="3d", facecolor="#10212c")
    add_mesh(axis, result, "#c89242", 1.0)
    frame(axis, result, -70.0, -90.0, "Face de combustion / registre")
    figure.text(
        0.5,
        0.034,
        "VOLUME ÉTANCHE D'ESSAI — MAILLAGE TRIANGULÉ, GALERIES D'HUILE ET FILETAGES ABSENTS, IMPRESSION MÉTAL INTERDITE",
        ha="center",
        color="#f0aaa3",
        fontsize=9.5,
        fontweight="bold",
    )
    figure.subplots_adjust(left=0.015, right=0.985, bottom=0.075, top=0.90, wspace=0.02)
    figure.savefig(output, dpi=180, facecolor=figure.get_facecolor())
    plt.close(figure)


def pv_mesh(mesh: trimesh.Trimesh) -> object:
    require(pv is not None, "pyvista_absent")
    faces = np.column_stack((np.full(len(mesh.faces), 3, dtype=np.int64), mesh.faces)).ravel()
    return pv.PolyData(mesh.vertices, faces)


def font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


def render_pyvista(result: trimesh.Trimesh, flow: trimesh.Trimesh, output: Path) -> None:
    require(pv is not None, "pyvista_absent")
    body = pv_mesh(result)
    flow_body = pv_mesh(flow)
    plotter = pv.Plotter(shape=(1, 3), off_screen=True, window_size=(2400, 900), border=False)
    for index in range(3):
        plotter.subplot(0, index)
        plotter.set_background("#10212c")

    plotter.subplot(0, 0)
    plotter.add_mesh(body, color="#c89242", smooth_shading=True, pbr=True, metallic=0.10, roughness=0.55)
    plotter.view_isometric()
    plotter.camera.zoom(1.15)
    plotter.add_text("Vue admission / deck", font_size=13, color="white", position="upper_edge")

    plotter.subplot(0, 1)
    half = body.clip(normal=(1.0, 0.0, 0.0), origin=(0.0, 0.0, 0.0), invert=False)
    visible_flow = flow_body.clip(normal=(1.0, 0.0, 0.0), origin=(0.0, 0.0, 0.0), invert=False)
    visible_flow = visible_flow.clip(normal=(0.0, 0.0, 1.0), origin=(0.0, 0.0, 15.0), invert=False)
    visible_flow = visible_flow.clip(normal=(0.0, 0.0, -1.0), origin=(0.0, 0.0, 62.0), invert=False)
    plotter.add_mesh(half, color="#c89242", smooth_shading=True, opacity=0.72)
    plotter.add_mesh(visible_flow, color="#8c63c7", smooth_shading=True, opacity=0.50)
    plotter.view_xz()
    plotter.camera.azimuth = 18.0
    plotter.camera.elevation = 12.0
    plotter.add_text("Demi-coupe X = 0", font_size=13, color="white", position="upper_edge")

    plotter.subplot(0, 2)
    plotter.add_mesh(body, color="#c89242", smooth_shading=True, pbr=True, metallic=0.10, roughness=0.55)
    plotter.view_xy(negative=True)
    plotter.camera.zoom(0.95)
    plotter.add_text("Face de combustion / registre", font_size=13, color="white", position="upper_edge")

    rendered = plotter.screenshot(return_img=True)
    plotter.close()
    panel = Image.fromarray(rendered)
    canvas = Image.new("RGB", (panel.width, panel.height + 190), "#07121a")
    canvas.paste(panel, (0, 120))
    draw = ImageDraw.Draw(canvas)
    draw.text(
        (canvas.width / 2, 43),
        "Culasse 917 F40 — essai fonctionnel scan-conforme",
        anchor="mm",
        fill="white",
        font=font(44, bold=True),
    )
    draw.text(
        (canvas.width / 2, 87),
        "CHAMBRE + Y 4V + SIÈGES + GUIDES + 2 BOUGIES + 4 GOUJONS + BAIE · ENVELOPPE EXTÉRIEURE INCHANGÉE",
        anchor="mm",
        fill="#f4c161",
        font=font(18, bold=True),
    )
    draw.text(
        (canvas.width / 2, canvas.height - 28),
        "VOLUME ÉTANCHE D'ESSAI · GALERIES D'HUILE ET FILETAGES ABSENTS · IMPRESSION MÉTAL INTERDITE",
        anchor="mm",
        fill="#f0aaa3",
        font=font(18, bold=True),
    )
    canvas.save(output)


def render(result: trimesh.Trimesh, flow: trimesh.Trimesh, output: Path) -> str:
    if pv is not None:
        render_pyvista(result, flow, output)
        return "pyvista_vtk"
    render_matplotlib(result, flow, output)
    return "matplotlib_fallback"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outer", type=Path, required=True)
    parser.add_argument("--flow-core", type=Path, required=True)
    parser.add_argument("--interfaces", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    outer = trimesh.load_mesh(args.outer, process=True)
    flow = trimesh.load_mesh(args.flow_core, process=True)
    interfaces = json.loads(args.interfaces.read_text(encoding="utf-8"))
    require(isinstance(outer, trimesh.Trimesh) and outer.is_volume, "BRep_exterieur_tesselle_non_volumique")
    require(isinstance(flow, trimesh.Trimesh) and len(flow.faces) > 0, "noyau_fluide_absent")

    result, topology = build(outer, flow, interfaces)
    mesh_path = args.output / "917-head-935-scan-locked-functional-trial-f40.local.stl"
    image_path = args.output / "917-head-935-scan-locked-functional-trial-f40.png"
    result.export(mesh_path)
    renderer = render(result, main_volume(flow), image_path)
    density_g_mm3 = 2.73e-3
    report = {
        "schema_version": "1.0.0",
        "phase": "F40",
        "status": "scan_locked_functional_trial_mesh_complete_release_blocked",
        "classification": "triangulated_boolean_trial_not_editable_functional_BRep_or_manufacturing_master",
        "inputs": {
            "outer": {"path": str(args.outer), "sha256": sha256(args.outer)},
            "flow_core": {"path": str(args.flow_core), "sha256": sha256(args.flow_core)},
            "interfaces": {"path": str(args.interfaces), "sha256": sha256(args.interfaces)},
        },
        "topology": topology,
        "geometry": {
            "watertight": result.is_watertight,
            "winding_consistent": result.is_winding_consistent,
            "is_volume": result.is_volume,
            "vertices": len(result.vertices),
            "triangles": len(result.faces),
            "volume_obj_units3": float(result.volume),
            "mass_kg_if_obj_unit_is_mm_and_cp1_density_2_73_g_cm3": float(result.volume * density_g_mm3 / 1000.0),
            "bounds_obj_units": result.bounds.tolist(),
        },
        "files": {
            "mesh_local": {"path": mesh_path.name, "sha256": sha256(mesh_path), "bytes": mesh_path.stat().st_size},
            "image": {
                "path": image_path.name,
                "sha256": sha256(image_path),
                "bytes": image_path.stat().st_size,
                "renderer": renderer,
            },
        },
        "release_gates": {
            "editable_functional_BRep_complete": False,
            "continuous_wall_thickness_verified": False,
            "oil_galleries_and_drainage_complete": False,
            "thread_and_machining_definition_complete": False,
            "openfoam_cht_converged": False,
            "independent_cfd_converged": False,
            "thermomechanical_fatigue_passed": False,
            "lpbf_process_simulation_calibrated": False,
            "metal_print_authorized": False,
            "engine_start_authorized": False,
        },
    }
    report_path = args.output / "917-head-935-scan-locked-functional-trial-f40-report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "geometry": report["geometry"], "image": str(image_path)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
