from transport.client import Client
from transport.vehicle import Vehicle


class TransportCompany:
    def __init__(self, name: str):
        self.name = name
        self.vehicles = []
        self.clients = []


    def add_vehicle(self, vehicle):
        if not isinstance(vehicle, Vehicle):
            raise TypeError("vehicle должен быть экземпляром Vehicle или его наследника")
        self.vehicles.append(vehicle)

    def list_vehicles(self):
        return self.vehicles

    def add_client(self, client):
        if not isinstance(client, Client):
            raise TypeError("client должен быть экземпляром Client")
        self.clients.append(client)

    def _reset_vehicle_loads(self):
        for v in self.vehicles:
            v.current_load = 0
            v.clients_list = []

    def optimize_cargo_distribution(self):
        if not self.vehicles:
            print(" Нет транспорта для распределения.")
            return

        if not self.clients:
            print(" Нет клиентов для распределения.")
            return

        self._reset_vehicle_loads()

        sorted_clients = sorted(
            self.clients,
            key=lambda c: (not c.is_vip, -c.cargo_weight)
        )

        sorted_vehicles = sorted(self.vehicles, key=lambda v: -v.capacity)

        for client in sorted_clients:
            remaining = client.cargo_weight  

            for vehicle in sorted_vehicles:
                if remaining <= 0:
                    break

                free_space = vehicle.capacity - vehicle.current_load
                if free_space <= 0:
                    continue


                to_load = min(remaining, free_space)


                part_client = Client(
                    name=f"{client.name}",
                    cargo_weight=to_load,
                    is_vip=client.is_vip
                )

                vehicle.load_cargo(part_client)
                remaining -= to_load

            if remaining > 0:
                print(f" Клиент {client.name}: не удалось распределить {remaining} т.")

        return sorted_vehicles
