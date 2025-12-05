import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import re
import os

from transport.client import Client
from transport.vehicle import Truck, Train, Vehicle
from transport.transportcompany import TransportCompany

NAME_RE = re.compile(r"^[A-Za-zА-Яа-яЁё\s\-]{2,}$")

def validate_name(value: str) -> bool:
    return bool(NAME_RE.match(value.strip()))

def validate_weight(value: str) -> bool:
    try:
        w = float(value)
        return 0 < w <= 10000
    except Exception:
        return False

def show_error(msg: str):
    messagebox.showerror("Ошибка", msg)

def show_info(msg: str):
    messagebox.showinfo("Информация", msg)

class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Транспортная компания — GUI (ЛР12)")
        self.geometry("1000x650")
        self.minsize(900, 500)

        self.company = TransportCompany(name="MyTransportCo")
        self.distribution_result = None

        self._create_menu()
        self._create_toolbar()
        self._create_main_tables()
        self._create_status_bar()
        self._create_bindings()

        self.set_status("Готово")

    def _create_menu(self):
        menubar = tk.Menu(self)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Сохранить состояние...", command=self.save_state, accelerator="Ctrl+S")
        file_menu.add_command(label="Загрузить состояние...", command=self.load_state)
        file_menu.add_separator()
        file_menu.add_command(label="Экспорт результата", command=self.export_distribution)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.quit)
        menubar.add_cascade(label="Файл", menu=file_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="О программе", command=self.show_about)
        menubar.add_cascade(label="Помощь", menu=help_menu)

        self.config(menu=menubar)


    def _create_toolbar(self):
        frm = ttk.Frame(self)
        frm.pack(fill="x", padx=6, pady=6)

        self.btn_add_client = ttk.Button(frm, text="Добавить клиента", command=self.add_client)
        self.btn_add_client.pack(side="left", padx=4)

        self.btn_add_vehicle = ttk.Button(frm, text="Добавить транспорт", command=self.add_vehicle)
        self.btn_add_vehicle.pack(side="left", padx=4)

        self.btn_delete = ttk.Button(frm, text="Удалить выбранное", command=self.delete_selected)
        self.btn_delete.pack(side="left", padx=4)

        self.btn_distribute = ttk.Button(frm, text="Распределить грузы", command=self.distribute_cargos)
        self.btn_distribute.pack(side="left", padx=4)

        ttk.Label(frm, text="Фильтр клиентов:").pack(side="left", padx=(20,4))
        self.filter_var = tk.StringVar()
        ent_filter = ttk.Entry(frm, textvariable=self.filter_var, width=20)
        ent_filter.pack(side="left")
        ent_filter.bind("<KeyRelease>", lambda e: self.refresh_clients())

    def _create_main_tables(self):
        main_frame = ttk.Frame(self)
        main_frame.pack(fill="both", expand=True, padx=6, pady=(0,6))

        left = ttk.LabelFrame(main_frame, text="Клиенты")
        left.pack(side="left", fill="both", expand=True, padx=(0,6), pady=2)

        columns_clients = ("name", "weight", "vip")
        self.client_tree = ttk.Treeview(left, columns=columns_clients, show="headings", selectmode="browse")
        for col, title in zip(columns_clients, ("Имя", "Вес (т)", "VIP")):
            self.client_tree.heading(col, text=title, command=lambda c=col: self._sort_tree(self.client_tree, c))
            self.client_tree.column(col, anchor="center")
        self.client_tree.pack(fill="both", expand=True, padx=4, pady=4)
        self.client_tree.bind("<Double-1>", lambda e: self.edit_client())

        right = ttk.LabelFrame(main_frame, text="Транспорт")
        right.pack(side="right", fill="both", expand=True, padx=(6,0), pady=2)

        columns_veh = ("id", "type", "capacity", "load", "clients")
        self.vehicle_tree = ttk.Treeview(right, columns=columns_veh, show="headings", selectmode="browse")
        headers = ["ID", "Тип", "Грузоподъёмность (т)", "Текущая загрузка (т)", "Клиентов"]
        for col, title in zip(columns_veh, headers):
            self.vehicle_tree.heading(col, text=title, command=lambda c=col: self._sort_tree(self.vehicle_tree, c))
            self.vehicle_tree.column(col, anchor="center")
        self.vehicle_tree.pack(fill="both", expand=True, padx=4, pady=4)
        self.vehicle_tree.bind("<Double-1>", lambda e: self.edit_vehicle())

    def _create_status_bar(self):
        self.status_var = tk.StringVar(value="")
        status = ttk.Label(self, textvariable=self.status_var, relief="sunken", anchor="w")
        status.pack(fill="x", side="bottom")

    def set_status(self, text: str):
        self.status_var.set(text)

    def _create_bindings(self):
        self.bind_all("<Control-s>", lambda e: self.save_state())
        self.bind_all("<Escape>", lambda e: self._close_top())

    def _close_top(self):
        for w in self.winfo_children():
            if isinstance(w, tk.Toplevel):
                w.destroy()

    def add_client(self):
        ClientForm(self, mode="add")

    def edit_client(self):
        sel = self.client_tree.selection()
        if not sel:
            return
        idx = int(self.client_tree.item(sel[0], "tags")[0])
        ClientForm(self, mode="edit", client_index=idx)

    def add_vehicle(self):
        VehicleForm(self, mode="add")

    def edit_vehicle(self):
        sel = self.vehicle_tree.selection()
        if not sel:
            return
        idx = int(self.vehicle_tree.item(sel[0], "tags")[0])
        VehicleForm(self, mode="edit", vehicle_index=idx)

    def delete_selected(self):
        if self.client_tree.selection():
            sel = self.client_tree.selection()[0]
            idx = int(self.client_tree.item(sel, "tags")[0])
            client = self.company.clients.pop(idx)
            self.refresh_clients()
            self.set_status(f"Клиент '{client.name}' удалён")
            return

        if self.vehicle_tree.selection():
            sel = self.vehicle_tree.selection()[0]
            idx = int(self.vehicle_tree.item(sel, "tags")[0])
            vehicle = self.company.vehicles.pop(idx)
            self.refresh_vehicles()
            self.set_status(f"Транспорт '{vehicle.vehicle_id}' удалён")
            return

    def refresh_clients(self):
        f = self.filter_var.get().strip().lower()
        for it in self.client_tree.get_children():
            self.client_tree.delete(it)

        for idx, c in enumerate(self.company.clients):
            if f and f not in c.name.lower():
                continue
            self.client_tree.insert("", "end",
                values=(c.name, c.cargo_weight, "Да" if c.is_vip else "Нет"),
                tags=(str(idx),)
            )

    def refresh_vehicles(self):
        for it in self.vehicle_tree.get_children():
            self.vehicle_tree.delete(it)

        for idx, v in enumerate(self.company.vehicles):
            clients_count = len(getattr(v, "clients_list", []))
            self.vehicle_tree.insert("",
                "end",
                values=(v.vehicle_id, v.__class__.__name__, v.capacity,
                        getattr(v, "current_load", 0.0), clients_count),
                tags=(str(idx),)
            )

    def _sort_tree(self, tree: ttk.Treeview, col: str):
        data = [(tree.set(k, col), k) for k in tree.get_children('')]
        try:
            data = [(float(v), k) for v, k in data]
            data.sort()
        except:
            data.sort(key=lambda x: x[0])

        for index, (_, k) in enumerate(data):
            tree.move(k, "", index)

    def distribute_cargos(self):
        if not self.company.vehicles:
            show_error("Нет транспорта для распределения.")
            return
        if not self.company.clients:
            show_error("Нет клиентов для распределения.")
            return

        try:
            vehicles_after = self.company.optimize_cargo_distribution()
        except Exception as e:
            show_error(f"Ошибка при распределении: {e}")
            return

        result = []
        for v in vehicles_after:
            clients = []
            for c in getattr(v, "clients_list", []):
                clients.append({
                    "name": c.name,
                    "cargo_weight": c.cargo_weight,
                    "is_vip": c.is_vip
                })
            result.append({
                "vehicle_id": v.vehicle_id,
                "type": v.__class__.__name__,
                "capacity": v.capacity,
                "current_load": v.current_load,
                "clients": clients
            })

        self.distribution_result = result
        self.refresh_vehicles()
        self.set_status("Распределение завершено")
        show_info("Распределение выполнено")

        DistributionResultDialog(self, result)

    def export_distribution(self):
        if not self.distribution_result:
            show_error("Нет результатов для экспорта.")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")]
        )
        if not path:
            return

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.distribution_result, f, ensure_ascii=False, indent=2)
            show_info("Результат сохранён.")
        except Exception as e:
            show_error(f"Ошибка при сохранении: {e}")

    def save_state(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")]
        )
        if not path:
            return

        data = {
            "clients": [
                {
                    "name": c.name,
                    "cargo_weight": c.cargo_weight,
                    "is_vip": c.is_vip
                }
                for c in self.company.clients
            ],
            "vehicles": []
        }

        for v in self.company.vehicles:
            vdata = {
                "class": v.__class__.__name__,
                "vehicle_id": v.vehicle_id,
                "capacity": v.capacity
            }
            if isinstance(v, Truck):
                vdata["color"] = v.color
            if isinstance(v, Train):
                vdata["number_of_cars"] = v.number_of_cars
            data["vehicles"].append(vdata)

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            show_info("Состояние сохранено.")
        except Exception as e:
            show_error(f"Ошибка сохранения: {e}")

    def load_state(self):
        path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if not path:
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.company.clients = []
            for c in data.get("clients", []):
                self.company.clients.append(
                    Client(
                        name=c["name"],
                        cargo_weight=float(c["cargo_weight"]),
                        is_vip=bool(c["is_vip"])
                    )
                )

            self.company.vehicles = []
            for v in data.get("vehicles", []):
                cls = v["class"]
                cap = float(v["capacity"])

                if cls == "Truck":
                    obj = Truck(capacity=cap, color=v.get("color", ""))
                elif cls == "Train":
                    obj = Train(capacity=cap, number_of_cars=int(v.get("number_of_cars", 0)))
                else:
                    obj = Vehicle(capacity=cap)

                obj.vehicle_id = v.get("vehicle_id", obj.vehicle_id)
                self.company.vehicles.append(obj)

            self.refresh_clients()
            self.refresh_vehicles()
            show_info("Состояние загружено.")

        except Exception as e:
            show_error(f"Ошибка загрузки: {e}")

    def show_about(self):
        text = (
            "Лабораторная работа №12\n"
            "Вариант: X\n"
            "Разработчик: ФИО\n"
        )
        messagebox.showinfo("О программе", text)

