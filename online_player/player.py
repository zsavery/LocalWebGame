import random  # Used to randomly assign player starting positions

from online_player.p_stats import PlayerStats  # Import the PlayerStats class

# The Player class represents a player in the game, including their connection, stats, and position.
class Player:
    def __init__(self, connection=None, address=None, stats: PlayerStats | None = None):
        self.connection = connection  # Network connection to the client
        self.address = address        # Client's address (IP, port)
        # Use provided stats or create new PlayerStats
        self.stats: PlayerStats = stats if isinstance(stats, PlayerStats) else PlayerStats()
        # Random starting position within bounds
        self.position = {"x": random.randint(-100, 100),
                         "y": random.randint(-100, 100)}

    def send(self, command: str, encoding: str = "utf-8") -> bool:
        """
        Send a message to the player's client over the network.
        Returns True if successful, False otherwise.
        """
        if not self.connection:
            return False
        try:
            self.connection.send(command.encode(encoding))
            return True
        except Exception:
            return False

    def is_alive(self) -> bool:
        """
        Check if the player is alive (health > 0).
        """
        return self.stats.health > 0

    def move(self, command: str, distance: int | float = 1) -> bool:
        """
        Move the player in the specified direction by the given distance.
        Returns True if the direction is valid, False otherwise.
        """
        direction = command.lower()
        if direction == "right":
            self.position["x"] = int(self.position["x"] + distance)
        elif direction == "left":
            self.position["x"] = int(self.position["x"] - distance)
        elif direction == "up":
            self.position["y"] = int(self.position["y"] + distance)
        elif direction == "down":
            self.position["y"] = int(self.position["y"] - distance)
        else:
            return False
        return True

    def learn_skill(self, skill) -> bool:
        """
        Add a new skill to the player if not already known and if there's space.
        Returns True if the skill was added, False otherwise.
        """
        if skill in self.stats.skills:
            return False
        if len(self.stats.skills) >= 4:
            return False
        self.stats.skills.append(skill)
        return True

    def add_item(self, item_name: str, count: int = 1) -> bool:
        """
        Add an item to the player's inventory using PlayerStats logic.
        """
        return self.stats.add_item(item_name, count)

    def attack(self, msg: str = "Slash") -> str:
        """
        Simulate an attack and return a message describing the action.
        """
        text = f"Player {self.stats.name} used {msg} to attack!"
        print(text)
        return text
