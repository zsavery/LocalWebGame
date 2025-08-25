import random
import socket


from player.stats import PlayerStats


class Player:
    def __init__(self, connection=None, stats:PlayerStats=PlayerStats()):
        self.connection = connection
        self.address = None
        self.stats = stats
        self.position = {"x": random.randint(-100, 100),
                         "y": random.randint(-100, 100)}

    def send(self, command, encoding="utf-8"):
        self.connection.send(command.encode(encoding))

    def is_alive(self):
        return self.stats.health > 0

    def move(self, command):
        if not isinstance(command, str):
            return

        direction = command.lower()

        match direction:
            case "left":
                self.position["x"]+=1
            case "right":
                self.position["x"]-=1
            case "up":
                self.position["y"]+=1
            case "down":
                self.position["y"]-=1
            case _:
                return

    def learn_skill(self, skill):
        if self.stats.skills.contains(skill):
            return
        if len(self.stats.skills) >= 4:
            return
        self.stats.skills.add(skill)

    def add_item(self, item, count=1):
        if len(self.stats.items) < self.stats.items_capacity :

            return

        if item in self.stats.items.keys():
            if len(self.stats.items[item]) < self.stats.slots_count:
                self.stats.items[item] += count
            return

    def attack(self, msg="Slash"):
        print(f"Plater {self.stats.name} used {msg} to attack!")
