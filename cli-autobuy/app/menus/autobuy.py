"""
Menu Auto Buy
"""

import os, json, copy, time, threading
from app.menus.util import clear_screen, pause
from app.service.autobuy import AutoBuyInstance, PAYMENT_METHODS
from app.service.auth import AuthInstance
from app.client.engsel import get_family

W = 58
PRESET_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "preset_packages.json")
LOG_FILE = "autobuy.log"

def _sep(): print("─" * W)
def _hdr(t): print("=" * W); print(f"  {t}"); print("=" * W)

def _int(prompt, default):
    r = input(f"  {prompt} [{default}]: ").strip()
    try: return int(r) if r else default
    except ValueError: return default

def _load_presets():
    try:
        with open(PRESET_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def _save_presets(presets: list):
    os.makedirs(os.path.dirname(PRESET_FILE), exist_ok=True)
    with open(PRESET_FILE, "w", encoding="utf-8") as f:
        json.dump(presets, f, indent=4, ensure_ascii=False)

def _presets_menu():
    """Kelola daftar preset paket."""
    while True:
        clear_screen()
        presets = _load_presets()
        _hdr("📦 Kelola Preset Paket")

        if not presets:
            print("  (belum ada preset)")
        else:
            for i, p in enumerate(presets):
                print(f"  {i+1}. {p['label']}")
        print()
        _sep()
        print("  1. Tambah preset via family code")
        print("  2. Hapus preset")
        print("  0. Kembali")
        _sep()
        c = input("  Pilihan: ").strip()

        if c == "0":
            break

        elif c == "1":
            # Browse family code lalu simpan ke preset
            _add_to_preset()

        elif c == "2":
            if not presets:
                print("  Tidak ada preset."); pause(); continue
            clear_screen()
            _hdr("Hapus Preset")
            for i, p in enumerate(presets):
                print(f"  {i+1}. {p['label']}")
            print()
            _sep()
            print("  Pilih: contoh  1 3   |  A = semua  |  0 = batal")
            _sep()
            r = input("  Pilih: ").strip()
            if r == "0": continue
            idxs = sorted(_parse_multi(r, len(presets)), reverse=True)
            for idx in idxs:
                removed = presets.pop(idx)
                print(f"  ✅ '{removed['label']}' dihapus.")
            _save_presets(presets)
            pause()

        else:
            print("  ❌ Tidak valid."); pause()


def _add_to_preset():
    """Browse family code, pilih paket, simpan ke preset."""
    # Pakai akun aktif
    active = AuthInstance.get_active_user()
    if not active:
        print("  ❌ Tidak ada akun aktif."); pause(); return

    api_key = AuthInstance.api_key
    tokens  = active["tokens"]

    fc = input("  Family code: ").strip()
    if not fc: return

    print("  Mengambil data...")
    data = get_family(api_key, tokens, fc)
    if not data:
        print("  ❌ Tidak ditemukan."); pause(); return

    fname    = data["package_family"]["name"]
    variants = data["package_variants"]

    clear_screen()
    _hdr(fname)
    print(f"  Code: {fc}"); _sep()

    numbered = []
    n = 1
    presets  = _load_presets()
    existing_keys = {(p["family_code"], p["order"]) for p in presets}

    for v in variants:
        vname = v["name"]; vcode = v["package_variant_code"]
        print(f"  [{vname}]")
        for opt in v["package_options"]:
            bnames = [b["name"] for b in opt.get("benefits", [])
                      if b.get("data_type") == "DATA" and b.get("name")]
            already = (fc, opt["order"]) in existing_keys
            mark = " ✅" if already else ""
            print(f"    {n}. {opt['name']}  Rp{opt['price']:,}{mark}")
            numbered.append({
                "label":         opt["name"],
                "family_code":   fc,
                "family_name":   fname,
                "variant_code":  vcode,
                "variant_name":  vname,
                "option_name":   opt["name"],
                "order":         opt["order"],
                "is_enterprise": False,
                "benefit_names": bnames,
            })
            n += 1
        print()

    _sep()
    print("  Pilih yang mau disimpan ke preset:")
    print("  contoh  1 3 4   |  A = semua  |  0 = batal")
    _sep()
    r = input("  Pilih: ").strip()
    if r == "0": return

    idxs  = _parse_multi(r, len(numbered))
    added = 0
    for idx in idxs:
        pkg = numbered[idx]
        key = (pkg["family_code"], pkg["order"])
        if key in existing_keys:
            print(f"  ⚠ '{pkg['label']}' sudah ada di preset, skip.")
            continue
        presets.append(pkg)
        existing_keys.add(key)
        added += 1

    if added:
        _save_presets(presets)
        print(f"\n  ✅ {added} paket ditambahkan ke preset.")
    else:
        print(f"\n  Tidak ada yang ditambahkan.")
    pause()

def _pick_method(current="balance") -> str:
    methods = list(PAYMENT_METHODS.items())
    print("\n  Metode pembayaran:")
    for i, (k, label) in enumerate(methods):
        mark = " ◀" if k == current else ""
        print(f"    {i+1}. {label}{mark}")
    r = input(f"  Pilih [1-{len(methods)}, Enter=skip]: ").strip()
    if r.isdigit() and 1 <= int(r) <= len(methods):
        return methods[int(r)-1][0]
    return current

def _parse_multi(raw: str, max_n: int):
    """Parse input '1 3 5' atau 'A' → list of 0-based index."""
    raw = raw.strip().lower()
    if raw in ("a", "semua"):
        return list(range(max_n))
    result = []
    for tok in raw.split():
        if tok.isdigit() and 1 <= int(tok) <= max_n:
            idx = int(tok) - 1
            if idx not in result:
                result.append(idx)
    return result

# ── Kelola paket ─────────────────────────────────────────────────

def _packages_menu(number: int):
    presets = _load_presets()

    while True:
        clear_screen()
        entry = AutoBuyInstance.get_by_number(number)
        if not entry: break

        _hdr(f"Paket Auto Buy — {number}")
        pkgs = entry.get("packages", [])

        if not pkgs:
            print("  (belum ada paket)")
        else:
            for i, p in enumerate(pkgs):
                print(f"  {i+1}. {p.get('option_name','?')}")
        print()
        _sep()
        print("  1. Tambah dari daftar preset")
        print("  2. Tambah via family code (manual)")
        print("  3. Hapus paket")
        print("  0. Selesai")
        _sep()
        c = input("  Pilihan: ").strip()

        if c == "0":
            break

        elif c == "1":
            # Tambah dari preset
            clear_screen()
            _hdr("Daftar Paket Preset")
            for i, p in enumerate(presets):
                # Tandai kalau sudah ada
                already = any(
                    x.get("family_code") == p["family_code"] and
                    x.get("order") == p["order"]
                    for x in entry.get("packages", [])
                )
                mark = " ✅" if already else ""
                print(f"  {i+1}. {p['label']}{mark}")
            print()
            _sep()
            print("  Pilih beberapa: contoh  1 3 4   |  A = semua")
            print("  0. Batal")
            _sep()
            r = input("  Pilih: ").strip()
            if r == "0":
                continue
            idxs = _parse_multi(r, len(presets))
            added = 0
            for idx in idxs:
                ok = AutoBuyInstance.add_package(number, presets[idx])
                if ok: added += 1
            print(f"\n  {added} paket ditambahkan.")
            pause()

        elif c == "2":
            # Tambah via family code
            _add_via_family(number)

        elif c == "3":
            if not pkgs:
                print("  Tidak ada paket."); pause(); continue
            clear_screen()
            _hdr(f"Hapus Paket — {number}")
            for i, p in enumerate(pkgs):
                print(f"  {i+1}. {p.get('option_name','?')}")
            print()
            _sep()
            print("  Pilih beberapa: contoh  1 3   |  A = semua")
            print("  0. Batal")
            _sep()
            r = input("  Pilih: ").strip()
            if r == "0":
                continue
            idxs = sorted(_parse_multi(r, len(pkgs)), reverse=True)
            for idx in idxs:
                AutoBuyInstance.remove_package(number, idx)
            print(f"\n  {len(idxs)} paket dihapus.")
            pause()

        else:
            print("  ❌ Tidak valid."); pause()


def _add_via_family(number: int):
    api_key = AuthInstance.api_key
    AuthInstance.set_active_user(number)
    active = AuthInstance.get_active_user()
    if not active:
        print("  ❌ Gagal ambil token."); pause(); return
    tokens = active["tokens"]

    fc = input("  Family code: ").strip()
    if not fc: return

    print("  Mengambil data...")
    data = get_family(api_key, tokens, fc)
    if not data:
        print("  ❌ Tidak ditemukan."); pause(); return

    fname    = data["package_family"]["name"]
    variants = data["package_variants"]

    clear_screen()
    _hdr(fname)
    print(f"  Code: {fc}"); _sep()

    numbered = []
    n = 1
    for v in variants:
        vname = v["name"]; vcode = v["package_variant_code"]
        print(f"  [{vname}]")
        for opt in v["package_options"]:
            bnames = [b["name"] for b in opt.get("benefits", [])
                      if b.get("data_type") == "DATA" and b.get("name")]
            print(f"    {n}. {opt['name']}  Rp{opt['price']:,}")
            numbered.append({
                "family_code": fc, "family_name": fname,
                "variant_code": vcode, "variant_name": vname,
                "option_name": opt["name"], "order": opt["order"],
                "is_enterprise": False, "benefit_names": bnames,
            })
            n += 1
        print()

    _sep()
    print("  Pilih beberapa: contoh  1 3 4   |  A = semua  |  0 = batal")
    _sep()
    r = input("  Pilih: ").strip()
    if r == "0": return
    idxs  = _parse_multi(r, len(numbered))
    added = 0
    for idx in idxs:
        ok = AutoBuyInstance.add_package(number, numbered[idx])
        if ok: added += 1
    print(f"\n  {added} paket ditambahkan.")
    pause()

# ── Edit konfigurasi ──────────────────────────────────────────────

def _edit_menu(entry: dict):
    number = entry["number"]
    while True:
        clear_screen()
        _hdr(f"Edit — {number}")
        m = PAYMENT_METHODS.get(entry.get("payment_method","balance"),"?")
        status = "AKTIF" if entry.get("active", True) else "NONAKTIF"
        print(f"  1. Status          : {status}")
        print(f"  2. Threshold kuota : {entry.get('threshold_mb',100)} MB")
        print(f"  3. Interval cek    : {entry['interval_minutes']} menit")
        print(f"  4. Jeda antar beli : {entry.get('buy_delay_seconds',16)} detik")
        print(f"  5. Max beli/sesi   : {entry['max_buy']} (0=∞)")
        print(f"  6. Metode bayar    : {m}")
        print(f"  7. Kelola paket")
        print(f"  0. Selesai")
        _sep()
        c = input("  Pilihan: ").strip()

        if c == "0": break
        elif c == "1":
            AutoBuyInstance.toggle_active(number)
            # Baca ulang dari storage supaya status sinkron
            fresh = AutoBuyInstance.get_by_number(number)
            if fresh:
                entry["active"] = fresh["active"]
            pause()
        elif c == "2":
            v = max(0, _int("Threshold MB", entry.get("threshold_mb",100)))
            AutoBuyInstance.update_entry(number, threshold_mb=v)
            entry["threshold_mb"] = v; print("  ✅"); pause()
        elif c == "3":
            v = max(1, _int("Interval menit", entry["interval_minutes"]))
            AutoBuyInstance.update_entry(number, interval_minutes=v)
            entry["interval_minutes"] = v; print("  ✅"); pause()
        elif c == "4":
            v = max(0, _int("Jeda detik", entry.get("buy_delay_seconds",16)))
            AutoBuyInstance.update_entry(number, buy_delay_seconds=v)
            entry["buy_delay_seconds"] = v; print("  ✅"); pause()
        elif c == "5":
            v = max(0, _int("Max beli", entry["max_buy"]))
            AutoBuyInstance.update_entry(number, max_buy=v)
            entry["max_buy"] = v; print("  ✅"); pause()
        elif c == "6":
            nm = _pick_method(entry.get("payment_method","balance"))
            AutoBuyInstance.update_entry(number, payment_method=nm)
            entry["payment_method"] = nm; print(f"  ✅ {PAYMENT_METHODS[nm]}"); pause()
        elif c == "7":
            _packages_menu(number)
        else:
            print("  ❌ Tidak valid."); pause()

# ── Daftar nomor ─────────────────────────────────────────────────

def _register_menu():
    clear_screen()
    _hdr("Daftarkan Nomor")
    users = AuthInstance.refresh_tokens
    if not users:
        print("  Belum ada akun. Login dulu."); pause(); return

    for i, u in enumerate(users):
        reg = "✅" if AutoBuyInstance.get_by_number(u["number"]) else "  "
        print(f"  {i+1}. {reg} {u['number']}")
    print("  0. Batal"); _sep()

    r = input("  Pilih: ").strip()
    if not r.isdigit() or int(r) == 0: return
    idx = int(r) - 1
    if not (0 <= idx < len(users)): print("  ❌ Tidak valid."); pause(); return

    number = users[idx]["number"]
    if AutoBuyInstance.get_by_number(number):
        print(f"  {number} sudah terdaftar.")
        if input("  Edit? (y/n): ").strip().lower() == "y":
            _edit_menu(AutoBuyInstance.get_by_number(number))
        return

    print(f"\n  Konfigurasi {number}:\n")
    threshold = max(0, _int("Threshold MB (beli jika kuota <= ini / tidak ada)", 100))
    interval  = max(1, _int("Cek kuota tiap berapa menit", 5))
    delay     = max(0, _int("Jeda antar beli (detik)", 16))
    max_buy   = max(0, _int("Max beli/sesi (0=∞)", 3))
    method    = _pick_method("balance")

    AutoBuyInstance.add_entry(
        number=number, threshold_mb=threshold, max_buy=max_buy,
        interval_minutes=interval, buy_delay_seconds=delay,
        payment_method=method,
    )
    print(f"\n  ✅ {number} didaftarkan!")
    if input("  Tambah paket sekarang? (y/n): ").strip().lower() == "y":
        _packages_menu(number)
    else:
        pause()

# ── Beli manual ───────────────────────────────────────────────────

def _buy_now(entry: dict):
    number = entry["number"]
    pkgs   = entry.get("packages", [])
    if not pkgs:
        print("  ❌ Belum ada paket."); return

    clear_screen()
    _hdr(f"Beli Manual — {number}")
    for i, p in enumerate(pkgs):
        print(f"  {i+1}. {p.get('option_name','?')}")
    print()
    _sep()
    print("  Pilih: contoh  1 3   |  A = semua  |  0 = batal")
    _sep()
    r = input("  Pilih paket: ").strip()
    if r == "0": return

    idxs = _parse_multi(r, len(pkgs))
    if not idxs: print("  ❌ Tidak ada pilihan valid."); return

    chosen = [pkgs[i] for i in idxs]
    count  = max(1, _int("Berapa kali beli", 1))

    print(f"\n  Paket  : {', '.join(p['option_name'] for p in chosen)}")
    print(f"  Metode : {PAYMENT_METHODS.get(entry['payment_method'],'?')}")
    print(f"  Jumlah : {count}x\n")

    temp = copy.copy(entry)
    temp["packages"] = chosen

    AuthInstance.set_active_user(number)
    active = AuthInstance.get_active_user()
    if not active: print("  ❌ Gagal ambil token."); return

    done = AutoBuyInstance.do_purchase(
        AuthInstance.api_key, active["tokens"], temp, count=count)
    print(f"\n  {'✅' if done > 0 else '❌'} {done}/{count} berhasil.")

# ── Lihat log live ───────────────────────────────────────────────

def _view_log():
    """Tampilkan log live, refresh tiap 3 detik. Tekan Ctrl+C untuk keluar."""
    import time as _time
    log_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)))), LOG_FILE
    )
    print(f"\n  Log: {LOG_FILE}  |  Ctrl+C untuk keluar\n")
    _time.sleep(0.5)

    last_lines = []
    try:
        while True:
            clear_screen()
            print("=" * W)
            print(f"  📋 LOG AUTO BUY  (Ctrl+C keluar)")
            print("=" * W)
            if os.path.exists(log_path):
                with open(log_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                # Tampilkan 30 baris terakhir
                show = lines[-30:] if len(lines) > 30 else lines
                for l in show:
                    print(" ", l.rstrip())
            else:
                print("  (log kosong)")
            print()
            print(f"  Refresh tiap 3 detik...")
            _time.sleep(3)
    except KeyboardInterrupt:
        print("\n  Keluar dari log viewer.")

# ── Pilih entry ───────────────────────────────────────────────────

def _pick_entry(entries, action="pilih"):
    if not entries: print("  Tidak ada entry."); pause(); return None
    if len(entries) == 1: return entries[0]
    r = input(f"  Nomor urut ({action}): ").strip()
    if r.isdigit() and 1 <= int(r) <= len(entries):
        return entries[int(r)-1]
    print("  ❌ Tidak valid."); pause(); return None

# ── Main menu ─────────────────────────────────────────────────────

def show_autobuy_menu():
    while True:
        # Selalu reload dari file supaya status aktif/nonaktif akurat
        AutoBuyInstance.reload()
        clear_screen()
        _hdr("⚡ AUTO BUY")

        entries = AutoBuyInstance.get_all()
        mon_on  = AutoBuyInstance.is_monitor_running()

        mon_status = AutoBuyInstance.get_monitor_status()

        if not entries:
            print("  Belum ada nomor terdaftar.")
        else:
            for i, e in enumerate(entries):
                number   = e["number"]
                st       = "✅" if e.get("active", True) else "⛔"
                m        = PAYMENT_METHODS.get(e.get("payment_method","balance"),"?")
                pkgs     = len(e.get("packages",[]))
                mb       = e.get("max_buy", 3)
                sess     = e.get("buy_count_session", 0)
                ms       = f"{sess}/{mb}" if mb > 0 else f"{sess}/∞"
                thr_icon = "🟢" if mon_status.get(number) else "🔴"
                last_at  = e.get("last_buy_at") or "-"
                last_st  = e.get("last_buy_status") or "-"
                print(f"  {i+1}. {st} {number} {thr_icon}")
                print(f"     Threshold : {e.get('threshold_mb',100)} MB  |  Cek: {e['interval_minutes']} mnt")
                print(f"     Terbeli   : {ms}  |  Jeda: {e.get('buy_delay_seconds',16)}s")
                print(f"     Bayar via : {m}  |  Paket: {pkgs}")
                print(f"     Last beli : {last_at}  {last_st}")
                print()
        _sep()
        print("  1. Daftarkan nomor baru")
        print("  2. Edit konfigurasi")
        print("  3. Hapus nomor")
        print("  4. Kelola paket")
        print("  5. Beli sekarang (manual)")
        _sep()
        print(f"  6. {'Hentikan' if mon_on else 'Mulai'} Monitor")
        print(f"  7. 📋 Lihat Log")
        print(f"  8. 📦 Kelola Preset Paket")
        print("  0. Kembali")
        _sep()
        c = input("  Pilihan: ").strip()

        if c == "0": break
        elif c == "1": _register_menu()
        elif c == "2":
            e = _pick_entry(entries, "edit")
            if e: _edit_menu(e)
        elif c == "3":
            e = _pick_entry(entries, "hapus")
            if e:
                if input(f"  Hapus {e['number']}? (y/n): ").strip().lower() == "y":
                    AutoBuyInstance.remove_entry(e["number"])
                    print("  ✅ Dihapus.")
            pause()
        elif c == "4":
            e = _pick_entry(entries, "kelola paket")
            if e: _packages_menu(e["number"])
        elif c == "5":
            e = _pick_entry(entries, "beli")
            if e: _buy_now(e); pause()
        elif c == "6":
            if mon_on: AutoBuyInstance.stop_monitor()
            else:      AutoBuyInstance.start_monitor()
            pause()
        elif c == "7":
            _view_log()
        elif c == "8":
            _presets_menu()
        else:
            print("  ❌ Tidak valid."); pause()
