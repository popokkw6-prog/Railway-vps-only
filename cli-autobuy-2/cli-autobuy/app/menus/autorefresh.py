"""
Menu Auto Refresh Token
=======================
Thread terpisah dari Auto Buy.
Refresh token semua nomor di autobuy.json tiap 55 menit.
Jika gagal → skip, tidak hapus nomor.
"""

from app.menus.util import clear_screen, pause
from app.service.autobuy import AutoBuyInstance, TOKEN_REFRESH_INTERVAL_MIN
from app.service.auth import AuthInstance

W = 58

def _sep(): print("─" * W)

def show_autorefresh_menu():
    while True:
        clear_screen()
        print("=" * W)
        print("  🔄 AUTO TOKEN REFRESH")
        print("=" * W)

        is_on   = AutoBuyInstance.is_refresh_running()
        entries = AutoBuyInstance.get_all()

        status_str = "🟢 JALAN" if is_on else "🔴 MATI"
        print(f"  Status   : {status_str}")
        print(f"  Interval : setiap {TOKEN_REFRESH_INTERVAL_MIN} menit")
        print()

        if not entries:
            print("  Tidak ada nomor terdaftar di Auto Buy.")
            print("  Daftarkan nomor dulu via menu Auto Buy.")
        else:
            print("  Nomor yang akan di-refresh:")
            for e in entries:
                aktif = "✅" if e.get("active",True) else "⛔"
                print(f"    {aktif} {e['number']}")

        print()
        _sep()
        if is_on:
            print("  1. Hentikan Auto Refresh")
        else:
            print("  1. Mulai Auto Refresh")
        print("  2. Refresh semua token SEKARANG (manual)")
        print("  0. Kembali")
        _sep()
        c = input("  Pilihan: ").strip()

        if c == "0": break

        elif c == "1":
            if is_on:
                AutoBuyInstance.stop_refresh()
                print("  ✅ Auto Refresh dihentikan.")
            else:
                if not entries:
                    print("  ❌ Tidak ada nomor terdaftar.")
                else:
                    AutoBuyInstance.start_refresh()
                    print("  ✅ Auto Refresh dimulai.")
            pause()

        elif c == "2":
            _manual_refresh_all()

        else:
            print("  ❌ Tidak valid."); pause()


def _manual_refresh_all():
    from app.client.ciam import get_new_token

    entries = AutoBuyInstance.get_all()
    if not entries:
        print("  Tidak ada nomor terdaftar."); pause(); return

    print()
    print("  Refresh token semua nomor...\n")
    success = 0
    fail    = 0

    for entry in entries:
        number = entry["number"]
        rt = next((r for r in AuthInstance.refresh_tokens
                   if r["number"] == number), None)
        if not rt:
            print(f"  [{number}] ⚠ Tidak ada token tersimpan, skip.")
            fail += 1; continue
        try:
            new = get_new_token(
                AuthInstance.api_key,
                rt["refresh_token"],
                rt.get("subscriber_id","")
            )
            if new and "refresh_token" in new:
                rt["refresh_token"] = new["refresh_token"]
                AuthInstance.write_tokens_to_file()
                if (AuthInstance.active_user and
                        AuthInstance.active_user["number"] == number):
                    AuthInstance.active_user["tokens"] = new
                print(f"  [{number}] ✅ Berhasil.")
                success += 1
            else:
                print(f"  [{number}] ⚠ Gagal (response kosong), skip.")
                fail += 1
        except Exception as e:
            print(f"  [{number}] ❌ Error: {e}")
            fail += 1

    print()
    print(f"  Selesai — ✅ {success} berhasil  |  ❌ {fail} gagal")
    pause()
