#!/usr/bin/env python3
"""Recoupe l'echelle du scan 935 sans la transformer en cote certifiee.

Le calcul compare seulement des interfaces identifiables : hauteur depuis le
plan de deck, diametre du raccord d'admission et diametre du raccord
d'echappement. Le nuage/maillage derive reste local et hors Git.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import statistics

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


EXPECTED_SCAN_SHA256 = "4623d5d3b73fe3d03ca988a47543a8dd1be7834d3040e6f7efd1e1e95c766486"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def local_transform(interfaces: dict) -> np.ndarray:
    frame = np.asarray(interfaces["frame_rows_A_B_C"], dtype=float)
    chamber = interfaces["combustion_interface"]["chamber_step"]
    transform = np.eye(4)
    transform[:3, :3] = np.diag([1.0, 1.0, -1.0]) @ frame
    transform[:3, 3] = np.asarray(
        [-float(chamber["center"][0]), -float(chamber["center"][1]), float(chamber["plane_C"])]
    )
    return transform


def selected_port_sections(interfaces: dict) -> tuple[list[float], list[float]]:
    """Retourne les sections quasi cylindriques, hors zones de transition."""

    high = [float(item["diameter_obj_units"]) for item in interfaces["port_sections"]["high_B"][:4]]
    low = [float(item["diameter_obj_units"]) for item in interfaces["port_sections"]["low_B"][1:3]]
    return high, low


def build_report(contract: dict, interfaces: dict, local_bounds: np.ndarray) -> dict:
    race = contract["documentary_constraints"]["retro_sport_935_race_head"]
    high, low = selected_port_sections(interfaces)
    intake_scales = [float(race["external_intake_port_diameter_mm"]) / value for value in high]
    exhaust_scales = [float(race["external_exhaust_port_diameter_mm"]) / value for value in low]
    scan_height = float(local_bounds[1, 2])
    height_min = float(race["head_height_mm"]["minimum"])
    height_max = float(race["head_height_mm"]["maximum"])
    height_mid = 0.5 * (height_min + height_max)
    port_median = float(statistics.median(intake_scales + exhaust_scales))
    height_scale = height_mid / scan_height
    spread = abs(height_scale - port_median) / port_median
    return {
        "schema_version": "1.0.0",
        "phase": "F40",
        "status": "millimetre_scale_plausible_but_source_identity_and_metrology_unclosed",
        "scan": {
            "sha256": EXPECTED_SCAN_SHA256,
            "local_bounds_obj_units": {
                "minimum": [float(value) for value in local_bounds[0]],
                "maximum": [float(value) for value in local_bounds[1]],
            },
            "height_above_deck_obj_units": scan_height,
        },
        "documentary_values": {
            "source_id": race["source_id"],
            "head_height_mm": {"minimum": height_min, "maximum": height_max},
            "intake_port_mm": float(race["external_intake_port_diameter_mm"]),
            "exhaust_port_mm": float(race["external_exhaust_port_diameter_mm"]),
        },
        "scale_candidates_mm_per_obj_unit": {
            "intake": intake_scales,
            "exhaust": exhaust_scales,
            "height_midpoint": height_scale,
            "ports_median": port_median,
            "height_vs_ports_relative_spread": spread,
        },
        "decision": {
            "working_unit_convention": "1_OBJ_unit_equals_1_mm",
            "geometry_rescaled": False,
            "reason": "three observable feature families cluster close to one, but the advertised race heads and the purchased scan do not have a shared custody identity",
            "global_scale_certified": False,
            "porsche_917_fitment_certified": False,
        },
    }


def render(mesh: trimesh.Trimesh, report: dict, output: Path) -> None:
    points = np.asarray(mesh.vertices, dtype=float)
    if len(points) > 55_000:
        selection = np.linspace(0, len(points) - 1, 55_000, dtype=int)
        points = points[selection]
    scales = report["scale_candidates_mm_per_obj_unit"]
    values = scales["intake"] + scales["exhaust"] + [scales["height_midpoint"]]
    labels = ["Adm"] * len(scales["intake"]) + ["Ech"] * len(scales["exhaust"]) + ["H"]
    colours = ["#55b8e6"] * len(scales["intake"]) + ["#ef8158"] * len(scales["exhaust"]) + ["#f6d365"]

    figure = plt.figure(figsize=(15, 8.5), facecolor="#09131b")
    figure.suptitle("F40 — verrouillage de la forme 935 et audit d'échelle", color="white", fontsize=21, fontweight="bold")
    figure.text(
        0.5,
        0.925,
        "SCAN CONSERVE · AUCUNE ELLIPSE GLOBALE · DIMENSIONS WEB UTILISEES COMME CONTROLES CROISES",
        ha="center",
        color="#f6c85f",
        fontsize=10,
        fontweight="bold",
    )

    for index, (elevation, azimuth, title) in enumerate(((22, -52, "Morphologie extérieure"), (15, 132, "Ailettes et bossages locaux"))):
        axis = figure.add_subplot(1, 3, index + 1, projection="3d", facecolor="#101f2a")
        axis.scatter(points[:, 0], points[:, 1], points[:, 2], s=0.15, c="#c99a4b", alpha=0.72, depthshade=False)
        centre = mesh.bounds.mean(axis=0)
        radius = 0.58 * float(np.ptp(mesh.bounds, axis=0).max())
        axis.set_xlim(centre[0] - radius, centre[0] + radius)
        axis.set_ylim(centre[1] - radius, centre[1] + radius)
        axis.set_zlim(centre[2] - 0.42 * radius, centre[2] + 0.58 * radius)
        axis.view_init(elev=elevation, azim=azimuth)
        axis.set_box_aspect((1.0, 1.35, 0.72))
        axis.set_axis_off()
        axis.set_title(title, color="white", fontsize=12, fontweight="bold")

    axis = figure.add_subplot(1, 3, 3, facecolor="#101f2a")
    positions = np.arange(len(values))
    axis.scatter(positions, values, c=colours, s=80, edgecolor="white", linewidth=0.7, zorder=3)
    axis.axhline(1.0, color="white", linestyle="--", linewidth=1.1, alpha=0.75)
    axis.set_xticks(positions, labels)
    axis.set_ylim(0.975, 1.008)
    axis.grid(axis="y", color="#546570", alpha=0.35)
    axis.tick_params(colors="#d9e2e8")
    for spine in axis.spines.values():
        spine.set_color("#546570")
    axis.set_ylabel("mm par unité OBJ", color="#d9e2e8")
    axis.set_title("Candidats d'échelle indépendants", color="white", fontsize=12, fontweight="bold")
    axis.text(
        0.5,
        0.06,
        f"médiane raccords {scales['ports_median']:.5f}\nhauteur {scales['height_midpoint']:.5f}\nécart relatif {100.0 * scales['height_vs_ports_relative_spread']:.2f}%",
        transform=axis.transAxes,
        ha="center",
        color="#d9e2e8",
        fontsize=10,
    )
    figure.text(
        0.5,
        0.025,
        "Conclusion : l'unité millimétrique est plausible; aucune remise à l'échelle globale ni compatibilité 917 n'est certifiée.",
        ha="center",
        color="#f3a6a6",
        fontsize=11,
        fontweight="bold",
    )
    figure.subplots_adjust(left=0.015, right=0.985, bottom=0.08, top=0.89, wspace=0.08)
    figure.savefig(output, dpi=180, facecolor=figure.get_facecolor())
    plt.close(figure)


def main() -> int:
    import trimesh

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scan", type=Path, required=True)
    parser.add_argument("--envelope", type=Path, required=True)
    parser.add_argument("--interfaces", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if sha256(args.scan) != EXPECTED_SCAN_SHA256:
        raise SystemExit("empreinte du scan 935 inattendue")
    interfaces = json.loads(args.interfaces.read_text(encoding="utf-8"))
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    if contract.get("phase") != "F40":
        raise SystemExit("le contrat doit etre F40")
    mesh = trimesh.load_mesh(args.envelope, process=False)
    if not isinstance(mesh, trimesh.Trimesh):
        raise SystemExit("l'enveloppe du scan n'est pas un maillage unique")
    mesh.apply_transform(local_transform(interfaces))
    report = build_report(contract, interfaces, np.asarray(mesh.bounds, dtype=float))
    args.output.mkdir(parents=True, exist_ok=True)
    report_path = args.output / "935-scan-scale-audit-f40.json"
    image_path = args.output / "935-scan-scale-audit-f40.png"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    render(mesh, report, image_path)
    print(json.dumps({"report": str(report_path), "image": str(image_path), "decision": report["decision"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
