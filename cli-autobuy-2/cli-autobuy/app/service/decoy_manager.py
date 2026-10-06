"""
Decoy Manager
=============
Kelola isi file decoy_data/*.json via CLI tanpa edit manual.

6 slot decoy:
  default-balance   → pulsa biasa, user PREPAID/reguler
  default-qris      → QRIS (+Rp1K), user PREPAID/reguler
  default-qris0     → QRIS (Rp0), user PREPAID/reguler
  prio-balance      → pulsa, user PRIORITAS/PRIOHYBRID/GO
  prio-qris         → QRIS (+Rp1K), user PRIORITAS
  prio-qris0        → QRIS (Rp0), user PRIORITAS

Setiap file wajib field:
  family_name, family_code, is_enterprise, migration_type,
  variant_code, option_name, order, price
"""

import json
import os

DECOY_DIR = "decoy_data"

DECOY_SLOTS = {
    "default-balance": "Pulsa – PREPAID/Reguler",
    "default-qris":    "QRIS (+Rp1K) – PREPAID/Reguler",
    "default-qris0":   "QRIS (Rp0) – PREPAID/Reguler",
    "prio-balance":    "Pulsa – PRIORITAS/PRIOHYBRID/GO",
    "prio-qris":       "QRIS (+Rp1K) – PRIORITAS",
    "prio-qris0":      "QRIS (Rp0) – PRIORITAS",
}

REQUIRED_FIELDS = [
    "family_name", "family_code", "is_enterprise",
    "migration_type", "variant_code", "option_name", "order", "price"
]


def _path(slot: str) -> str:
    return os.path.join(DECOY_DIR, f"decoy-{slot}.json")


def load_slot(slot: str) -> dict:
    p = _path(slot)
    if not os.path.exists(p):
        return {}
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[Decoy] Gagal baca {p}: {e}")
        return {}


def save_slot(slot: str, data: dict) -> bool:
    p = _path(slot)
    try:
        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[Decoy] Gagal simpan {p}: {e}")
        return False


def validate_data(data: dict) -> list:
    """Return list of missing/invalid fields."""
    errors = []
    for field in REQUIRED_FIELDS:
        if field not in data:
            errors.append(f"Field '{field}' tidak ada")
    if "order" in data:
        try:
            int(data["order"])
        except (ValueError, TypeError):
            errors.append("'order' harus integer")
    if "price" in data:
        try:
            int(data["price"])
        except (ValueError, TypeError):
            errors.append("'price' harus integer")
    return errors


def fetch_and_preview(api_key: str, tokens: dict, data: dict) -> dict | None:
    """
    Coba fetch family dari API untuk validasi family_code + variant_code + order.
    Return option detail atau None.
    """
    from app.client.engsel import get_package_details
    try:
        print("Memvalidasi ke API...")
        result = get_package_details(
            api_key, tokens,
            data["family_code"],
            data["variant_code"],
            int(data["order"]),
            data.get("is_enterprise"),
            data.get("migration_type") or None,
        )
        return result
    except Exception as e:
        print(f"[Decoy] Validasi API gagal: {e}")
        return None
