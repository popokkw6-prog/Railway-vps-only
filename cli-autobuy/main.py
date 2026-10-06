from dotenv import load_dotenv
load_dotenv()

import sys
from app.menus.util import clear_screen, pause
from app.service.auth import AuthInstance
from app.service.autobuy import AutoBuyInstance
from app.service.git import check_for_updates
from app.menus.account import show_account_menu
from app.menus.autobuy import show_autobuy_menu
from app.menus.autorefresh import show_autorefresh_menu
from app.client.engsel import get_balance, get_tiering_info
from datetime import datetime

WIDTH = 58

def show_main_menu(profile):
    clear_screen()
    print("=" * WIDTH)
    exp = datetime.fromtimestamp(profile["balance_expired_at"]).strftime("%Y-%m-%d")
    print(f"  {profile['number']}  [{profile['subscription_type']}]")
    print(f"  Pulsa: Rp {profile['balance']}  |  Aktif s/d: {exp}")
    print(f"  {profile['point_info']}")
    print("=" * WIDTH)

    ab = "🟢" if AutoBuyInstance.is_monitor_running() else "🔴"
    ar = "🟢" if AutoBuyInstance.is_refresh_running()  else "🔴"
    print(f"  1. Login / Ganti Akun")
    print(f"  2. ⚡ Auto Buy          [{ab}]")
    print(f"  3. 🔄 Auto Refresh Token [{ar}]")
    print(f"  0. Keluar")
    print("=" * WIDTH)

def main():
    while True:
        active_user = AuthInstance.get_active_user()

        if active_user is None:
            selected = show_account_menu()
            if selected:
                AuthInstance.set_active_user(selected)
            continue

        # Ambil info profil untuk header
        try:
            balance       = get_balance(AuthInstance.api_key, active_user["tokens"]["id_token"])
            bal_remaining = balance.get("remaining", 0)
            bal_exp       = balance.get("expired_at", 0)

            point_info = "Points: N/A | Tier: N/A"
            if active_user["subscription_type"] == "PREPAID":
                tiering    = get_tiering_info(AuthInstance.api_key, active_user["tokens"])
                point_info = f"Points: {tiering.get('current_point',0)} | Tier: {tiering.get('tier',0)}"

            profile = {
                "number":            active_user["number"],
                "subscription_type": active_user["subscription_type"],
                "balance":           bal_remaining,
                "balance_expired_at": bal_exp,
                "point_info":        point_info,
            }
        except Exception as e:
            print(f"Gagal ambil profil: {e}")
            pause()
            continue

        show_main_menu(profile)
        choice = input("  Pilihan: ").strip()

        if choice == "1":
            selected = show_account_menu()
            if selected:
                AuthInstance.set_active_user(selected)

        elif choice == "2":
            show_autobuy_menu()

        elif choice == "3":
            show_autorefresh_menu()

        elif choice == "0":
            print("Sampai jumpa!")
            sys.exit(0)

        else:
            print("  Pilihan tidak valid.")
            pause()

if __name__ == "__main__":
    try:
        print("Checking for updates...")
        if check_for_updates():
            pause()

        main()
    except KeyboardInterrupt:
        print("\nKeluar.")
