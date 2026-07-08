import socketserver
import threading
import uuid
from xmlrpc.server import SimpleXMLRPCServer

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
        self.sessions = {}
        self.lock = threading.Lock()

    def join_game(self, player_name):
        player_id = str(uuid.uuid4())[:8]
        session_id = str(uuid.uuid4())[:8]
        with self.lock:
            self.players[player_id] = {"name": player_name, "session_id": session_id}
            self.sessions[session_id] = {
                "player_id": player_id,
                "player_name": player_name,
                "last_city": None,
                "used_cities": [],
                "status": "playing",
                "log": [f"Игра началась! Игрок: {player_name}. Назовите любой город."],
            }
        print(f"Игрок '{player_name}' подключился (id={player_id})")
        return {"player_id": player_id, "session_id": session_id}

    def submit_city(self, player_id, city_input):
        with self.lock:
            player = self.players.get(player_id)
            if not player:
                return {"ok": False, "message": "Игрок не найден"}

            session = self.sessions[player["session_id"]]
            if session["status"] != "playing":
                return {"ok": False, "message": "Игра завершена"}

            city = find_city(city_input)

            if city is None:
                return {"ok": False, "message": f"Города '{city_input}' нет в списке"}

            if city in session["used_cities"]:
                return {"ok": False, "message": f"Город '{city}' уже был назван"}

            if session["last_city"]:
                req = get_required_letter(session["last_city"])
                if city[0].lower().replace("ё", "е") != req:
                    return {"ok": False, "message": f"Город должен начинаться на '{req.upper()}'"}

            session["used_cities"].append(city)
            session["last_city"] = city
            next_letter = get_required_letter(city)
            session["log"].append(f"✓ {city}  →  следующий на '{next_letter.upper()}'")

            print(f"[{player['name']}] {city}")
            return {"ok": True, "message": f"Принято! Следующий город на '{next_letter.upper()}'"}

    def get_state(self, player_id):
        with self.lock:
            player = self.players.get(player_id)
            if not player:
                return {"status": "error", "message": "Игрок не найден"}
            session = self.sessions[player["session_id"]]
            return {
                "status": session["status"],
                "last_city": session["last_city"] or "",
                "used_count": len(session["used_cities"]),
                "log": session["log"][-5:],
            }


server_instance = CitiesServer()

server = ThreadedXMLRPCServer(("0.0.0.0", 8001), logRequests=False)
server.register_instance(server_instance)
print("Сервер Городов (одиночный режим) запущен на порту 8001")
server.serve_forever()