class ClientForm(tk.Toplevel):
    def __init__(self, parent: MainApp, mode="add", client_index=None):
        super().__init__(parent)
        self.parent = parent
        self.mode = mode
        self.client_index = client_index

        self.title("Клиент — " + ("редактирование" if mode == "edit" else "добавление"))
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        frm = ttk.Frame(self)
        frm.pack(padx=10, pady=10)

        ttk.Label(frm, text="Имя клиента:").grid(row=0, column=0, sticky="w")
        self.name_var = tk.StringVar()
        ent_name = ttk.Entry(frm, textvariable=self.name_var, width=35)
        ent_name.grid(row=0, column=1, pady=4)

        ttk.Label(frm, text="Вес груза:").grid(row=1, column=0, sticky="w")
        self.weight_var = tk.StringVar()
        ent_weight = ttk.Entry(frm, textvariable=self.weight_var, width=20)
        ent_weight.grid(row=1, column=1, sticky="w", pady=4)

        self.vip_var = tk.BooleanVar()
        ttk.Checkbutton(frm, text="VIP", variable=self.vip_var).grid(row=2, column=1, sticky="w")

        btns = ttk.Frame(frm)
        btns.grid(row=3, column=0, columnspan=2, pady=10)

        ttk.Button(btns, text="Сохранить", command=self.save).pack(side="left", padx=5)
        ttk.Button(btns, text="Отмена", command=self.destroy).pack(side="left", padx=5)

        ent_name.bind("<Return>", lambda e: self.save())
        ent_weight.bind("<Return>", lambda e: self.save())
        self.bind("<Escape>", lambda e: self.destroy())

        if mode == "edit":
            c = parent.company.clients[client_index]
            self.name_var.set(c.name)
            self.weight_var.set(c.cargo_weight)
            self.vip_var.set(c.is_vip)

    def save(self):
        name = self.name_var.get().strip()
        weight = self.weight_var.get().strip()

        if not validate_name(name):
            show_error("Некорректное имя")
            return

        if not validate_weight(weight):
            show_error("Некорректный вес")
            return

        cli = Client(name=name, cargo_weight=float(weight), is_vip=self.vip_var.get())

        if self.mode == "add":
            self.parent.company.add_client(cli)
        else:
            self.parent.company.clients[self.client_index] = cli

        self.parent.refresh_clients()
        self.destroy()

