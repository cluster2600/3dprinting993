#!/usr/bin/env python3
"""Contrôleur hors secret du cycle Vast F46.

Ce module valide uniquement des instantanés JSON produits par les wrappers
OpenBao approuvés. Il ne contacte ni Vast, ni GHCR et ne crée aucune instance.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_FLOOR
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import tempfile
from typing import Any


IMAGE_RE = re.compile(
    r"(?P<repository>[a-z0-9][a-z0-9._/-]*)@(?P<digest>sha256:[0-9a-f]{64})"
)
DIGEST_RE = re.compile(r"sha256:[0-9a-f]{64}")
HEX_RE = re.compile(r"[0-9a-f]{64}")
MAX_JSON_BYTES = 4 * 1024 * 1024
REQUIRED_FAMILIES = {"OpenFOAM", "ICEEngineFoam", "Cantera", "CHT", "FEA"}
REQUIRED_TOOL_KEYS = {
    "openfoam", "iceenginefoam", "cantera", "cht", "fea", "cuda", "job_runner"
}


class ContractError(RuntimeError):
    """Erreur fail-closed dont le texte ne contient aucune donnée secrète."""


def reject_constant(value: str) -> None:
    raise ValueError(f"constante JSON non finie interdite: {value}")


def load_json(path: Path) -> dict[str, Any]:
    try:
        info = path.lstat()
    except FileNotFoundError as exc:
        raise ContractError(f"JSON absent: {path}") from exc
    if not stat.S_ISREG(info.st_mode) or path.is_symlink() or not 0 < info.st_size <= MAX_JSON_BYTES:
        raise ContractError(f"JSON non régulier, vide ou trop volumineux: {path}")

    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"clé JSON dupliquée: {key}")
            result[key] = value
        return result

    try:
        payload = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=pairs,
            parse_constant=reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ContractError(f"JSON strict invalide: {path}") from exc
    if not isinstance(payload, dict):
        raise ContractError(f"racine JSON invalide: {path}")
    return payload


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".partial"
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def number(value: object, label: str, *, allow_zero: bool = False) -> Decimal:
    if isinstance(value, bool):
        raise ContractError(f"{label} invalide")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ContractError(f"{label} invalide") from exc
    if not result.is_finite() or result < 0 or (not allow_zero and result == 0):
        raise ContractError(f"{label} invalide")
    return result


def positive_integer(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ContractError(f"{label} doit être un entier positif")
    return value


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_contract(contract: dict[str, Any], manifest: dict[str, Any], root: Path) -> None:
    if contract.get("id") != "917-f46-vast-cfd-cae-controller":
        raise ContractError("identité du contrat F46 invalide")
    if contract.get("classification") != "execution_controller_contract_not_execution_evidence":
        raise ContractError("classification du contrat F46 invalide")
    authority = contract.get("authority_boundary")
    if not isinstance(authority, dict) or authority.get("contract_prepared") is not True:
        raise ContractError("frontière d'autorité F46 invalide")
    for key in (
        "offer_selected_live",
        "image_verified_live",
        "instance_created",
        "simulation_executed",
        "physical_validation",
        "manufacturing_release",
    ):
        if authority.get(key) is not False:
            raise ContractError(f"autorité prématurée: {key}")
    if number(authority.get("spend_incurred_usd"), "spend_incurred_usd", allow_zero=True) != 0:
        raise ContractError("le contrat préparatoire ne peut déclarer une dépense")

    budget = contract.get("budget")
    if not isinstance(budget, dict):
        raise ContractError("budget F46 absent")
    hard = number(budget.get("hard_total_usd"), "hard_total_usd")
    planned = number(budget.get("planned_compute_ceiling_usd"), "planned_compute_ceiling_usd")
    reserve = number(budget.get("cleanup_and_billing_reserve_usd"), "cleanup reserve")
    if hard != Decimal("23") or planned + reserve != hard or planned >= hard:
        raise ContractError("décomposition du plafond F46 incohérente")
    if number(budget.get("maximum_selected_dph_usd"), "maximum_selected_dph_usd") > Decimal("2.5"):
        raise ContractError("débit horaire supérieur au contrat")
    maximum_runtime = positive_integer(budget.get("maximum_runtime_seconds"), "maximum_runtime_seconds")
    cleanup_seconds = positive_integer(budget.get("cleanup_reserve_seconds"), "cleanup_reserve_seconds")
    if maximum_runtime > 28800 or cleanup_seconds < 900:
        raise ContractError("TTL ou réserve cleanup hors limites")

    image = contract.get("image_policy")
    if not isinstance(image, dict):
        raise ContractError("politique image F46 absente")
    expected_ref = image.get("expected_immutable_ref")
    evidence_path = image.get("committed_evidence_path")
    evidence_sha = image.get("committed_evidence_sha256")
    if expected_ref is None:
        if evidence_path is not None or evidence_sha is not None:
            raise ContractError("preuve image présente sans digest verrouillé")
    else:
        match = IMAGE_RE.fullmatch(str(expected_ref))
        if match is None or match.group("repository") != image.get("expected_repository"):
            raise ContractError("référence image F46 verrouillée invalide")
        if not isinstance(evidence_path, str) or not HEX_RE.fullmatch(str(evidence_sha or "")):
            raise ContractError("preuve image verrouillée absente")
        candidate = root / evidence_path
        if not candidate.is_file() or candidate.is_symlink() or sha256(candidate) != evidence_sha:
            raise ContractError("preuve image verrouillée absente ou différente")
    if image.get("required_os") != "linux" or image.get("required_architecture") != "amd64":
        raise ContractError("plateforme image F46 invalide")
    if set(image.get("required_tools", {})) != REQUIRED_TOOL_KEYS:
        raise ContractError("outillage image F46 incomplet")

    lifecycle = contract.get("lifecycle")
    required_cleanup_flags = (
        "destroy_on_normal_exit",
        "destroy_on_error",
        "destroy_on_signal",
        "destroy_on_deadline",
        "destroy_on_budget_gate",
        "destroy_on_image_or_instance_drift",
        "inventory_after_must_be_empty_for_label",
        "complete_paginated_inventory_required",
    )
    if not isinstance(lifecycle, dict) or any(lifecycle.get(key) is not True for key in required_cleanup_flags):
        raise ContractError("chemins de cleanup F46 incomplets")
    if lifecycle.get("local_and_remote_deadline_must_match") is not True:
        raise ContractError("les deadlines locale et distante doivent être identiques")

    release = contract.get("current_release_gates")
    if not isinstance(release, dict) or not release or any(value is not False for value in release.values()):
        raise ContractError("toutes les portes F46 courantes doivent rester fermées")

    if manifest.get("id") != "917-f46-vast-cfd-cae-job-manifest":
        raise ContractError("identité du manifeste de jobs invalide")
    if manifest.get("classification") != "planned_jobs_not_execution_evidence":
        raise ContractError("classification du manifeste de jobs invalide")
    global_policy = manifest.get("global_policy")
    if not isinstance(global_policy, dict) or global_policy.get("geometry_domains_complete") not in (True, False):
        raise ContractError("état des domaines géométriques invalide")
    jobs = manifest.get("jobs")
    if not isinstance(jobs, list) or len(jobs) != 5:
        raise ContractError("le manifeste doit contenir cinq familles de jobs")
    if {job.get("family") for job in jobs if isinstance(job, dict)} != REQUIRED_FAMILIES:
        raise ContractError("familles de jobs F46 incomplètes")
    identifiers: set[str] = set()
    total_timeout = 0
    total_cases = 0
    for job in jobs:
        if not isinstance(job, dict):
            raise ContractError("job F46 invalide")
        identifier = job.get("id")
        if not isinstance(identifier, str) or identifier in identifiers:
            raise ContractError("identifiant de job absent ou dupliqué")
        identifiers.add(identifier)
        ready = job.get("execution_ready")
        if ready not in (True, False):
            raise ContractError(f"état d'exécution invalide: {identifier}")
        blocked = job.get("blocked_by")
        if ready:
            command = job.get("command")
            if (
                not isinstance(command, list)
                or not command
                or any(not isinstance(item, str) or not item or "\0" in item for item in command)
                or not HEX_RE.fullmatch(str(job.get("input_manifest_sha256", "")))
                or blocked not in ([], None)
            ):
                raise ContractError(f"job exécutable non complètement lié: {identifier}")
        elif job.get("command") is not None or job.get("input_manifest_sha256") is not None:
            raise ContractError(f"job bloqué contenant une commande ou un digest: {identifier}")
        elif not isinstance(blocked, list) or not blocked:
            raise ContractError(f"blocages absents: {identifier}")
        total_timeout += positive_integer(job.get("timeout_seconds"), f"timeout {identifier}")
        total_cases += positive_integer(job.get("case_count"), f"case_count {identifier}")
    if total_timeout != positive_integer(global_policy.get("total_phase_timeout_seconds"), "total phase timeout"):
        raise ContractError("somme des timeouts de jobs incohérente")
    if total_timeout + positive_integer(global_policy.get("cleanup_reserve_seconds"), "manifest cleanup reserve") > maximum_runtime:
        raise ContractError("jobs et cleanup dépassent le TTL global")
    executable_cases = sum(job["case_count"] for job in jobs if job["execution_ready"])
    all_ready = all(job["execution_ready"] for job in jobs)
    if (
        total_cases != manifest.get("planned_case_count")
        or executable_cases != manifest.get("executable_case_count")
        or manifest.get("execution_authorized") is not all_ready
    ):
        raise ContractError("comptage des cas F46 incohérent")
    if global_policy.get("geometry_domains_complete") is not all_ready:
        raise ContractError("autorité géométrique incohérente avec la readiness globale")
    for key in ("simulation_validated", "manufacturing_release"):
        if manifest.get(key) is not False:
            raise ContractError(f"porte de manifeste prématurée: {key}")
    for source in manifest.get("source_contracts", []):
        if not isinstance(source, dict) or not HEX_RE.fullmatch(str(source.get("sha256", ""))):
            raise ContractError("source amont mal formée")
        relative = source.get("path")
        if not isinstance(relative, str) or relative.startswith("/") or ".." in Path(relative).parts:
            raise ContractError("chemin source amont interdit")
        path = root / relative
        if not path.is_file() or path.is_symlink() or sha256(path) != source["sha256"]:
            raise ContractError(f"source amont absente ou différente: {relative}")


def validate_evidence_classification(payload: dict[str, Any], allow_synthetic: bool) -> bool:
    classification = payload.get("classification")
    synthetic = classification == "synthetic_test_fixture"
    if synthetic and not allow_synthetic:
        raise ContractError("fixture synthétique interdite hors test explicite")
    if classification not in {"production_wrapper_evidence", "synthetic_test_fixture"}:
        raise ContractError("classification de preuve inconnue")
    return synthetic


def validate_image_proof(
    proof: dict[str, Any], contract: dict[str, Any], *, allow_synthetic: bool
) -> tuple[str, bool]:
    synthetic = validate_evidence_classification(proof, allow_synthetic)
    immutable = proof.get("immutable_ref")
    match = IMAGE_RE.fullmatch(str(immutable))
    if match is None:
        raise ContractError("référence image non immuable")
    policy = contract["image_policy"]
    if match.group("repository") != policy["expected_repository"]:
        raise ContractError("dépôt image différent du dépôt F46 autorisé")
    if proof.get("index_digest") != match.group("digest"):
        raise ContractError("digest index différent de la référence image")
    if not DIGEST_RE.fullmatch(str(proof.get("platform_manifest_digest", ""))):
        raise ContractError("digest du manifeste plateforme absent")
    if proof.get("os") != "linux" or proof.get("architecture") != "amd64":
        raise ContractError("image différente de linux/amd64")
    for gate in ("registry_digest_verified", "platform_manifest_verified", "runtime_smoke_verified"):
        if proof.get(gate) is not True:
            raise ContractError(f"preuve image manquante: {gate}")
    tools = proof.get("tools")
    if not isinstance(tools, dict) or set(tools) != REQUIRED_TOOL_KEYS:
        raise ContractError("inventaire des outils image incomplet")
    for name, result in tools.items():
        if not isinstance(result, dict) or result.get("passed") is not True:
            raise ContractError(f"smoke outil échoué: {name}")
        if not isinstance(result.get("version"), str) or not result["version"].strip():
            raise ContractError(f"version outil absente: {name}")
    return str(immutable), synthetic


def validate_inventory(
    snapshot: dict[str, Any], label: str, *, allow_synthetic: bool, must_be_empty: bool
) -> bool:
    synthetic = validate_evidence_classification(snapshot, allow_synthetic)
    if snapshot.get("pagination_complete") is not True or snapshot.get("label_filter") != label:
        raise ContractError("inventaire incomplet ou filtre différent")
    instances = snapshot.get("instances")
    if not isinstance(instances, list):
        raise ContractError("liste d'instances invalide")
    for instance in instances:
        if not isinstance(instance, dict) or instance.get("label") != label:
            raise ContractError("inventaire contient une entrée hors filtre")
    if must_be_empty and instances:
        raise ContractError("inventaire F46 non vide")
    return synthetic


def ledger_total(ledger: dict[str, Any], *, allow_synthetic: bool) -> tuple[Decimal, bool]:
    synthetic = validate_evidence_classification(ledger, allow_synthetic)
    entries = ledger.get("entries")
    if not isinstance(entries, list):
        raise ContractError("ledger de coûts invalide")
    seen: set[str] = set()
    total = Decimal("0")
    for entry in entries:
        if not isinstance(entry, dict):
            raise ContractError("entrée de ledger invalide")
        key = str(entry.get("charge_id", ""))
        if not key or key in seen:
            raise ContractError("charge_id absent ou dupliqué")
        seen.add(key)
        if entry.get("finalized") is not True:
            raise ContractError("charge antérieure non finalisée")
        total += number(entry.get("provider_charge_usd"), "provider_charge_usd", allow_zero=True)
    declared = number(ledger.get("cumulative_spend_usd"), "cumulative_spend_usd", allow_zero=True)
    if declared != total:
        raise ContractError("total du ledger différent de la somme des charges")
    return total, synthetic


def eligible_offer(offer: dict[str, Any], contract: dict[str, Any]) -> bool:
    policy = contract["offer_policy"]
    try:
        return (
            isinstance(offer.get("id"), int)
            and offer["id"] > 0
            and offer.get("gpu") in policy["allowed_gpu_models"]
            and number(offer.get("num_gpus"), "num_gpus") == policy["required_gpu_count"]
            and number(offer.get("gpu_fraction"), "gpu_fraction") == Decimal("1")
            and number(offer.get("gpu_ram_mb"), "gpu_ram_mb") >= number(policy["minimum_gpu_ram_mb"], "minimum_gpu_ram_mb")
            and number(offer.get("cpu_cores_effective"), "cpu cores") >= number(policy["minimum_cpu_cores_effective"], "minimum cpu cores")
            and number(offer.get("cpu_ram_mb"), "cpu ram") >= number(policy["minimum_cpu_ram_mb"], "minimum cpu ram")
            and number(offer.get("disk_space_gb"), "disk") >= number(policy["minimum_disk_space_gb"], "minimum disk")
            and number(offer.get("reliability"), "reliability") >= number(policy["minimum_reliability"], "minimum reliability")
            and number(offer.get("dph_total"), "dph_total", allow_zero=True) <= number(contract["budget"]["maximum_selected_dph_usd"], "maximum dph")
            and offer.get("verified") is True
            and offer.get("rentable") is True
            and offer.get("rented") is False
            and offer.get("rental_type") == "on-demand"
        )
    except ContractError:
        return False


def select_offer(
    snapshot: dict[str, Any], contract: dict[str, Any], now_epoch: int, *, allow_synthetic: bool
) -> tuple[dict[str, Any], bool]:
    synthetic = validate_evidence_classification(snapshot, allow_synthetic)
    if snapshot.get("pagination_complete") is not True:
        raise ContractError("instantané d'offres non paginé complètement")
    captured = positive_integer(snapshot.get("captured_at_epoch"), "captured_at_epoch")
    age = now_epoch - captured
    if age < 0 or age > contract["offer_policy"]["snapshot_max_age_seconds"]:
        raise ContractError("instantané d'offres périmé ou futur")
    offers = snapshot.get("offers")
    if not isinstance(offers, list):
        raise ContractError("liste d'offres invalide")
    candidates = [offer for offer in offers if isinstance(offer, dict) and eligible_offer(offer, contract)]
    if not candidates:
        raise ContractError("aucune offre F46 éligible")
    preference = {name: rank for rank, name in enumerate(contract["offer_policy"]["allowed_gpu_models"])}
    candidates.sort(
        key=lambda offer: (
            preference[offer["gpu"]],
            -float(offer["cpu_cores_effective"]),
            -float(offer["cpu_ram_mb"]),
            float(offer["dph_total"]),
            offer["id"],
        )
    )
    return candidates[0], synthetic


def build_plan(
    contract: dict[str, Any],
    manifest: dict[str, Any],
    offers: dict[str, Any],
    image_proof: dict[str, Any],
    inventory_before: dict[str, Any],
    ledger: dict[str, Any],
    *,
    now_epoch: int,
    operator_deadline_epoch: int,
    root: Path,
    allow_synthetic: bool = False,
) -> dict[str, Any]:
    validate_contract(contract, manifest, root)
    now_epoch = positive_integer(now_epoch, "now_epoch")
    operator_deadline_epoch = positive_integer(operator_deadline_epoch, "operator_deadline_epoch")
    immutable_ref, image_synthetic = validate_image_proof(
        image_proof, contract, allow_synthetic=allow_synthetic
    )
    image_policy = contract["image_policy"]
    digest_locked = image_policy.get("expected_immutable_ref") == immutable_ref
    if digest_locked:
        committed_proof = load_json(root / image_policy["committed_evidence_path"])
        if committed_proof != image_proof:
            raise ContractError("preuve image fournie différente de la preuve verrouillée")
    inventory_synthetic = validate_inventory(
        inventory_before,
        contract["lifecycle"]["label"],
        allow_synthetic=allow_synthetic,
        must_be_empty=True,
    )
    selected, offers_synthetic = select_offer(
        offers, contract, now_epoch, allow_synthetic=allow_synthetic
    )
    prior_spend, ledger_synthetic = ledger_total(ledger, allow_synthetic=allow_synthetic)
    budget = contract["budget"]
    planned_ceiling = number(budget["planned_compute_ceiling_usd"], "planned ceiling")
    remaining = planned_ceiling - prior_spend
    if remaining <= 0:
        raise ContractError("plafond calcul déjà consommé")
    dph = number(selected["dph_total"], "selected dph")
    budget_seconds = int(
        ((remaining / dph) * Decimal("3600")).to_integral_value(rounding=ROUND_FLOOR)
    )
    operator_seconds = operator_deadline_epoch - now_epoch
    runtime_seconds = min(budget_seconds, operator_seconds, budget["maximum_runtime_seconds"])
    cleanup_seconds = budget["cleanup_reserve_seconds"]
    if runtime_seconds < budget["minimum_useful_runtime_seconds"] + cleanup_seconds:
        raise ContractError("fenêtre restante insuffisante pour calcul utile et cleanup")
    hard_deadline = now_epoch + runtime_seconds
    compute_deadline = hard_deadline - cleanup_seconds
    projected = prior_spend + dph * Decimal(runtime_seconds) / Decimal("3600")
    if projected > planned_ceiling:
        raise ContractError("projection de coût supérieure au plafond calcul")

    synthetic = image_synthetic or inventory_synthetic or offers_synthetic or ledger_synthetic
    jobs_ready = all(job.get("execution_ready") is True for job in manifest["jobs"])
    commands_bound = all(
        isinstance(job.get("command"), list)
        and job["command"]
        and HEX_RE.fullmatch(str(job.get("input_manifest_sha256", "")))
        for job in manifest["jobs"]
    )
    launch_authorized = jobs_ready and commands_bound and digest_locked and not synthetic
    blockers: list[str] = []
    if synthetic:
        blockers.append("au moins une preuve est une fixture synthétique")
    if not jobs_ready:
        blockers.append("au moins un job F46 reste bloqué")
    if not commands_bound:
        blockers.append("commandes ou manifestes d'entrée non liés par digest")
    if not digest_locked:
        blockers.append("digest et preuve image F46 non verrouillés dans le contrat")
    return {
        "schema_version": "1.0.0",
        "classification": "synthetic_test_fixture" if synthetic else "production_controller_plan",
        "status": "launch_authorized" if launch_authorized else "blocked",
        "launch_authorized": launch_authorized,
        "selected_offer": selected,
        "expected_image": immutable_ref,
        "expected_label": contract["lifecycle"]["label"],
        "prior_cumulative_spend_usd": str(prior_spend),
        "selected_dph_total_usd": str(dph),
        "projected_cumulative_spend_usd": str(projected.quantize(Decimal("0.000001"))),
        "hard_total_budget_usd": str(number(budget["hard_total_usd"], "hard total")),
        "planned_compute_ceiling_usd": str(planned_ceiling),
        "local_deadline_epoch": hard_deadline,
        "remote_deadline_epoch": hard_deadline,
        "compute_stop_epoch": compute_deadline,
        "cleanup_reserve_seconds": cleanup_seconds,
        "job_manifest_id": manifest["id"],
        "job_ids": [job["id"] for job in manifest["jobs"]],
        "planned_case_count": manifest["planned_case_count"],
        "blockers": blockers,
        "created_at": datetime.fromtimestamp(now_epoch, timezone.utc).isoformat(),
        "release_gates": {key: False for key in contract["current_release_gates"]},
    }


def cost_check(
    contract: dict[str, Any],
    plan: dict[str, Any],
    ledger: dict[str, Any],
    instance: dict[str, Any],
    *,
    now_epoch: int,
    allow_synthetic: bool = False,
) -> dict[str, Any]:
    synthetic = validate_evidence_classification(instance, allow_synthetic)
    prior, ledger_synthetic = ledger_total(ledger, allow_synthetic=allow_synthetic)
    now_epoch = positive_integer(now_epoch, "now_epoch")
    if instance.get("id") != plan.get("selected_instance_id"):
        raise ContractError("instance courante différente du plan")
    if instance.get("label") != plan.get("expected_label") or instance.get("image") != plan.get("expected_image"):
        raise ContractError("label ou image de l'instance a dérivé")
    selected = plan.get("selected_offer", {})
    if instance.get("gpu") != selected.get("gpu"):
        raise ContractError("GPU de l'instance différent de l'offre")
    exact_fields = (
        ("num_gpus", "num_gpus"),
        ("gpu_fraction", "gpu_fraction"),
        ("gpu_ram_mb", "gpu_ram_mb"),
        ("cpu_cores_effective", "cpu_cores_effective"),
        ("cpu_ram_mb", "cpu_ram_mb"),
        ("disk_space_gb", "disk_space_gb"),
    )
    for instance_key, offer_key in exact_fields:
        if number(instance.get(instance_key), instance_key) != number(selected.get(offer_key), offer_key):
            raise ContractError(f"champ instance différent de l'offre: {instance_key}")
    if instance.get("machine_verification") != "verified" or instance.get("status") != "running":
        raise ContractError("instance non vérifiée ou non active")
    dph = number(instance.get("dph_total"), "instance dph")
    if dph != number(plan.get("selected_dph_total_usd"), "plan dph"):
        raise ContractError("coût horaire de l'instance a dérivé")
    start = positive_integer(instance.get("started_at_epoch"), "started_at_epoch")
    if now_epoch < start:
        raise ContractError("horodatage de coût antérieur au démarrage")
    elapsed_charge = Decimal(now_epoch - start) * dph / Decimal("3600")
    provider_charge = number(instance.get("provider_charge_usd"), "provider charge", allow_zero=True)
    current_charge = max(elapsed_charge, provider_charge)
    cumulative = prior + current_charge
    planned_cap = number(contract["budget"]["planned_compute_ceiling_usd"], "planned cap")
    hard_cap = number(contract["budget"]["hard_total_usd"], "hard cap")
    compute_deadline = positive_integer(plan.get("compute_stop_epoch"), "compute_stop_epoch")
    hard_deadline = positive_integer(plan.get("local_deadline_epoch"), "local_deadline_epoch")
    contract_ok = dph <= number(contract["budget"]["maximum_selected_dph_usd"], "max dph")
    continue_compute = (
        contract_ok
        and cumulative < planned_cap
        and now_epoch < compute_deadline
        and plan.get("launch_authorized") is True
        and not synthetic
        and not ledger_synthetic
    )
    cleanup_required = not continue_compute
    hard_budget_exceeded = cumulative >= hard_cap
    return {
        "schema_version": "1.0.0",
        "classification": "synthetic_test_fixture" if synthetic or ledger_synthetic else "production_cost_evidence",
        "status": "continue" if continue_compute else "cleanup_required",
        "continue_compute": continue_compute,
        "cleanup_required": cleanup_required,
        "current_conservative_charge_usd": str(current_charge.quantize(Decimal("0.000001"))),
        "cumulative_conservative_spend_usd": str(cumulative.quantize(Decimal("0.000001"))),
        "planned_compute_ceiling_usd": str(planned_cap),
        "hard_total_budget_usd": str(hard_cap),
        "hard_budget_exceeded": hard_budget_exceeded,
        "compute_deadline_reached": now_epoch >= compute_deadline,
        "hard_deadline_reached": now_epoch >= hard_deadline,
        "checked_at": datetime.fromtimestamp(now_epoch, timezone.utc).isoformat(),
    }


def finalize(
    contract: dict[str, Any],
    plan: dict[str, Any],
    jobs_state: dict[str, Any],
    ledger: dict[str, Any],
    destroy_report: dict[str, Any],
    inventory_after: dict[str, Any],
    *,
    allow_synthetic: bool = False,
) -> dict[str, Any]:
    synthetic_flags = [
        validate_evidence_classification(jobs_state, allow_synthetic),
        validate_evidence_classification(destroy_report, allow_synthetic),
        validate_inventory(
            inventory_after,
            contract["lifecycle"]["label"],
            allow_synthetic=allow_synthetic,
            must_be_empty=True,
        ),
    ]
    total, ledger_synthetic = ledger_total(ledger, allow_synthetic=allow_synthetic)
    synthetic = any(synthetic_flags) or ledger_synthetic
    if destroy_report.get("destroyed") is not True or destroy_report.get("verified_absent") is not True:
        raise ContractError("destruction non vérifiée")
    if destroy_report.get("instance_id") != plan.get("selected_instance_id"):
        raise ContractError("rapport de destruction pour une autre instance")
    states = jobs_state.get("jobs")
    if not isinstance(states, list):
        raise ContractError("état des jobs invalide")
    expected_ids = set(plan.get("job_ids", []))
    actual_ids = {item.get("id") for item in states if isinstance(item, dict)}
    if not expected_ids or actual_ids != expected_ids:
        raise ContractError("état des jobs incomplet")
    terminal = {"passed", "failed", "blocked", "cancelled"}
    if any(not isinstance(item, dict) or item.get("status") not in terminal for item in states):
        raise ContractError("job non terminal au cleanup")
    hard = number(contract["budget"]["hard_total_usd"], "hard total")
    return {
        "schema_version": "1.0.0",
        "classification": "synthetic_test_fixture" if synthetic else "production_cleanup_evidence",
        "status": "cleanup_verified" if total <= hard else "cleanup_verified_budget_exceeded",
        "cleanup_verified": True,
        "empty_final_inventory_verified": True,
        "cumulative_spend_usd": str(total),
        "hard_total_budget_usd": str(hard),
        "budget_respected": total <= hard,
        "jobs_all_passed": bool(states) and all(item["status"] == "passed" for item in states),
        "simulation_validated": False,
        "metal_print_authorized": False,
        "engine_start_authorized": False,
    }


def preparation_report(contract: dict[str, Any], manifest: dict[str, Any], root: Path) -> dict[str, Any]:
    validate_contract(contract, manifest, root)
    artifact_paths = (
        "twins/reference-917-engine/f46-vast-cfd-cae-controller.json",
        "twins/reference-917-engine/f46-vast-job-manifest.json",
        "deploy/vast/f46/_f46_controller.py",
        "deploy/vast/f46/run-controller.sh",
        "deploy/vast/simready/_controller_common.sh",
        "deploy/vast/simready/destroy-instance.sh",
        "deploy/openbao/openbao-vastai",
        "deploy/openbao/openbao-ghcr",
        "docs/917_F46_VAST_CFD_CAE_CONTROLLER.md",
    )
    artifacts = []
    for relative in artifact_paths:
        path = root / relative
        if not path.is_file() or path.is_symlink():
            raise ContractError(f"artefact contrôleur absent: {relative}")
        artifacts.append({"path": relative, "sha256": sha256(path), "bytes": path.stat().st_size})
    return {
        "schema_version": "1.0.0",
        "id": "917-f46-vast-cfd-cae-controller-preparation",
        "classification": "offline_preparation_evidence_not_live_vast_evidence",
        "status": "controller_prepared_launch_blocked",
        "spend_incurred_by_this_preparation_usd": 0.0,
        "vast_api_called_by_preparation": False,
        "ghcr_api_called_by_preparation": False,
        "live_offer_selected": False,
        "live_image_verified": False,
        "live_inventory_before_verified_empty": False,
        "instance_created": False,
        "planned_case_count": manifest["planned_case_count"],
        "executable_case_count": manifest["executable_case_count"],
        "hard_total_budget_usd": contract["budget"]["hard_total_usd"],
        "planned_compute_ceiling_usd": contract["budget"]["planned_compute_ceiling_usd"],
        "cleanup_and_billing_reserve_usd": contract["budget"]["cleanup_and_billing_reserve_usd"],
        "current_blockers": [
            "F46 linux/amd64 image digest and committed smoke evidence absent",
            "live eligible offer snapshot absent",
            "live complete empty pre-launch inventory absent",
            "2V/4V solver domains and qualified hot material card incomplete",
            "all five job commands and input-manifest digests absent",
        ],
        "artifacts": artifacts,
        "release_gates": {key: False for key in contract["current_release_gates"]},
    }


def cli() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--jobs", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--allow-synthetic-fixture", action="store_true")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("check")
    report_parser = subparsers.add_parser("preparation-report")
    report_group = report_parser.add_mutually_exclusive_group(required=True)
    report_group.add_argument("--output", type=Path)
    report_group.add_argument("--check-report", type=Path)
    plan_parser = subparsers.add_parser("plan")
    plan_parser.add_argument("--offers", type=Path, required=True)
    plan_parser.add_argument("--image-proof", type=Path, required=True)
    plan_parser.add_argument("--inventory-before", type=Path, required=True)
    plan_parser.add_argument("--ledger", type=Path, required=True)
    plan_parser.add_argument("--now-epoch", type=int, required=True)
    plan_parser.add_argument("--operator-deadline-epoch", type=int, required=True)
    plan_parser.add_argument("--output", type=Path, required=True)
    cost_parser = subparsers.add_parser("cost-check")
    cost_parser.add_argument("--plan", type=Path, required=True)
    cost_parser.add_argument("--ledger", type=Path, required=True)
    cost_parser.add_argument("--instance", type=Path, required=True)
    cost_parser.add_argument("--now-epoch", type=int, required=True)
    cost_parser.add_argument("--output", type=Path, required=True)
    final_parser = subparsers.add_parser("finalize")
    final_parser.add_argument("--plan", type=Path, required=True)
    final_parser.add_argument("--jobs-state", type=Path, required=True)
    final_parser.add_argument("--ledger", type=Path, required=True)
    final_parser.add_argument("--destroy-report", type=Path, required=True)
    final_parser.add_argument("--inventory-after", type=Path, required=True)
    final_parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    contract = load_json(args.contract)
    jobs = load_json(args.jobs)
    try:
        validate_contract(contract, jobs, args.root.resolve())
        if args.command == "check":
            print("F46 Vast controller contract OK; live launch gates remain closed")
            return 0
        if args.command == "preparation-report":
            result = preparation_report(contract, jobs, args.root.resolve())
            if args.output is not None:
                atomic_json(args.output, result)
                return 0
            expected = load_json(args.check_report)
            if expected != result:
                raise ContractError("rapport de préparation F46 différent des sources")
            print(f"F46 preparation report OK: {args.check_report}")
            return 0
        if args.command == "plan":
            result = build_plan(
                contract,
                jobs,
                load_json(args.offers),
                load_json(args.image_proof),
                load_json(args.inventory_before),
                load_json(args.ledger),
                now_epoch=args.now_epoch,
                operator_deadline_epoch=args.operator_deadline_epoch,
                root=args.root.resolve(),
                allow_synthetic=args.allow_synthetic_fixture,
            )
        elif args.command == "cost-check":
            result = cost_check(
                contract,
                load_json(args.plan),
                load_json(args.ledger),
                load_json(args.instance),
                now_epoch=args.now_epoch,
                allow_synthetic=args.allow_synthetic_fixture,
            )
        else:
            result = finalize(
                contract,
                load_json(args.plan),
                load_json(args.jobs_state),
                load_json(args.ledger),
                load_json(args.destroy_report),
                load_json(args.inventory_after),
                allow_synthetic=args.allow_synthetic_fixture,
            )
        atomic_json(args.output, result)
        if args.command == "plan":
            return 0 if result["launch_authorized"] else 1
        if args.command == "cost-check":
            return 0 if result["continue_compute"] else 3
        return 0 if result["cleanup_verified"] and result["budget_respected"] else 1
    except ContractError as exc:
        if getattr(args, "output", None):
            atomic_json(
                args.output,
                {
                    "schema_version": "1.0.0",
                    "status": "blocked",
                    "launch_authorized": False,
                    "errors": [str(exc)],
                    "simulation_validated": False,
                    "metal_print_authorized": False,
                    "engine_start_authorized": False,
                },
            )
        print(f"f46-controller: {exc}", file=os.sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(cli())
