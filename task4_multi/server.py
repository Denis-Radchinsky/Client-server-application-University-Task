import random
import socketserver
import threading
import time
import uuid
from xmlrpc.server import SimpleXMLRPCServer

LOBBY_MIN = 2
LOBBY_MAX = 5
TURN_TIMEOUT = 60

CITIES = {
    "Абакан", "Азов", "Александров", "Алексин", "Альметьевск",
    "Анадырь", "Ангарск", "Апатиты", "Арзамас", "Армавир",
    "Артём", "Архангельск", "Астрахань", "Ачинск",
    "Балаково", "Балашиха", "Барнаул", "Батайск", "Белгород",
    "Бердск", "Берёзники", "Биробиджан", "Бийск", "Благовещенск",
    "Братск", "Брянск", "Бузулук", "Белово",
    "Великий Новгород", "Вологда", "Волгоград", "Волгодонск",
    "Волжский", "Воркута", "Воронеж", "Воткинск", "Выборг",
    "Гатчина", "Глазов", "Грозный", "Губкин",
    "Дербент", "Дзержинск", "Димитровград", "Дмитров", "Долгопрудный",
    "Ейск", "Екатеринбург", "Елабуга", "Елец", "Ессентуки",
    "Жуковский",
    "Зеленодольск", "Златоуст",
    "Иваново", "Ижевск", "Иркутск", "Искитим", "Ишим",
    "Йошкар-Ола",
    "Казань", "Калининград", "Калуга", "Каменск-Уральский",
    "Камышин", "Канск", "Каспийск", "Кемерово", "Кинешма",
    "Кириши", "Киров", "Кирово-Чепецк", "Кисловодск",
    "Клин", "Ковров", "Коломна", "Копейск", "Королёв",
    "Кострома", "Котлас", "Краснодар", "Красногорск",
    "Красноярск", "Кропоткин", "Курган", "Курск",
    "Лабытнанги", "Ленинск-Кузнецкий", "Липецк", "Лиски", "Люберцы",
    "Магадан", "Магнитогорск", "Майкоп", "Малоярославец",
    "Махачкала", "Миасс", "Минеральные Воды", "Мирный",
    "Мичуринск", "Мончегорск", "Москва", "Муром", "Мурманск", "Мытищи",
    "Набережные Челны", "Надым", "Назрань", "Нальчик",
    "Находка", "Нефтекамск", "Нефтеюганск",
    "Нижневартовск", "Нижнекамск", "Нижний Новгород", "Нижний Тагил",
    "Новокузнецк", "Новокуйбышевск", "Новомосковск",
    "Новороссийск", "Новосибирск", "Новотроицк", "Новочеркасск",
    "Новый Уренгой", "Норильск", "Ноябрьск",
    "Обнинск", "Одинцово", "Омск", "Орёл", "Оренбург", "Орск",
    "Пенза", "Первоуральск", "Пермь", "Петрозаводск",
    "Петропавловск-Камчатский", "Подольск", "Прокопьевск", "Псков",
    "Пятигорск",
    "Раменское", "Ростов-на-Дону", "Рубцовск", "Рыбинск", "Рязань",
    "Салават", "Салехард", "Самара", "Саранск", "Саратов",
    "Сарапул", "Саров", "Северодвинск", "Серов", "Серпухов",
    "Симферополь", "Смоленск", "Сочи", "Соликамск",
    "Ставрополь", "Стерлитамак", "Сургут", "Сыктывкар",
    "Санкт-Петербург",
    "Таганрог", "Тамбов", "Тверь", "Тихвин",
    "Тобольск", "Тольятти", "Томск", "Тула", "Тюмень",
    "Улан-Удэ", "Ульяновск", "Уссурийск", "Усть-Илимск", "Уфа", "Ухта",
    "Хабаровск", "Хасавюрт", "Химки",
    "Чайковский", "Чебоксары", "Чита", "Черемхово", "Череповец",
    "Черняховск", "Челябинск",
    "Шадринск", "Шахты", "Шуя",
    "Щёлково",
    "Электросталь", "Элиста", "Энгельс",
    "Южно-Сахалинск",
    "Якутск", "Ярославль",
}

