import random

from player.stats import PlayerStats


class Player:
    def __init__(self, connection=None, address=None, stats: PlayerStats | None = None):
        self.connection = connection
        self.address = address
        self.stats: PlayerStats = stats if isinstance(stats, PlayerStats) else PlayerStats()
        self.position = {"x": random.randint(-100, 100),
                         "y": random.randint(-100, 100)}

    def send(self, command: str, encoding: str = "utf-8") -> bool:
        if not self.connection:
            return False
        try:
            self.connection.send(command.encode(encoding))
            return True
        except Exception:
            return False

    def is_alive(self) -> bool:
        return self.stats.health > 0

    def move(self, command: str, distance: int | float = 1) -> bool:
        if not isinstance(command, str):
            return False

        direction = command.lower()
        if direction == "right":
            self.position["x"] += distance
        elif direction == "left":
            self.position["x"] -= distance
        elif direction == "up":
            self.position["y"] += distance
        elif direction == "down":
            self.position["y"] -= distance
        else:
            return False
        return True

    def learn_skill(self, skill) -> bool:
        if skill in self.stats.skills:
            return False
        if len(self.stats.skills) >= 4:
            return False
        self.stats.skills.append(skill)
        return True

    def add_item(self, item_name: str, count: int = 1) -> bool:
        return self.stats.add_item(item_name, count)

    def attack(self, msg: str = "Slash") -> str:
        text = f"Player {self.stats.name} used {msg} to attack!"
        print(text)
        return text
