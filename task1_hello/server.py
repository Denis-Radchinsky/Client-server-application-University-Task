from xmlrpc.server import SimpleXMLRPCServer


def say_hello(name):
    return f"Привет, {name}! Это ответ от удалённого сервера."


server = SimpleXMLRPCServer(("localhost", 8000), logRequests=False)
print("Сервер HelloWorld запущен на порту 8000. Ожидание клиентов...")
server.register_function(say_hello, "say_hello")
server.serve_forever()
