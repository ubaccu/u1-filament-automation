from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any, Callable, Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .models import SpoolmanInventory


class ServiceError(RuntimeError):
    pass


def normalize_url(value: str) -> str:
    value = value.strip().rstrip("/")
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"URL non valido: {value!r}")
    return value


def get_json(url: str, timeout: float = 2.0) -> Any:
    return request_json(url, timeout=timeout)


def request_json(
    url: str,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
    timeout: float = 2.0,
    opener: Callable[..., Any] = urlopen,
) -> Any:
    data = None
    headers = {
        "Accept": "application/json",
        "User-Agent": "u1-filament-automation/1.1",
    }
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = Request(url, data=data, headers=headers, method=method.upper())
    try:
        with opener(request, timeout=timeout) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return json.loads(response.read().decode(charset))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        raise ServiceError(f"{url}: {exc}") from exc


class SpoolmanClient:
    """Client minimo per gli endpoint REST ufficiali usati dall'app."""

    def __init__(
        self,
        base_url: str,
        timeout: float = 2.0,
        opener: Callable[..., Any] = urlopen,
    ) -> None:
        self.base_url = normalize_url(base_url)
        self.timeout = timeout
        self.opener = opener

    def _request(
        self,
        method: str,
        endpoint: str,
        payload: dict[str, Any] | None = None,
    ) -> Any:
        return request_json(
            f"{self.base_url}/api/v1/{endpoint}",
            method=method,
            payload=payload,
            timeout=self.timeout,
            opener=self.opener,
        )

    def inventory(self) -> SpoolmanInventory:
        vendors = _as_list(self._request("GET", "vendor"), "vendor")
        filaments = _as_list(self._request("GET", "filament"), "filament")
        spools = _as_list(self._request("GET", "spool"), "spool")
        return SpoolmanInventory(
            url=self.base_url,
            vendors=vendors,
            filaments=filaments,
            spools=spools,
        )

    def create_vendor(self, payload: dict[str, Any]) -> dict[str, Any]:
        return _created_object(self._request("POST", "vendor", payload), "vendor")

    def create_filament(self, payload: dict[str, Any]) -> dict[str, Any]:
        return _created_object(
            self._request("POST", "filament", payload),
            "filamento",
        )

    def create_spool(self, payload: dict[str, Any]) -> dict[str, Any]:
        return _created_object(self._request("POST", "spool", payload), "bobina")


def _created_object(payload: Any, label: str) -> dict[str, Any]:
    if not isinstance(payload, dict) or payload.get("id") is None:
        raise ServiceError(
            f"Spoolman ha restituito una risposta inattesa creando {label}"
        )
    return payload


@dataclass(frozen=True)
class NewSpoolRequest:
    vendor: str
    material: str
    name: str
    color_hex: str
    density: float
    diameter: float
    filament_weight: float
    empty_spool_weight: float
    remaining_weight: float
    nozzle_temperature: int
    bed_temperature: int
    location: str = ""
    lot_nr: str = ""
    comment: str = "Creato con U1 Filament Automation"
    # Spoolman rappresenta le bobine multicolore con una stringa di HEX
    # separati da virgole.  Manteniamo una tupla nel modello interno per non
    # perdere l'ordine dei colori quando creiamo il profilo Orca.
    multi_color_hexes: tuple[str, ...] = ()

    @property
    def used_weight(self) -> float:
        return round(self.filament_weight - self.remaining_weight, 3)

    def validated(self) -> "NewSpoolRequest":
        vendor = _required_text(self.vendor, "Marca/vendor")
        material = _required_text(self.material, "Materiale").upper()
        name = _required_text(self.name, "Nome tecnico")
        if len(vendor) > 64 or len(material) > 64 or len(name) > 64:
            raise ValueError("Marca, materiale e nome tecnico devono avere al massimo 64 caratteri")
        color_values = _parse_color_values(self.multi_color_hexes)
        if color_values:
            if len(color_values) < 2 or len(color_values) > 8:
                raise ValueError("Una bobina multicolore deve avere da 2 a 8 colori HEX")
            colors = tuple(_normalize_color(value) for value in color_values)
            if len(set(colors)) != len(colors):
                raise ValueError("I colori HEX della bobina multicolore devono essere distinti")
            color = colors[0]
        else:
            color = _normalize_color(self.color_hex)
            colors = ()
        if not 0.1 <= float(self.density) <= 10:
            raise ValueError("La densità deve essere compresa tra 0.1 e 10 g/cm³")
        if not 1.0 <= float(self.diameter) <= 4.0:
            raise ValueError("Il diametro deve essere compreso tra 1 e 4 mm")
        if not 0 < float(self.filament_weight) <= 50000:
            raise ValueError("Il peso nominale deve essere compreso tra 0 e 50000 g")
        if not 0 <= float(self.empty_spool_weight) <= 10000:
            raise ValueError("La tara deve essere compresa tra 0 e 10000 g")
        if not 0 <= float(self.remaining_weight) <= float(self.filament_weight):
            raise ValueError("Il peso rimasto deve essere compreso tra 0 e il peso nominale")
        if not 170 <= int(self.nozzle_temperature) <= 300:
            raise ValueError("La temperatura ugello deve essere compresa tra 170 e 300 °C")
        if not 0 <= int(self.bed_temperature) <= 150:
            raise ValueError("La temperatura piano deve essere compresa tra 0 e 150 °C")
        location = self.location.strip()
        lot_nr = self.lot_nr.strip()
        comment = self.comment.strip()
        if len(location) > 64 or len(lot_nr) > 64 or len(comment) > 1024:
            raise ValueError("Posizione, lotto o commento superano la lunghezza consentita")
        return NewSpoolRequest(
            vendor=vendor,
            material=material,
            name=name,
            color_hex=color,
            density=float(self.density),
            diameter=float(self.diameter),
            filament_weight=float(self.filament_weight),
            empty_spool_weight=float(self.empty_spool_weight),
            remaining_weight=float(self.remaining_weight),
            nozzle_temperature=int(self.nozzle_temperature),
            bed_temperature=int(self.bed_temperature),
            location=location,
            lot_nr=lot_nr,
            comment=comment,
            multi_color_hexes=colors,
        )


