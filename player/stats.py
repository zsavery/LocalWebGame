class PlayerStats(object):
    def __init__(self, health=100, name=None, skills=None,
                 items=None, items_capacity=16, slots_count=5):
        self.health: int = health
        self.name: str | None = name
        self.skills: list = skills or []
        self.items: dict[str, dict] = items or {}  # always a dict
        self.items_capacity: int = items_capacity  # max distinct item types
        self.slots_count: int = slots_count        # max stack size per item

    def add_item(self, name: str, count: int = 1) -> bool:
        """
        Add an item by name. Stacks up to slots_count per item.
        Respects items_capacity for distinct item types.
        Returns True if any amount was added, False otherwise.
        """
        if count <= 0:
            return False

        if name in self.items:
            current = self.items[name].get("count", 0)
            if current >= self.slots_count:
                return False
            to_add = min(count, self.slots_count - current)
            self.items[name]["count"] = current + to_add
            return to_add > 0

        if len(self.items) >= self.items_capacity:
            return False

        to_add = min(count, self.slots_count)
        self.items[name] = {"name": name, "count": to_add}
        return to_add > 0
