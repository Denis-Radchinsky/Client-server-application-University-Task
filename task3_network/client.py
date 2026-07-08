import xmlrpc.client


def get_required_letter(city):
    n = city.strip().lower().replace("ё", "е")
    last = n[-1]
    if last in ("ь", "ъ"):
        return n[-2]
    return last


def main():
    host = input("IP сервера (Enter = localhost): ").strip() or "localhost"
    proxy = xmlrpc.client.ServerProxy(f"http://{host}:8001/")

    name = input("Ваше имя: ").strip()
    result = proxy.join_game(name)
    player_id = result["player_id"]

    print(f"\nПодключились к игре! Ваш ID: {player_id}")
    print("Введите 'выход' для завершения.\n")

    state = proxy.get_state(player_id)
    for msg in state["log"]:
        print(msg)

    while True:
        state = proxy.get_state(player_id)

        last_city = state["last_city"]
        if last_city:
            req = get_required_letter(last_city)
            print(f"\nПоследний город: {last_city}  |  Ваш город на '{req.upper()}':")
        else:
            print("\nНазовите любой город:")

        city_input = input(">>> ").strip()

        if city_input.lower() == "выход":
            print("До свидания!")
            break

        result = proxy.submit_city(player_id, city_input)
        if result["ok"]:
            print(f"  ✓ {result['message']}")
            print(f"  Всего городов названо: {proxy.get_state(player_id)['used_count']}")
        else:
            print(f"  ✗ {result['message']}")


if __name__ == "__main__":
    main()