def _required_text(value: str, label: str) -> str:
    result = re.sub(r"\s+", " ", str(value)).strip()
    if not result:
        raise ValueError(f"{label} obbligatorio")
    return result


def _parse_color_values(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        values = re.split(r"[,;\s]+", value.strip())
    else:
        try:
            values = list(value)
        except TypeError:
            values = [value]
    return tuple(str(item).strip() for item in values if str(item).strip())


def _normalize_color(value: Any) -> str:
    color = str(value).strip().lstrip("#").upper()
    if not re.fullmatch(r"[0-9A-F]{6}", color):
        raise ValueError("Il colore deve essere un valore esadecimale di 6 cifre")
    return color


def _filament_colors(filament: dict[str, Any]) -> tuple[str, ...]:
    values = _parse_color_values(filament.get("multi_color_hexes"))
    if len(values) >= 2:
        try:
            return tuple(_normalize_color(value) for value in values)
        except ValueError:
            pass
    color = filament.get("color_hex")
    if color:
        try:
            return (_normalize_color(color),)
        except ValueError:
            return ()
    return ()


@dataclass(frozen=True)
class SpoolCreationPlan:
    request: NewSpoolRequest
    vendor_id: int | str | None
    filament_id: int | str | None
    profile_name: str
    base_profile: str

    @property
    def vendor_action(self) -> str:
        return "reuse" if self.vendor_id is not None else "create"

    @property
    def filament_action(self) -> str:
        return "reuse" if self.filament_id is not None else "create"


@dataclass(frozen=True)
class SpoolCreationResult:
    plan: SpoolCreationPlan
    vendor_id: int | str
    filament_id: int | str
    spool_id: int | str
    vendor_created: bool
    filament_created: bool


def plan_spool_creation(
    inventory: SpoolmanInventory,
    request: NewSpoolRequest,
) -> SpoolCreationPlan:
    from .sync import choose_base, make_profile_name

    item = request.validated()
    vendor_matches = [
        vendor for vendor in inventory.vendors
        if str(vendor.get("name", "")).strip().casefold() == item.vendor.casefold()
    ]
    if len(vendor_matches) > 1:
        raise ValueError(f"Più vendor Spoolman hanno il nome {item.vendor!r}")
    vendor_id = vendor_matches[0].get("id") if vendor_matches else None
    if vendor_matches and vendor_id is None:
        raise ValueError("Il vendor Spoolman trovato non ha un ID valido")

    filament_matches: list[dict[str, Any]] = []
    if vendor_id is not None:
        for filament in inventory.filaments:
            nested_vendor = filament.get("vendor")
            filament_vendor_id = filament.get("vendor_id")
            if filament_vendor_id is None and isinstance(nested_vendor, dict):
                filament_vendor_id = nested_vendor.get("id")
            filament_colors = _filament_colors(filament)
            if (
                str(filament_vendor_id) == str(vendor_id)
                and str(filament.get("material", "")).strip().casefold() == item.material.casefold()
                and str(filament.get("name", "")).strip().casefold() == item.name.casefold()
                and filament_colors == (item.multi_color_hexes or (item.color_hex,))
            ):
                filament_matches.append(filament)
    if len(filament_matches) > 1:
        raise ValueError("Più filamenti Spoolman corrispondono esattamente ai dati inseriti")
    filament_id = filament_matches[0].get("id") if filament_matches else None
    if filament_matches and filament_id is None:
        raise ValueError("Il filamento Spoolman trovato non ha un ID valido")

    base = choose_base(
        item.vendor,
        item.material,
        item.name,
        multicolor=len(item.multi_color_hexes) >= 2,
    )
    if base is None:
        raise ValueError(
            "Materiale non ancora associato a un profilo base Snapmaker; creazione bloccata"
        )
    return SpoolCreationPlan(
        request=item,
        vendor_id=vendor_id,
        filament_id=filament_id,
        profile_name=make_profile_name(item.vendor, item.material, item.name),
        base_profile=base,
    )


def create_spool_from_plan(
    client: SpoolmanClient,
    plan: SpoolCreationPlan,
) -> SpoolCreationResult:
    item = plan.request
    vendor_id = plan.vendor_id
    filament_id = plan.filament_id
    vendor_created = False
    filament_created = False
    progress: list[str] = []
    try:
        if vendor_id is None:
            vendor_payload: dict[str, Any] = {"name": item.vendor}
            if item.empty_spool_weight:
                vendor_payload["empty_spool_weight"] = item.empty_spool_weight
            vendor = client.create_vendor(vendor_payload)
            vendor_id = vendor["id"]
            vendor_created = True
            progress.append(f"vendor ID {vendor_id}")
        if filament_id is None:
            filament_payload: dict[str, Any] = {
                "vendor_id": vendor_id,
                "name": item.name,
                "material": item.material,
                "density": item.density,
                "diameter": item.diameter,
                "weight": item.filament_weight,
                "spool_weight": item.empty_spool_weight,
                "settings_extruder_temp": item.nozzle_temperature,
                "settings_bed_temp": item.bed_temperature,
                "comment": item.comment,
            }
            if item.multi_color_hexes:
                filament_payload["multi_color_hexes"] = ",".join(item.multi_color_hexes)
            else:
                filament_payload["color_hex"] = item.color_hex
            filament = client.create_filament(filament_payload)
            filament_id = filament["id"]
            filament_created = True
            progress.append(f"filamento ID {filament_id}")
        spool_payload: dict[str, Any] = {
            "filament_id": filament_id,
            "initial_weight": item.filament_weight,
            "spool_weight": item.empty_spool_weight,
            "used_weight": item.used_weight,
            "comment": item.comment,
        }
        if item.location:
            spool_payload["location"] = item.location
        if item.lot_nr:
            spool_payload["lot_nr"] = item.lot_nr
        spool = client.create_spool(spool_payload)
        return SpoolCreationResult(
            plan=plan,
            vendor_id=vendor_id,
            filament_id=filament_id,
            spool_id=spool["id"],
            vendor_created=vendor_created,
            filament_created=filament_created,
        )
    except (ServiceError, KeyError, TypeError) as exc:
        detail = "" if not progress else f"; già creati: {', '.join(progress)}"
        raise ServiceError(
            f"Creazione Spoolman interrotta{detail}. Nessuna cancellazione automatica: {exc}"
        ) from exc


def _as_list(payload: Any, endpoint: str) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("items", "results", endpoint):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    raise ServiceError(f"Risposta inattesa dall'endpoint {endpoint}")


def read_inventory(base_url: str, timeout: float = 2.0) -> SpoolmanInventory:
    return SpoolmanClient(base_url, timeout=timeout).inventory()


def explicit_candidates(
    spoolman_url: str | None = None,
    environ: dict[str, str] | None = None,
) -> list[str]:
    env = os.environ if environ is None else environ
    values = [
        spoolman_url,
        env.get("U1FA_SPOOLMAN_URL"),
        "http://127.0.0.1:7912",
        "http://localhost:7912",
    ]
    result: list[str] = []
    for value in values:
        if not value:
            continue
        try:
            normalized = normalize_url(value)
        except ValueError:
            continue
        if normalized not in result:
            result.append(normalized)
    return result


def _walk(value: Any, path: tuple[str, ...] = ()) -> Iterable[tuple[tuple[str, ...], str]]:
    if isinstance(value, dict):
        for key, child in value.items():
            yield from _walk(child, path + (str(key).lower(),))
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child, path)
    elif isinstance(value, str):
        yield path, value


