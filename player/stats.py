class PlayerStats(object):
    def __init__(self, health=100, name=None, skills=None,
                 items=None, items_capacity=16,slots_count=5):
        self.health:str = health
        self.name:str = name
        self.skills:list = skills
        self.items:dict = items
        self.items_capacity:int = items_capacity
        self.slots_count:int = slots_count
