import xmlrpc.client

host = input("Введите IP сервера (Enter = localhost): ").strip() or "localhost"
proxy = xmlrpc.client.ServerProxy(f"http://{host}:8000/")

name = input("Введите ваше имя: ").strip()
response = proxy.say_hello(name)
print(f"Ответ сервера: {response}")
