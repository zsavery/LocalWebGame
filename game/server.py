import socket
import threading

from player.Player import Player

class GameServer:
    def __init__(self, ip, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind(ip, port)
        self.socket.listen()
        self.players = []
        self.running = True

    def handle_player(self, player:Player):
        while player.is_alive() and self.running:
            try:
                msg = player.connection.recv(1024).decode()
            except Exception as e:
                print(e)
                break
        self.remove_player(player)

    def remove_player(self, player:Player):
        if player in self.players:
            player.connection.close()
            self.players.remove(player)
            print(f"{player.stats.name} has disconnected.")