def extract_spoolman_urls(payload: Any) -> list[str]:
    result: list[str] = []
    url_pattern = re.compile(r"https?://[^\s\"'<>]+")
    for path, value in _walk(payload):
        joined = ".".join(path)
        if "spoolman" not in joined and "spoolman" not in value.lower():
            continue
        for match in url_pattern.findall(value):
            try:
                normalized = normalize_url(match.rstrip(",;)]}"))
            except ValueError:
                continue
            if normalized not in result:
                result.append(normalized)
    return result


def candidates_from_moonraker(moonraker_url: str, timeout: float = 2.0) -> list[str]:
    base = normalize_url(moonraker_url)
    payload = get_json(f"{base}/server/config", timeout=timeout)
    result = extract_spoolman_urls(payload)

    host = urlparse(base).hostname
    if host:
        local_guess = f"http://{host}:7912"
        if local_guess not in result:
            result.append(local_guess)
    return result


def first_working_inventory(candidates: Iterable[str], timeout: float = 2.0) -> tuple[SpoolmanInventory | None, list[str]]:
    errors: list[str] = []
    for candidate in candidates:
        try:
            return read_inventory(candidate, timeout=timeout), errors
        except (ServiceError, ValueError) as exc:
            errors.append(str(exc))
    return None, errors