CITIES_NORMALIZED = {c.lower().replace("ё", "е"): c for c in CITIES}


def normalize(s):
    return s.strip().lower().replace("ё", "е")


def get_required_letter(city):
    n = normalize(city)
    last = n[-1]
    if last in ("ь", "ъ"):
        return n[-2]
    return last


def find_city(user_input):
    return CITIES_NORMALIZED.get(normalize(user_input))


class ThreadedXMLRPCServer(socketserver.ThreadingMixIn, SimpleXMLRPCServer):
    pass


class CitiesServer:
    def __init__(self):
        self.players = {}
        self.lobby = []
        self.sessions = {}
        self.lock = threading.Lock()

        bg = threading.Thread(target=self._background_loop, daemon=True)
        bg.start()

    def join_lobby(self, player_name):
        player_id = str(uuid.uuid4())[:8]
        with self.lock:
            self.players[player_id] = {"name": player_name, "session_id": None}
            self.lobby.append(player_id)
            pos = len(self.lobby)
        print(f"[ЛОББИ] '{player_name}' (id={player_id}) — в очереди: {pos} чел.")
        return player_id

    def submit_city(self, player_id, city_input):
        with self.lock:
            player = self.players.get(player_id)
            if not player or not player["session_id"]:
                return {"ok": False, "message": "Вы не в игре"}

            session = self.sessions[player["session_id"]]
            if session["status"] != "playing":
                return {"ok": False, "message": "Игра завершена"}

            active = session["active_players"]
            if not active:
                return {"ok": False, "message": "Нет активных игроков"}

            current_id = active[session["current_idx"] % len(active)]
            if current_id != player_id:
                return {"ok": False, "message": "Сейчас не ваш ход"}

            city = find_city(city_input)
            if city is None:
                return {"ok": False, "message": f"Города '{city_input}' нет в списке"}

            if city in session["used_cities"]:
                return {"ok": False, "message": f"Город '{city}' уже был назван"}

            if session["last_city"]:
                req = get_required_letter(session["last_city"])
                if city[0].lower().replace("ё", "е") != req:
                    return {"ok": False, "message": f"Нужен город на '{req.upper()}'"}

            session["used_cities"].add(city)
            session["last_city"] = city
            next_letter = get_required_letter(city)
            session["log"].append(f"{session['player_names'][player_id]}: {city}")

            session["current_idx"] = (session["current_idx"] + 1) % len(active)
            session["turn_start"] = time.time()
            next_id = active[session["current_idx"]]
            session["log"].append(f"Ход: {session['player_names'][next_id]} (город на '{next_letter.upper()}')")

            print(f"[Сессия {session['id'][:4]}] {session['player_names'][player_id]}: {city}")
            return {"ok": True, "message": f"Принято! Следующий город на '{next_letter.upper()}'"}

    def get_state(self, player_id):
        with self.lock:
            player = self.players.get(player_id)
            if not player:
                return {"status": "error", "message": "Игрок не найден"}

            if not player["session_id"]:
                lobby_pos = self.lobby.index(player_id) + 1 if player_id in self.lobby else 0
                return {
                    "status": "lobby",
                    "lobby_size": len(self.lobby),
                    "lobby_pos": lobby_pos,
                    "message": f"Ожидание игроков ({len(self.lobby)}/{LOBBY_MIN} мин.)...",
                }

            session = self.sessions[player["session_id"]]
            active = session["active_players"]

            if session["status"] == "finished":
                eliminated = player_id in session["eliminated"]
                return {
                    "status": "finished" if not eliminated else "eliminated",
                    "winner": session["winner"] or "",
                    "log": session["log"][-10:],
                    "active_players": [],
                    "last_city": session["last_city"] or "",
                    "is_my_turn": False,
                    "current_player": "",
                    "time_left": 0,
                }

            if player_id in session["eliminated"]:
                return {
                    "status": "eliminated",
                    "winner": session["winner"] or "",
                    "log": session["log"][-10:],
                    "active_players": [session["player_names"][pid] for pid in active],
                    "last_city": session["last_city"] or "",
                    "is_my_turn": False,
                    "current_player": "",
                    "time_left": 0,
                }

            current_id = active[session["current_idx"] % len(active)] if active else ""
            time_left = max(0, TURN_TIMEOUT - int(time.time() - session["turn_start"]))

            return {
                "status": "playing",
                "is_my_turn": current_id == player_id,
                "current_player": session["player_names"].get(current_id, ""),
                "last_city": session["last_city"] or "",
                "active_players": [session["player_names"][pid] for pid in active],
                "time_left": time_left,
                "log": session["log"][-10:],
                "winner": "",
            }

    def _create_session(self, player_ids):
        session_id = str(uuid.uuid4())[:8]
        random.shuffle(player_ids)
        names = {pid: self.players[pid]["name"] for pid in player_ids}

        session = {
            "id": session_id,
            "active_players": list(player_ids),
            "player_names": names,
            "eliminated": set(),
            "current_idx": 0,
            "last_city": None,
            "used_cities": set(),
            "turn_start": time.time(),
            "status": "playing",
            "winner": None,
            "log": [],
        }
        order = " → ".join(names[pid] for pid in player_ids)
        session["log"].append(f"Игра началась! Порядок: {order}")
        session["log"].append(f"Ход: {names[player_ids[0]]} — назовите любой город")

        self.sessions[session_id] = session
        for pid in player_ids:
            self.players[pid]["session_id"] = session_id

        print(f"[СЕССИЯ {session_id[:4]}] Создана: {order}")

    def _background_loop(self):
        while True:
            time.sleep(1)
            with self.lock:
                if len(self.lobby) >= LOBBY_MIN:
                    count = min(LOBBY_MAX, len(self.lobby))
                    batch = self.lobby[:count]
                    self.lobby = self.lobby[count:]
                    self._create_session(batch)

                now = time.time()
                for session in self.sessions.values():
                    if session["status"] != "playing":
                        continue
                    active = session["active_players"]
                    if not active:
                        session["status"] = "finished"
                        continue

                    elapsed = now - session["turn_start"]
                    if elapsed <= TURN_TIMEOUT:
                        continue

                    idx = session["current_idx"] % len(active)
                    out_id = active.pop(idx)
                    session["eliminated"].add(out_id)
                    out_name = session["player_names"][out_id]
                    session["log"].append(f"⏰ {out_name} выбыл — время вышло")
                    print(f"[Сессия {session['id'][:4]}] {out_name} выбыл по таймауту")

                    remaining = len(active)
                    if remaining <= 1:
                        session["status"] = "finished"
                        if remaining == 1:
                            winner_id = active[0]
                            session["winner"] = session["player_names"][winner_id]
                            session["log"].append(f"🏆 Победитель: {session['winner']}!")
                            print(f"[Сессия {session['id'][:4]}] Победитель: {session['winner']}")
                        else:
                            session["log"].append("Все игроки выбыли. Нет победителя.")
                    else:
                        session["current_idx"] = idx % remaining
                        session["turn_start"] = now
                        next_id = active[session["current_idx"]]
                        next_name = session["player_names"][next_id]
                        req = get_required_letter(session["last_city"]) if session["last_city"] else "?"
                        session["log"].append(f"Ход: {next_name} (город на '{req.upper()}')")


server_instance = CitiesServer()

server = ThreadedXMLRPCServer(("0.0.0.0", 8002), logRequests=False)
server.register_instance(server_instance)
print(f"Сервер Городов (мультиплеер) запущен на порту 8002")
print(f"Игра начнётся при {LOBBY_MIN}-{LOBBY_MAX} игроках в лобби. Таймаут хода: {TURN_TIMEOUT}с")
server.serve_forever()
