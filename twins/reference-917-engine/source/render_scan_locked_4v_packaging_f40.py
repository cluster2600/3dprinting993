#!/usr/bin/env python3
"""Rend le paquet 4V F38 dans le B-Rep exterieur F40 verrouille sur le scan.

Cette vue est une preuve de positionnement et de provenance geometrique. Elle
ne remplace ni les booleens des conduits, ni un controle de jeu, ni une CAO de
fabrication liberee.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgb
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np
import trimesh

from build_scan_locked_outer_brep_f40 import tessellate_step


COMPONENTS = (
    ("rocker-carrier-f38-rounded-reinforced.step", "porte-axes", "#d7993f", 1.0),
    ("two-rocker-shafts-f38.step", "axes", "#78d5ff", 1.0),
    ("four-rockers-f38.step", "culbuteurs", "#ef5d4d", 1.0),
    ("two-intake-valves-f38.step", "soupapes admission", "#37c9ff", 1.0),
    ("two-exhaust-valves-f38.step", "soupapes echappement", "#ff6d51", 1.0),
    ("four-valve-guides-f38.step", "guides", "#d9e2e5", 0.88),
    ("four-valve-seats-f38.step", "sieges", "#f4c15f", 1.0),
    ("eight-valve-springs-f38.step", "doubles ressorts", "#a5ed69", 0.92),
    ("four-lower-spring-cups-f38.step", "coupelles inferieures", "#ddc988", 1.0),
    ("four-upper-spring-retainers-f38.step", "coupelles superieures", "#f4e4ac", 1.0),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_component(path: Path) -> trimesh.Trimesh:
    mesh = tessellate_step(path, linear_deflection=0.9, angular_deflection=0.28)
    if not mesh.is_watertight:
        raise RuntimeError(f"composant_STEP_non_etanche:{path.name}")
    return mesh


def triangles(
    mesh: trimesh.Trimesh,
    maximum_faces: int,
    half_x: bool,
    minimum_mean_z: float | None,
) -> tuple[np.ndarray, np.ndarray]:
    faces = mesh.faces
    normals = mesh.face_normals
    if minimum_mean_z is not None:
        selected = np.mean(mesh.vertices[faces][:, :, 2], axis=1) >= minimum_mean_z
        faces = faces[selected]
        normals = normals[selected]
    if half_x:
        selected = np.mean(mesh.vertices[faces][:, :, 0], axis=1) <= 0.0
        faces = faces[selected]
        normals = normals[selected]
    if len(faces) > maximum_faces:
        choice = np.linspace(0, len(faces) - 1, maximum_faces, dtype=int)
        faces = faces[choice]
        normals = normals[choice]
    return mesh.vertices[faces], normals


def add_mesh(
    axis: object,
    mesh: trimesh.Trimesh,
    colour: str,
    alpha: float,
    *,
    maximum_faces: int,
    half_x: bool = False,
    minimum_mean_z: float | None = None,
) -> None:
    surface, normals = triangles(mesh, maximum_faces, half_x, minimum_mean_z)
    light = np.asarray([0.35, -0.45, 0.82], dtype=float)
    light /= np.linalg.norm(light)
    intensity = np.clip(0.45 + 0.55 * np.maximum(normals @ light, 0.0), 0.40, 1.0)
    base = np.asarray(to_rgb(colour), dtype=float)
    colours = np.column_stack((intensity[:, None] * base[None, :], np.full(len(intensity), alpha)))
    axis.add_collection3d(Poly3DCollection(surface, facecolors=colours, edgecolor="none"))


def frame(axis: object, elevation: float, azimuth: float, title: str) -> None:
    axis.set_xlim(-70.0, 70.0)
    axis.set_ylim(-102.0, 128.0)
    axis.set_zlim(-12.0, 124.0)
    axis.set_box_aspect((140.0, 230.0, 136.0))
    axis.view_init(elev=elevation, azim=azimuth)
    axis.set_axis_off()
    axis.set_title(title, color="white", fontsize=12, fontweight="bold", pad=8)


def flow_containment_screen(outer: trimesh.Trimesh, flow: trimesh.Trimesh) -> dict:
    points, _ = trimesh.sample.sample_surface(flow, 12_000, seed=942)
    # Exclut la primitive de chambre F36 et les raccords ouverts : cette porte
    # ne porte que sur les branches Y enfouies dans le corps de culasse.
    selected = points[
        (points[:, 2] > 15.0)
        & (points[:, 2] < 60.0)
        & (points[:, 1] > -75.0)
        & (points[:, 1] < 100.0)
    ]
    inside = outer.contains(selected)
    _, distances, _ = trimesh.proximity.closest_point(outer, selected)
    minimum = float(np.min(distances))
    return {
        "method": "sampled_F36_Y_core_points_inside_F40_outer_BRep_and_nearest_external_surface_distance",
        "selection": "15<z<60,-75<y<100; chamber_primitive_and_open_flange_regions_excluded",
        "sample_count": len(selected),
        "inside_count": int(np.sum(inside)),
        "inside_fraction": float(np.mean(inside)),
        "minimum_distance_obj_units": minimum,
        "p01_distance_obj_units": float(np.quantile(distances, 0.01)),
        "p05_distance_obj_units": float(np.quantile(distances, 0.05)),
        "median_distance_obj_units": float(np.median(distances)),
        "screen_minimum_obj_units": 4.0,
        "screen_passed": bool(np.all(inside) and minimum >= 4.0),
        "classification": "external_clearance_screen_not_true_wall_thickness_or_CT",
    }


def render(
    outer: trimesh.Trimesh,
    flow: trimesh.Trimesh,
    components: list[tuple[str, str, str, float, trimesh.Trimesh]],
    flow_screen: dict,
    output: Path,
) -> None:
    figure = plt.figure(figsize=(16, 9), facecolor="#07121a")
    figure.suptitle(
        "Culasse 917 F40 — intégration 4 soupapes dans l'enveloppe du scan 935",
        color="white",
        fontsize=20,
        fontweight="bold",
    )
    figure.text(
        0.5,
        0.935,
        "FORME EXTÉRIEURE CONSERVÉE · 1 RACCORD PAR FAMILLE · BIFURCATIONS Y INTERNES · DOUBLE ALLUMAGE À RECONSTRUIRE",
        ha="center",
        color="#f4c161",
        fontsize=9.5,
        fontweight="bold",
    )

    axis = figure.add_subplot(1, 3, 1, projection="3d", facecolor="#10212c")
    add_mesh(axis, outer, "#c79243", 0.34, maximum_faces=150_000)
    for _, _, colour, alpha, mesh in components:
        add_mesh(axis, mesh, colour, alpha, maximum_faces=28_000)
    frame(axis, 24.0, -55.0, "Enveloppe scan + distribution 4V")

    axis = figure.add_subplot(1, 3, 2, projection="3d", facecolor="#10212c")
    add_mesh(axis, outer, "#c79243", 0.50, maximum_faces=150_000, half_x=True)
    # Le noyau F36 contient aussi une grande sphere de construction de chambre.
    # Elle est exclue ici : F40 doit reconstruire sa chambre a partir du scan et
    # de la fermeture de cotes, pas heriter de cette primitive provisoire.
    add_mesh(
        axis,
        flow,
        "#9966cc",
        0.34,
        maximum_faces=35_000,
        half_x=True,
        minimum_mean_z=15.0,
    )
    for _, _, colour, alpha, mesh in components:
        add_mesh(axis, mesh, colour, min(alpha, 0.96), maximum_faces=28_000, half_x=True)
    frame(axis, 20.0, -28.0, "Demi-coupe X ≤ 0 — Y internes provisoires")

    axis = figure.add_subplot(1, 3, 3, projection="3d", facecolor="#10212c")
    add_mesh(axis, outer, "#c79243", 0.30, maximum_faces=150_000)
    for name, _, colour, alpha, mesh in components:
        if name in {
            "two-intake-valves-f38.step",
            "two-exhaust-valves-f38.step",
            "four-valve-guides-f38.step",
            "four-valve-seats-f38.step",
        }:
            add_mesh(axis, mesh, colour, alpha, maximum_faces=16_000)
    frame(axis, -64.0, -90.0, "Face de combustion — 2 admission + 2 échappement")

    figure.text(
        0.5,
        0.035,
        f"Y UTILES : {100.0 * flow_screen['inside_fraction']:.1f} % DANS L'ENVELOPPE · DISTANCE EXTERNE MINI {flow_screen['minimum_distance_obj_units']:.2f} UNITÉS — PAS UNE ÉPAISSEUR CT NI UNE LIBÉRATION",
        ha="center",
        color="#f0aaa3",
        fontsize=9.5,
        fontweight="bold",
    )
    figure.subplots_adjust(left=0.015, right=0.985, bottom=0.075, top=0.90, wspace=0.02)
    figure.savefig(output, dpi=180, facecolor=figure.get_facecolor())
    plt.close(figure)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outer", type=Path, required=True)
    parser.add_argument("--flow-core", type=Path, required=True)
    parser.add_argument("--cad", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    outer = trimesh.load_mesh(args.outer, process=True)
    flow = trimesh.load_mesh(args.flow_core, process=True)
    if not isinstance(outer, trimesh.Trimesh) or not outer.is_watertight:
        raise RuntimeError("enveloppe_F40_non_etanche")
    if not isinstance(flow, trimesh.Trimesh) or not len(flow.faces):
        raise RuntimeError("noyau_fluide_F36_absent")

    components = []
    for filename, role, colour, alpha in COMPONENTS:
        path = args.cad / filename
        if not path.is_file():
            raise RuntimeError(f"composant_absent:{filename}")
        components.append((filename, role, colour, alpha, load_component(path)))

    image_path = args.output / "917-head-935-scan-locked-4v-packaging-f40.png"
    flow_screen = flow_containment_screen(outer, flow)
    render(outer, flow, components, flow_screen, image_path)
    report = {
        "schema_version": "1.0.0",
        "phase": "F40",
        "status": "scan_locked_outer_and_four_valve_packaging_visualized_release_blocked",
        "classification": "visual_packaging_evidence_not_collision_clearance_or_manufacturing_release",
        "outer": {"path": str(args.outer), "sha256": sha256(args.outer), "watertight": True},
        "flow_core": {
            "path": str(args.flow_core),
            "sha256": sha256(args.flow_core),
            "classification": "F36_provisional_four_valve_flow_core_not_final_functional_BRep",
        },
        "flow_containment_screen": flow_screen,
        "components": [
            {
                "path": str(args.cad / filename),
                "sha256": sha256(args.cad / filename),
                "role": role,
                "watertight_surface_tessellation": mesh.is_watertight,
            }
            for filename, role, _, _, mesh in components
        ],
        "image": {"path": image_path.name, "sha256": sha256(image_path), "bytes": image_path.stat().st_size},
        "release_gates": {
            "exact_functional_booleans_complete": False,
            "continuous_wall_thickness_verified": False,
            "kinematic_clearance_verified": False,
            "lubrication_complete": False,
            "metal_print_authorized": False,
            "engine_start_authorized": False,
        },
    }
    report_path = args.output / "917-head-935-scan-locked-4v-packaging-f40-report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "components": len(components), "image": str(image_path)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
