import json
import socket
import threading

from player.Player import Player
from player.stats import PlayerStats


class GameServer:
    def __init__(self, ip, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((ip, port))
        self.socket.listen()
        self.players = []
        self.running = True

    def handle_player(self, player: Player):
        while player.is_alive() and self.running:
            try:
                data = player.connection.recv(1024)
                if not data:
                    break  # client closed connection
                msg = data.decode(errors="ignore").strip()
                if msg:
                    self.process_command(player, msg)
            except Exception as e:
                print(e)
                break
        self.remove_player(player)

    def remove_player(self, player: Player):
        if player in self.players:
            try:
                player.connection.close()
            except Exception:
                pass
            self.players.remove(player)
            print(f"{player.stats.name} has disconnected.")

    def process_command(self, player: Player, command: str):
        cmd = command.strip()
        lower = cmd.lower()

        if lower.startswith("attack"):
            parts = cmd.split(maxsplit=1)
            target = parts[1] if len(parts) > 1 else ""
            self.attack(player, target)
        elif lower.startswith("move"):
            parts = cmd.split()
            if len(parts) >= 2:
                direction = parts[1]
                self.move_player(player, direction)
            else:
                player.send("Usage: move <up|down|left|right>")
        elif lower.startswith("shutdown"):
            self.shutdown_server()
        else:
            player.send("Unknown command.")

    def move_player(self, player: Player, direction, distance=1):
        current_x, current_y = player.position["x"], player.position["y"]

        moved = player.move(direction, distance)
        if not moved:
            player.send("Invalid direction. Use: up, down, left, right.")
            return

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
        print("Shutting down server...")
        self.running = False
        for player in list(self.players):
            try:
                player.send("Server is shutting down.")
            finally:
                try:
                    player.connection.close()
                except Exception:
                    pass
        try:
            self.socket.close()
        except Exception:
            pass

    def attack(self, player: Player, target: str):
        # TODO: locate target, apply damage, and broadcast results
        pass

    def broadcast(self, message: str, exclude: Player | None = None, encoding: str = "utf-8"):
        for p in list(self.players):
            if exclude is not None and p is exclude:
                continue
            try:
                p.send(message, encoding=encoding)
            except Exception as e:
                print(f"Failed to send to {getattr(p.stats, 'name', 'unknown')}: {e}")
                self.remove_player(p)

    def listen_for_shutdown_command(self):
        pass

    def run(self):
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

                if stats.get("name") in [p.stats.name for p in self.players]:
                    client.send("Name already in use. Please reconnect with a different name.".encode())
                    client.close()
                    continue

                player = Player(client, address, PlayerStats(name=stats.get("name")))
                self.players.append(player)
                print(f"Player connected: {address} with stats {stats}")
                threading.Thread(target=self.handle_player, args=(player,), daemon=True).start()
            except OSError:
                break  # Occurs when server.close() is called