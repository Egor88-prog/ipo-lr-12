import uuid
from .client import Client

class Vehicle:
    def __init__(self, capacity: float):
        # Генерируем уникальный ID транспорта
        self.vehicle_id = str(uuid.uuid4())
        
        # Атрибуты
        self.capacity = capacity
        self.current_load = 0.0
        self.clients_list = []

    def load_cargo(self, client):
        # Валидация типа
        if not hasattr(client, "cargo_weight") or not hasattr(client, "name"):
            raise TypeError("Аргумент client должен быть объектом класса Client или иметь соответствующие атрибуты.")
        
        # Проверка превышения грузоподъёмности
        if self.current_load + client.cargo_weight > self.capacity:
            raise ValueError("Невозможно загрузить: превышение грузоподъёмности транспортного средства.")

        # Загрузка
        self.current_load += client.cargo_weight
        self.clients_list.append(client)

    def __str__(self):
        return (f"Vehicle ID: {self.vehicle_id}\n"
                f"Capacity: {self.capacity} t\n"
                f"Current load: {self.current_load} t")
    
class Truck(Vehicle):
    def __init__(self, capacity: float, color: str):
        super().__init__(capacity)
        self.color = color

    def __str__(self):
        return (f"Truck ({self.color}) | ID: {self.vehicle_id} | "
                f"Capacity: {self.capacity}t | Load: {self.current_load}t")



class Train(Vehicle):
    def __init__(self, capacity: float, number_of_cars: int):
        super().__init__(capacity)
        self.number_of_cars = number_of_cars

    def __str__(self):
        return (f"Train ({self.number_of_cars} cars) | ID: {self.vehicle_id} | "
                f"Capacity: {self.capacity}t | Load: {self.current_load}t")