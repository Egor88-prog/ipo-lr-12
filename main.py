from transport.client import Client
from transport.vehicle import Truck, Train
from transport.transportcompany import TransportCompany

def menu():
    company = TransportCompany("LogiCorp")

    while True:
        print("1. Добавить клиента")
        print("2. Добавить транспорт")
        print("3. Показать всех клиентов")
        print("4. Показать весь транспорт")
        print("5. Распределить грузы (с делением по транспорту)")
        print("6. Выйти")

        choice = input("Выберите пункт: ")

        if choice == "1":
            name = input("Имя клиента: ")
            weight = float(input("Вес груза: "))
            vip = input("VIP клиент? (y/n): ").lower() == "y"
            client = Client(name, weight, vip)
            company.add_client(client)
            print("Клиент добавлен.")

        elif choice == "2":
            print("1. Грузовик")
            print("2. Поезд")
            t = input("Тип транспорта: ")

            if t == "1":
                cap = float(input("Грузоподъемность: "))
                color = input("Цвет грузовика: ")
                company.add_vehicle(Truck(cap, color))
                print("Грузовик добавлен.")

            elif t == "2":
                cap = float(input("Грузоподъемность: "))
                cars = int(input("Количество вагонов: "))
                company.add_vehicle(Train(cap, cars))
                print("Поезд добавлен.")

        elif choice == "3":
            print("\n=== Клиенты ===")
            if not company.clients:
                print("Нет клиентов.")
            for c in company.clients:
                status = "VIP" if c.is_vip else "Обычный"
                print(f"{c.name} — {c.cargo_weight} т ({status})")

        elif choice == "4":
            print("\n=== Транспорт ===")
            if not company.vehicles:
                print("Нет транспорта.")
            for v in company.vehicles:
                print(v)

        elif choice == "5":
            print("\n=== Распределение грузов ===")
            company.optimize_cargo_distribution()

            for v in company.vehicles:
                print("\n", v)
                if not v.clients_list:
                    print("  (Пусто)")
                for cl in v.clients_list:
                    print(f"  - {cl.name}: {cl.cargo_weight} т")

        elif choice == "6":
            print("Выход...")
            break

        else:
            print("Неверный пункт меню.")


if __name__ == "__main__":
    menu()
