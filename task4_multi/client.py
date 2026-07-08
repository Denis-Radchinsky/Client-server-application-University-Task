import time
import xmlrpc.client


def get_required_letter(city):
    n = city.strip().lower().replace("ё", "е")
    last = n[-1]
    if last in ("ь", "ъ"):
        return n[-2]
    return last


def clear_and_print_log(log, header=""):
    if header:
        print(f"\n{'=' * 45}")
        print(header)
        print("=" * 45)
    for line in log:
        print(f"  {line}")


def main():
    host = input("IP сервера (Enter = localhost): ").strip() or "localhost"
    proxy = xmlrpc.client.ServerProxy(f"http://{host}:8002/")

    name = input("Ваше имя: ").strip()
    player_id = proxy.join_lobby(name)
    print(f"\nВы в лобби! Ваш ID: {player_id}")
    print("Ожидание других игроков...\n")

    last_log_len = 0

    while True:
        try:
            state = proxy.get_state(player_id)
        except Exception as e:
            print(f"Ошибка соединения: {e}")
            time.sleep(2)
            continue

        status = state["status"]

        if status == "lobby":
            print(f"\r{state['message']}", end="", flush=True)
            time.sleep(2)
            continue

        log = state.get("log", [])
        if len(log) > last_log_len:
            for line in log[last_log_len:]:
                print(f"  {line}")
            last_log_len = len(log)

        if status in ("finished", "eliminated"):
            winner = state.get("winner", "")
            if status == "eliminated":
                print("\n  Вы выбыли из игры.")
            if winner:
                print(f"\n{'=' * 45}")
                print(f"  ИГРА ОКОНЧЕНА. Победитель: {winner}")
                print("=" * 45)
            else:
                print("\n  Игра окончена.")
            break

        if status == "playing":
            active = state.get("active_players", [])
            last_city = state.get("last_city", "")
            time_left = state.get("time_left", 0)
            current_player = state.get("current_player", "")
            is_my_turn = state.get("is_my_turn", False)

            if is_my_turn:
                if last_city:
                    req = get_required_letter(last_city)
                    print(f"\n>>> ВАШ ХОД! Последний город: {last_city}  |  Нужна буква: '{req.upper()}'")
                else:
                    print("\n>>> ВАШ ХОД! Назовите любой город:")
                print(f"    Осталось времени: {time_left}с  |  Игроки: {', '.join(active)}")

                city_input = input("    Город: ").strip()
                if not city_input:
                    continue

                try:
                    result = proxy.submit_city(player_id, city_input)
                    if result["ok"]:
                        print(f"    ✓ {result['message']}")
                    else:
                        print(f"    ✗ {result['message']}")
                except Exception as e:
                    print(f"    Ошибка: {e}")
            else:
                print(f"\r  Ход: {current_player} (осталось {time_left}с)...", end="", flush=True)
                time.sleep(2)


if __name__ == "__main__":
    main()