class VehicleForm(tk.Toplevel):
    def __init__(self, parent: MainApp, mode="add", vehicle_index=None):
        super().__init__(parent)
        self.parent = parent
        self.mode = mode
        self.vehicle_index = vehicle_index

        self.title("Транспорт — " + ("редактирование" if mode == "edit" else "добавление"))
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        frm = ttk.Frame(self)
        frm.pack(padx=10, pady=10)

        ttk.Label(frm, text="Тип транспорта:").grid(row=0, column=0, sticky="w")
        self.type_var = tk.StringVar(value="Truck")
        cb = ttk.Combobox(frm, textvariable=self.type_var, values=["Truck", "Train"], state="readonly")
        cb.grid(row=0, column=1, sticky="w", pady=4)
        cb.bind("<<ComboboxSelected>>", lambda e: self._on_type_change())

        ttk.Label(frm, text="Грузоподъёмность (т):").grid(row=1, column=0, sticky="w")
        self.capacity_var = tk.StringVar()
        ttk.Entry(frm, textvariable=self.capacity_var, width=20).grid(row=1, column=1, sticky="w", pady=4)

        self.extra = ttk.Frame(frm)
        self.extra.grid(row=2, column=0, columnspan=2, sticky="w")

        ttk.Label(self.extra, text="Цвет (для грузовика):").grid(row=0, column=0, sticky="w")
        self.color_var = tk.StringVar()
        self.color_entry = ttk.Entry(self.extra, textvariable=self.color_var, width=20)
        self.color_entry.grid(row=0, column=1, sticky="w")

        ttk.Label(self.extra, text="Кол-во вагонов:").grid(row=1, column=0, sticky="w")
        self.cars_var = tk.StringVar()
        self.cars_entry = ttk.Entry(self.extra, textvariable=self.cars_var, width=20)
        self.cars_entry.grid(row=1, column=1, sticky="w")

        btns = ttk.Frame(frm)
        btns.grid(row=3, column=0, columnspan=2, pady=10)
        ttk.Button(btns, text="Сохранить", command=self.save).pack(side="left", padx=5)
        ttk.Button(btns, text="Отмена", command=self.destroy).pack(side="left", padx=5)

        self.bind("<Escape>", lambda e: self.destroy())

        if mode == "edit":
            v = parent.company.vehicles[vehicle_index]
            self.type_var.set(v.__class__.__name__)
            self.capacity_var.set(v.capacity)

            if isinstance(v, Truck):
                self.color_var.set(v.color)
            if isinstance(v, Train):
                self.cars_var.set(v.number_of_cars)

        self._on_type_change()

    def _on_type_change(self):
        t = self.type_var.get()
        if t == "Truck":
            self.color_entry.configure(state="normal")
            self.cars_entry.configure(state="disabled")
        elif t == "Train":
            self.cars_entry.configure(state="normal")
            self.color_entry.configure(state="disabled")
        else:
            self.cars_entry.configure(state="disabled")
            self.color_entry.configure(state="disabled")

    def save(self):
        t = self.type_var.get()
        cap = self.capacity_var.get().strip()

        try:
            capacity = float(cap)
            if capacity <= 0:
                raise ValueError
        except:
            show_error("Некорректная грузоподъёмность")
            return

        if t == "Truck":
            obj = Truck(capacity=capacity, color=self.color_var.get().strip())
        elif t == "Train":
            try:
                n = int(self.cars_var.get().strip())
                if n < 0:
                    raise ValueError
            except:
                show_error("Некорректное число вагонов")
                return
            obj = Train(capacity=capacity, number_of_cars=n)
        else:
            obj = Vehicle(capacity=capacity)

        if self.mode == "add":
            self.parent.company.add_vehicle(obj)
        else:
            old = self.parent.company.vehicles[self.vehicle_index]
            obj.vehicle_id = old.vehicle_id
            self.parent.company.vehicles[self.vehicle_index] = obj

        self.parent.refresh_vehicles()
        self.destroy()

