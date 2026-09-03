#!/usr/bin/env python3
"""Audite chaque facette de l'essai fonctionnel F40 sans ouvrir de gate.

L'audit reutilise le rayon VTK fail-closed F39 et publie une carte locale. Une
corde normale de facette n'est pas une epaisseur mediale continue et ne remplace
ni le B-Rep fonctionnel, ni un CT de premiere piece.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import platform

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import pyvista as pv


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def load_f39_audit() -> object:
    path = Path(__file__).with_name("f39-lpbf-scan-only-audit.py")
    spec = importlib.util.spec_from_file_location("f39_lpbf_scan_only_audit", path)
    require(spec is not None and spec.loader is not None, "audit_F39_introuvable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def system_font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


def render(poly: object, thickness: np.ndarray, output: Path) -> None:
    body = pv.wrap(poly)
    require(body.n_cells == len(thickness), "cellules_VTK_et_carte_incoherentes")
    display = np.nan_to_num(thickness, nan=0.0, posinf=6.0, neginf=0.0)
    display = np.clip(display, 0.0, 6.0)
    body.cell_data["corde_mm"] = display
    thin = body.extract_cells(np.where((np.isfinite(thickness)) & (thickness < 1.5))[0])

    plotter = pv.Plotter(shape=(1, 2), off_screen=True, window_size=(2200, 900), border=False)
    for index in range(2):
        plotter.subplot(0, index)
        plotter.set_background("#10212c")
    plotter.subplot(0, 0)
    plotter.add_mesh(
        body,
        scalars="corde_mm",
        cmap="RdYlGn",
        clim=(0.0, 6.0),
        show_edges=False,
        scalar_bar_args={"title": "Corde normale [mm si echelle 1:1]", "color": "white"},
    )
    plotter.view_isometric()
    plotter.camera.zoom(1.12)
    plotter.add_text("Carte exhaustive des cordes", font_size=13, color="white", position="upper_edge")
    plotter.subplot(0, 1)
    plotter.add_mesh(body, color="#806d51", opacity=0.20, smooth_shading=True)
    plotter.add_mesh(thin, color="#ff4d4d", opacity=1.0, show_edges=False)
    plotter.view_isometric()
    plotter.camera.zoom(1.12)
    plotter.add_text("Zones < 1,5 mm en rouge", font_size=13, color="white", position="upper_edge")
    rendered = plotter.screenshot(return_img=True)
    plotter.close()

    panel = Image.fromarray(rendered)
    canvas = Image.new("RGB", (panel.width, panel.height + 165), "#07121a")
    canvas.paste(panel, (0, 105))
    draw = ImageDraw.Draw(canvas)
    draw.text(
        (canvas.width / 2, 38),
        "F40 — écran d'épaisseur sur le vrai maillage fonctionnel",
        anchor="mm",
        fill="white",
        font=system_font(38, bold=True),
    )
    draw.text(
        (canvas.width / 2, 77),
        "CORDES DE FACETTES VTK · PAS UNE PREUVE D'ÉPAISSEUR CONTINUE · CT NON RÉALISÉ",
        anchor="mm",
        fill="#f4c161",
        font=system_font(17, bold=True),
    )
    draw.text(
        (canvas.width / 2, canvas.height - 23),
        "ÉCHEC DE LA CIBLE 1,5 mm : RECONSTRUIRE LA BAIE ET LES SURFACES FONCTIONNELLES AVANT LPBF",
        anchor="mm",
        fill="#f0aaa3",
        font=system_font(18, bold=True),
    )
    canvas.save(output)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--head", type=Path, required=True)
    parser.add_argument("--functional-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--minimum-wall", type=float, default=1.5)
    args = parser.parse_args()
    require(args.minimum_wall > 0.0, "epaisseur_minimale_non_positive")
    args.output.mkdir(parents=True, exist_ok=True)
    functional = json.loads(args.functional_report.read_text(encoding="utf-8"))
    require(functional["geometry"]["watertight"], "essai_fonctionnel_non_etanche")
    require(functional["release_gates"]["metal_print_authorized"] is False, "gate_impression_doit_rester_fermee")

    audit = load_f39_audit()
    poly, points, faces = audit.load_stl(args.head)
    mesh_topology = audit.topology(poly)
    require(mesh_topology["watertight_manifold_screen"], "maillage_non_manifold")
    triangles, centroids, normals, areas, signed_volume = audit.triangle_geometry(points, faces)
    bounds = np.column_stack((points.min(axis=0), points.max(axis=0)))
    diagonal = float(np.linalg.norm(bounds[:, 1] - bounds[:, 0]))
    thickness = audit.exhaustive_normal_chords(poly, centroids, normals, diagonal)
    summary = audit.thickness_summary(thickness, areas, args.minimum_wall)
    summary["domain"] = "all_triangles_of_exact_F40_functional_trial_mesh"
    thin = np.isfinite(thickness) & (thickness > 0.0) & (thickness < args.minimum_wall)
    z_bands = []
    for lower in range(0, 85, 5):
        selected = thin & (centroids[:, 2] >= lower) & (centroids[:, 2] < lower + 5)
        z_bands.append(
            {
                "z_range_obj_units": [lower, lower + 5],
                "thin_triangle_count": int(np.count_nonzero(selected)),
                "thin_area_obj_units2": float(np.sum(areas[selected])),
            }
        )
    map_path = args.output / "917-head-935-scan-locked-thickness-map-f40.local.npz"
    np.savez_compressed(
        map_path,
        triangle_id=np.arange(len(faces), dtype=np.int32),
        centroid_obj_units=centroids.astype(np.float32),
        area_obj_units2=areas.astype(np.float32),
        normal=normals.astype(np.float32),
        thickness_chord_obj_units=thickness.astype(np.float32),
    )
    image_path = args.output / "917-head-935-scan-locked-thickness-screen-f40.png"
    render(poly, thickness, image_path)
    report = {
        "schema_version": "1.0.0",
        "phase": "F40",
        "status": "exhaustive_faceted_thickness_screen_failed_release_blocked",
        "classification": "faceted_normal_chord_screen_not_continuous_medial_thickness_or_CT",
        "inputs": {
            "head": {"path": str(args.head), "sha256": sha256(args.head)},
            "functional_report": {"path": str(args.functional_report), "sha256": sha256(args.functional_report)},
        },
        "toolchain": {"python": platform.python_version(), "vtk": audit.vtk.vtkVersion.GetVTKVersion()},
        "mesh": {**mesh_topology, "signed_volume_obj_units3": signed_volume, "bounds_obj_units": bounds.tolist()},
        "thickness": summary,
        "thin_z_bands": z_bands,
        "files": {
            "map_local": {"path": map_path.name, "sha256": sha256(map_path), "bytes": map_path.stat().st_size},
            "image": {"path": image_path.name, "sha256": sha256(image_path), "bytes": image_path.stat().st_size},
        },
        "gates": {
            "all_triangles_evaluated": summary["unresolved_triangle_count"] == 0,
            "all_resolved_chords_at_least_1_5_mm": summary["all_resolved_chords_meet_inherited_requirement"],
            "continuous_wall_thickness_verified": False,
            "ct_verified": False,
            "metal_print_authorized": False,
            "engine_start_authorized": False,
        },
        "required_correction": "reconstruct_valvetrain_bay_and_functional_surfaces_as_smooth_BRep_then_offset_inward_to_at_least_1_5_mm_and_repeat",
    }
    report_path = args.output / "917-head-935-scan-locked-thickness-screen-f40.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "thickness": summary, "image": str(image_path)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
