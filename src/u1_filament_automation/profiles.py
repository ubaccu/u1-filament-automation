from __future__ import annotations

import re
from typing import Any

from .models import ProfilePreview, SpoolmanInventory


def _clean(value: Any, fallback: str = "Unknown") -> str:
    text = fallback if value is None else str(value)
    return re.sub(r"\s+", " ", text).strip() or fallback


def _pretty_vendor(value: Any) -> str:
    vendor = _clean(value, "Generic")
    return vendor.title() if vendor.isupper() or vendor.islower() else vendor


def _pretty_material(value: Any) -> str:
    material = _clean(value, "Unknown")
    known = {"pla", "petg", "abs", "asa", "tpu", "pa", "pc", "pva", "hips"}
    return material.upper() if material.casefold() in known else material


def _tokens(value: str) -> list[str]:
    return re.findall(r"[^\W_]+", value, flags=re.UNICODE)


def _pretty_token(value: str) -> str:
    if value.isupper() or value.islower():
        return value.title()
    return value


def _clean_variant(variant: Any, vendor: str, material: str) -> str:
    words = _tokens(_clean(variant, material))
    vendor_words = [word.casefold() for word in _tokens(vendor)]
    material_words = {word.casefold() for word in _tokens(material)}

    if vendor_words and [word.casefold() for word in words[: len(vendor_words)]] == vendor_words:
        words = words[len(vendor_words) :]
    words = [word for word in words if word.casefold() not in material_words]
    if not words:
        return material
    return " ".join(_pretty_token(word) for word in words)


def _filament_from_spool(spool: dict[str, Any], inventory: SpoolmanInventory) -> dict[str, Any]:
    nested = spool.get("filament")
    if isinstance(nested, dict):
        return nested
    filament_id = spool.get("filament_id")
    for filament in inventory.filaments:
        if filament.get("id") == filament_id:
            return filament
    return {}


def _vendor_name(filament: dict[str, Any], inventory: SpoolmanInventory) -> str:
    nested = filament.get("vendor")
    if isinstance(nested, dict):
        return _pretty_vendor(nested.get("name"))
    vendor_id = filament.get("vendor_id")
    for vendor in inventory.vendors:
        if vendor.get("id") == vendor_id:
            return _pretty_vendor(vendor.get("name"))
    return "Generic"


def build_previews(inventory: SpoolmanInventory, nozzle: float = 0.4) -> list[ProfilePreview]:
    grouped: dict[tuple[str, str, str], dict[str, Any]] = {}
    for spool in inventory.spools:
        filament = _filament_from_spool(spool, inventory)
        vendor = _vendor_name(filament, inventory)
        material = _pretty_material(filament.get("material"))
        variant = _clean_variant(
            filament.get("name") or filament.get("variant"),
            vendor,
            material,
        )
        key = (vendor.casefold(), material.casefold(), variant.casefold())
        entry = grouped.setdefault(
            key,
            {"vendor": vendor, "material": material, "variant": variant, "ids": []},
        )
        spool_id = spool.get("id")
        if spool_id is not None:
            entry["ids"].append(spool_id)

    previews: list[ProfilePreview] = []
    for entry in grouped.values():
        words = [entry["vendor"], entry["material"]]
        if entry["variant"].casefold() != entry["material"].casefold():
            words.append(entry["variant"])
        technical_name = " ".join(words)
        previews.append(
            ProfilePreview(
                identity=technical_name,
                base_profile=f"{technical_name} @Snapmaker U1 base",
                nozzle_profile=f"{technical_name} @Snapmaker U1 ({nozzle:g} nozzle)",
                spool_ids=tuple(entry["ids"]),
            )
        )
    return sorted(previews, key=lambda item: item.identity.casefold())