class DistributionResultDialog(tk.Toplevel):
    def __init__(self, parent: MainApp, result):
        super().__init__(parent)
        self.title("Результат распределения")
        self.geometry("700x450")
        self.transient(parent)
        self.grab_set()

        frm = ttk.Frame(self)
        frm.pack(fill="both", expand=True, padx=8, pady=8)

        left = ttk.LabelFrame(frm, text="Транспорт")
        left.pack(side="left", fill="both", expand=True)

        cols = ("id", "type", "cap", "load", "count")
        self.tv = ttk.Treeview(left, columns=cols, show="headings")
        headers = ["ID", "Тип", "Вместимость", "Загрузка", "Клиентов"]
        for c, h in zip(cols, headers):
            self.tv.heading(c, text=h)
        self.tv.pack(fill="both", expand=True)

        for v in result:
            self.tv.insert("", "end",
                values=(
                    v["vehicle_id"],
                    v["type"],
                    v["capacity"],
                    v["current_load"],
                    len(v["clients"])
                )
            )

        right = ttk.LabelFrame(frm, text="Клиенты транспорта")
        right.pack(side="right", fill="both", expand=True)

        cols2 = ("name", "weight", "vip")
        self.clients_tv = ttk.Treeview(right, columns=cols2, show="headings")
        for c, h in zip(cols2, ["Имя", "Вес", "VIP"]):
            self.clients_tv.heading(c, text=h)
        self.clients_tv.pack(fill="both", expand=True)

        def on_select(_):
            self.clients_tv.delete(*self.clients_tv.get_children())
            sel = self.tv.selection()
            if not sel:
                return
            row = self.tv.item(sel[0])["values"]
            vid = row[0]
            for v in result:
                if v["vehicle_id"] == vid:
                    for cli in v["clients"]:
                        self.clients_tv.insert(
                            "", "end",
                            values=(cli["name"], cli["cargo_weight"], "Да" if cli["is_vip"] else "Нет")
                        )

        self.tv.bind("<<TreeviewSelect>>", on_select)

        ttk.Button(self, text="Закрыть", command=self.destroy).pack(pady=6)

def main():
    app = MainApp()
    app.refresh_clients()
    app.refresh_vehicles()
    app.mainloop()

if __name__ == "__main__":
    main()
