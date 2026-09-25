from __future__ import annotations

import ipaddress
import json
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any, Callable, Iterable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class MoonrakerCandidate:
    url: str
    address: str


def local_private_ipv4_addresses() -> tuple[str, ...]:
    """Return likely private IPv4 addresses for this computer.

    Discovery is intentionally conservative: U1FA never sends printer commands
    here. The addresses are used only to derive small /24 LAN ranges that can
    be probed with read-only Moonraker HTTP requests.
    """
    found: set[str] = set()
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            address = info[4][0]
            try:
                parsed = ipaddress.ip_address(address)
            except ValueError:
                continue
            if parsed.is_private and not parsed.is_loopback:
                found.add(address)
    except OSError:
        pass

    # A UDP connect does not send application data. It lets the OS tell us
    # which local interface would be used for a normal LAN/internet route.
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.connect(("192.0.2.1", 9))
            address = sock.getsockname()[0]
        finally:
            sock.close()
        parsed = ipaddress.ip_address(address)
        if parsed.is_private and not parsed.is_loopback:
            found.add(address)
    except OSError:
        pass

    return tuple(sorted(found, key=lambda value: ipaddress.ip_address(value)))


def lan_hosts(addresses: Iterable[str], max_networks: int = 3) -> tuple[str, ...]:
    """Build a bounded set of /24 peers from local private addresses."""
    values = tuple(addresses)
    networks: list[ipaddress.IPv4Network] = []
    for value in values:
        try:
            parsed = ipaddress.ip_address(value)
        except ValueError:
            continue
        if not isinstance(parsed, ipaddress.IPv4Address):
            continue
        if not parsed.is_private or parsed.is_loopback:
            continue
        network = ipaddress.ip_network(f"{parsed}/24", strict=False)
        if network not in networks:
            networks.append(network)
        if len(networks) >= max_networks:
            break

    hosts: list[str] = []
    seen: set[str] = set()
    local = set(values)
    for network in networks:
        for host in network.hosts():
            text = str(host)
            if text in local or text in seen:
                continue
            seen.add(text)
            hosts.append(text)
    return tuple(hosts)


def _read_json(
    url: str,
    timeout: float,
    opener: Callable[..., object],
) -> Any:
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "u1-filament-automation/1.8.0b23",
        },
        method="GET",
    )
    with opener(request, timeout=timeout) as response:  # type: ignore[attr-defined]
        charset = response.headers.get_content_charset() or "utf-8"
        return json.loads(response.read().decode(charset))


def _is_moonraker_payload(payload: object) -> bool:
    if not isinstance(payload, dict):
        return False
    result = payload.get("result")
    if not isinstance(result, dict):
        return False
    markers = {
        "klippy_connected",
        "klippy_state",
        "components",
        "failed_components",
        "registered_directories",
        "warnings",
    }
    return bool(markers.intersection(result))


def _has_snapmaker_u1_object(payload: object) -> bool:
    if not isinstance(payload, dict):
        return False
    result = payload.get("result")
    if not isinstance(result, dict):
        return False
    objects = result.get("objects")
    if not isinstance(objects, list):
        return False
    # machine_state_manager is the Snapmaker-specific object already consumed
    # by U1FA's safety checks. Requiring it prevents auto-selecting an unrelated
    # generic Klipper/Moonraker printer discovered on the same LAN.
    return "machine_state_manager" in {str(value) for value in objects}


def probe_moonraker(
    address: str,
    timeout: float = 0.35,
    opener: Callable[..., object] = urlopen,
) -> MoonrakerCandidate | None:
    """Probe one host with read-only GETs only; never sends G-code."""
    url = f"http://{address}"
    try:
        server_info = _read_json(f"{url}/server/info", timeout, opener)
        if not _is_moonraker_payload(server_info):
            return None
        objects = _read_json(f"{url}/printer/objects/list", timeout, opener)
        if not _has_snapmaker_u1_object(objects):
            return None
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError):
        return None
    return MoonrakerCandidate(url=url, address=address)


def discover_moonraker_candidates(
    addresses: Iterable[str] | None = None,
    timeout: float = 0.35,
    max_workers: int = 48,
    probe: Callable[[str, float], MoonrakerCandidate | None] | None = None,
) -> tuple[MoonrakerCandidate, ...]:
    """Find Snapmaker U1 Moonraker endpoints using bounded read-only LAN probes."""
    local_addresses = (
        local_private_ipv4_addresses() if addresses is None else tuple(addresses)
    )
    hosts = lan_hosts(local_addresses)
    if not hosts:
        return ()
    probe_fn = probe or (lambda host, probe_timeout: probe_moonraker(host, probe_timeout))
    found: list[MoonrakerCandidate] = []
    workers = max(1, min(int(max_workers), 64))
    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="u1fa-moonraker-scan") as pool:
        futures = {pool.submit(probe_fn, host, timeout): host for host in hosts}
        for future in as_completed(futures):
            try:
                candidate = future.result()
            except Exception:
                candidate = None
            if candidate is not None:
                found.append(candidate)
    return tuple(sorted(found, key=lambda item: ipaddress.ip_address(item.address)))
