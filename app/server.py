#
# Серверное приложение для соединений
#
import asyncio
from asyncio import transports

logins = []
messages = []


class ServerProtocol(asyncio.Protocol):
    login: str = None
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server

    def data_received(self, data: bytes):
        print(data)

        decoded = data.decode()

        if self.login is not None:
            self.send_message(decoded)
        else:
            if decoded.startswith("login:"):
                self.login = decoded.replace("login:", "").replace("\r\n", "")
                if self.login not in logins:
                    logins.append(self.login)
                    self.send_history()
                    self.transport.write(
                        f"Привет, {self.login}!\n".encode()
                    )
                else:
                    self.transport.write(
                        f"Логин {self.login} занят, попробуйте другой\n".encode()
                    )
                    self.connection_terminate()
            else:
                self.transport.write("Неправильный логин\n".encode())

    def connection_made(self, transport: transports.Transport):
        self.server.clients.append(self)
        self.transport = transport
        print("Пришел новый клиент")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Клиент вышел")

    def connection_terminate(self):
        self.transport.close()

    def send_message(self, content: str):
        message = f"{self.login}: {content}\n"
        messages.append(message)

        for user in self.server.clients:
            user.transport.write(message.encode())

    def send_history(self):
        if len(messages) > 10:
            self.transport.write("...".encode())
        for message in messages[-10:]:
            self.transport.write(message.encode())


class Server:
    clients: list

    def __init__(self):
        self.clients = []

    def build_protocol(self):
        return ServerProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.build_protocol,
            '127.0.0.1',
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()

try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
