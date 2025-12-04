class Client:
    def __init__(self, name: str, cargo_weight: float, is_vip: bool = False):
        self.name = name
        self.cargo_weight = cargo_weight
        self.is_vip = is_vip

    def __repr__(self):
        return f"Client(name='{self.name}', cargo_weight={self.cargo_weight}, is_vip={self.is_vip})"