import json
import socket
import threading

class GameClient:
    def __init__(self, host: str, port: int, name: str, encoding: str = "utf-8"):
        self.host = host
        self.port = port
        self.name = name
        self.encoding = encoding
        self.sock: socket.socket | None = None
        self.running = False
        self.receiver_thread: threading.Thread | None = None

    @staticmethod
    def prompt_username() -> str:
        while True:
            name = input("Enter your username: ").strip()
            if name:
                return name
            print("Username cannot be empty.")

    def connect(self) -> bool:
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            # Initial handshake: send stats JSON with name
            payload = json.dumps({"name": self.name}).encode(self.encoding)
            self.sock.sendall(payload)
            # Wait for server response to username
            response = self.sock.recv(1024)
            if not response:
                print("No response from server.")
                self.close()
                return False
            msg = response.decode(self.encoding, errors="ignore").strip()
            if msg.startswith("USERNAME_TAKEN"):
                print("Someone else owns this username. Connection closed.")
                self.close()
                return False
            self.running = True
            self.receiver_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.receiver_thread.start()
            return True
        except Exception as e:
            print(f"Failed to connect: {e}")
            self.close()
            return False

    def _receive_loop(self):
        assert self.sock is not None
        try:
            while self.running:
                data = self.sock.recv(1024)
                if not data:
                    print("Disconnected from server.")
                    self.running = False
                    break
                msg = data.decode(self.encoding, errors="ignore")
                if msg:
                    # Server may send multiple messages in one packet; print as-is
                    print(f"\n[SERVER] {msg.strip()}")
                    print("> ", end="", flush=True)
        except Exception as e:
            if self.running:
                print(f"\nReceiver error: {e}")
        finally:
            self.running = False

    def send_command(self, cmd: str) -> bool:
        if not self.running or not self.sock:
            print("Not connected.")
            return False
        cmd = cmd.strip()
        if not cmd:
            return False
        try:
            # Append a newline to help human readability; server strips input anyway
            self.sock.sendall((cmd + "\n").encode(self.encoding))
            return True
        except Exception as e:
            print(f"Send failed: {e}")
            self.close()
            return False

    def close(self):
        self.running = False
        try:
            if self.sock:
                try:
                    self.sock.shutdown(socket.SHUT_RDWR)
                except Exception:
                    pass
                self.sock.close()
        finally:
            self.sock = None




if __name__ == "__main__":
    host = "localhost"
    port = 8580
    username = GameClient.prompt_username()
    client = GameClient(host, port, username)

    if client.connect():
        
        try:
            while client.running:
                cmd = input("> ")
                if cmd.lower() in ("quit", "exit", "shutdown"):
                    if cmd.lower() ==  "shutdown":
                        client.send_command(cmd)
                        msg = client.sock.recv(1024).decode()
                        print(msg)
                    break
                client.send_command(cmd)
                
        finally:
            
            client.close()