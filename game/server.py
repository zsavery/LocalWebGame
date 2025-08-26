import json  # For encoding/decoding messages between server and client
import socket  # For network communication
import threading  # For handling multiple clients concurrently


from online_player.player import Player
from online_player.player import PlayerStats


class GameServer:
    # Main server class that manages player connections and game logic
    def __init__(self, ip: str, port: int):
        # Initialize the server socket and prepare to accept connections
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Reuse address for quick restarts
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((ip, port))
        self.socket.listen()
        self.players: list[Player] = []
        self.running = True
        self._lock = threading.RLock()

    def handle_player(self, player: Player):
        # Handle communication and commands from a single player
        while player.is_alive() and self.running:
            try:
                if player.connection is None:
                    break  # connection is not available
                data = player.connection.recv(1024)
                if not data:
                    break  # client closed connection
                text = data.decode(errors="ignore").strip()
                if not text:
                    continue
                # Handle multiple newline-separated commands
                for msg in text.splitlines():
                    msg = msg.strip()
                    if msg:
                        self.process_command(player, msg)
            except Exception as e:
                print(e)
                break
        self.remove_player(player)

    def remove_player(self, player: Player):
        # Remove a player from the game and notify others
        with self._lock:
            if player in self.players:
                try:
                    if player.connection is not None:
                        player.connection.close()
                except Exception:
                    pass
                self.players.remove(player)
                print(f"{player.stats.name} has disconnected.")
                self.broadcast(f"{player.stats.name} has left the game.", exclude=None)

    def process_command(self, player: Player, command: str):
        # Interpret and execute commands sent by a player
        cmd = command.strip()
        lower = cmd.lower()

        if lower.startswith("attack"):
            parts = cmd.split(maxsplit=1)
            target_name = parts[1].strip() if len(parts) > 1 else ""
            self.attack(player, target_name)
        elif lower.startswith("move"):
            parts = cmd.split()
            if len(parts) >= 3:
                direction = parts[1]
                distance = parts[2]
                self.move_player(player, direction, distance)
            if len(parts) >= 2:
                direction = parts[1]
                self.move_player(player, direction)
            else:
                player.send("Usage: move <up|down|left|right>")
        elif lower.startswith("shutdown"):
    
            self.shutdown_server()
        else:
            player.send("Unknown command.")

    def move_player(self, player: Player, direction: str, distance: int | float = 1):
        # Move a player in the specified direction and distance, with bounds checking
        current_x, current_y = player.position["x"], player.position["y"]

        moved = player.move(direction, distance)
        if not moved:
            player.send("Invalid direction. Use: up, down, left, right.")
            return

        # Keep movement within inclusive bounds consistent with spawn range
        if not (-100 <= player.position["x"] <= 100 and -100 <= player.position["y"] <= 100):
            player.position["x"], player.position["y"] = current_x, current_y
            player.send("You can't move outside the -100 to 100 range.")
        elif any(
                (p.position["x"] == player.position["x"] and p.position["y"] == player.position["y"])
                for p in self.players if p is not player
        ):
            blocker = next(
                p for p in self.players
                if p is not player and p.position["x"] == player.position["x"] and p.position["y"] == player.position["y"]
            )
            player.send(f"Blocked by {blocker.stats.name}.")
            player.position["x"], player.position["y"] = current_x, current_y
        else:
            player.send(f"Moved {direction} to {player.position['x']} {player.position['y']}.")

    def shutdown_server(self):
        # Gracefully shut down the server and disconnect all players
        print("Shutting down server...")
        self.running = False
        with self._lock:
            for player in list(self.players):
                try:
                    player.send("Server is shutting down.")
                finally:
                    try:
                        if player.connection is not None:
                            player.connection.close()
                    except Exception:
                        pass
            self.players.clear()
        try:
            if self.socket is not None:
                self.socket.close()
        except Exception:
            pass

    def attack(self, player: Player, target_name: str):
        # Handle attack command: check if target is valid and apply damage
        target_name = target_name.strip()
        print(target_name)
        if not target_name:
            player.send("Usage: attack <playerName>")
            return

        with self._lock:
            target = next((p for p in self.players if p is not player and p.stats.name == target_name), None)

        if not target:
            player.send(f"Target '{target_name}' not found.")
            return

        # Optional: require adjacency (same tile or 4-neighborhood)
        same_tile = (player.position["x"] == target.position["x"] and player.position["y"] == target.position["y"])
        adjacent = (
                abs(player.position["x"] - target.position["x"]) + abs(player.position["y"] - target.position["y"]) == 1
        )
        if not (same_tile or adjacent):
            player.send(f"{target_name} is out of range.")
            return

        damage = 10
        target.stats.health = max(0, target.stats.health - damage)
        self.broadcast(f"{player.stats.name} hit {target.stats.name} for {damage} damage. "
                       f"HP={target.stats.health}", exclude=None)

        if not target.is_alive():
            self.broadcast(f"{target.stats.name} has been defeated!", exclude=None)
            self.remove_player(target)

    def broadcast(self, message: str, exclude: Player | None = None, encoding: str = "utf-8"):
        # Send a message to all connected players (except optionally one)
        for p in list(self.players):
            if exclude is not None and p is exclude:
                continue
            try:
                p.send(message, encoding=encoding)
            except Exception as e:
                print(f"Failed to send to {getattr(p.stats, 'name', 'unknown')}: {e}")
                self.remove_player(p)

    def listen_for_shutdown_command(self):
        # Listen for 'shutdown' command from the server console to stop the server
        # Simple console listener: type 'shutdown' to stop the server
        try:
            while self.running:
                try:
                    line = input().strip().lower()
                except EOFError:
                    break
                if line == "shutdown":
                    self.shutdown_server()
                    break
        except Exception as e:
            print(f"Shutdown listener error: {e}")

    def run(self):
        # Main loop: accept new connections, validate usernames, and start player threads
        print("Server running...")
        threading.Thread(target=self.listen_for_shutdown_command, daemon=True).start()
        while self.running:
            try:
                client, address = self.socket.accept()
                try:
                    payload = client.recv(1024)
                    if not payload:
                        client.close()
                        continue
                    stats = json.loads(payload.decode(errors="ignore"))
                except Exception:
                    client.close()
                    continue

                name = (stats.get("name") or "").strip()
                if not name:
                    client.send("Invalid name.".encode())
                    client.close()
                    continue

                with self._lock:
                    if name in [p.stats.name for p in self.players]:
                        client.send(f"USERNAME_TAKEN\nName: {name} already in use. Please reconnect with a different name.".encode())
                        client.close()
                        continue

                    player = Player(client, address, PlayerStats(name=name))
                    self.players.append(player)

                print(f"Player connected: {address} as '{name}'")
                try:
                    player.send(f"Welcome, {name}!")
                except Exception:
                    pass

                threading.Thread(target=self.handle_player, args=(player,), daemon=True).start()
            except OSError:
                break  # Occurs when server.close() is called


if __name__ == "__main__":
    # Entry point: start the game server on localhost:8580
    server = GameServer("localhost", 8580)
    server.run()