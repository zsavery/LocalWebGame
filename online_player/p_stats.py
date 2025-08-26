class PlayerStats(object):
    """
    Stores stats and inventory for a player, including health, name, skills, and items.
    """
    def __init__(self, health=100, name=None, skills=None,
                 items=None, items_capacity=16, slots_count=5):
        self.health: int = health  # Player's health points
        self.name: str | None = name  # Player's name
        self.skills: list = skills or []  # List of skills the player knows
        self.items: dict[str, dict] = items or {}  # Inventory: item name -> item info
        self.items_capacity: int = items_capacity  # Max number of distinct item types
        self.slots_count: int = slots_count        # Max stack size per item type

    def add_item(self, name: str, count: int = 1) -> bool:
        """
        Add an item to the player's inventory.
        - Stacks up to slots_count per item type.
        - Respects items_capacity for distinct item types.
        Returns True if any amount was added, False otherwise.
        """
        if count <= 0:
            return False

        # If item already exists, try to stack more
        if name in self.items:
            current = self.items[name].get("count", 0)
            if current >= self.slots_count:
                return False  # Can't add more, stack is full
            to_add = min(count, self.slots_count - current)
            self.items[name]["count"] = current + to_add
            return to_add > 0

        # If inventory is full, can't add new item type
        if len(self.items) >= self.items_capacity:
            return False

        # Add new item type
        to_add = min(count, self.slots_count)
        self.items[name] = {"name": name, "count": to_add}
        return to_add > 0
