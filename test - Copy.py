import tkinter as tk
from tkinter import ttk
import customtkinter
import sqlite3
from tkinter import messagebox
from tkinter import filedialog
import openpyxl
import os
from datetime import datetime
from tkinter import filedialog


class InventoryHome:
    def __init__(self, root):
        self.root = root
        self.root.title("Inventory Dashboard")
    
        # ✅ Centrar la ventana principal
        win_width = 795
        win_height = 447
    
        # Asegura que la geometría del sistema esté disponible
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (win_width // 2)
        y = (screen_height // 2) - (win_height // 2)
    
        self.root.geometry(f"{win_width}x{win_height}+{x}+{y}")
        self.root.configure(bg="white")
    
        self.icons = {
            "Home": tk.PhotoImage(file="images/icons/house_icon.png"),
            "Items": tk.PhotoImage(file="images/icons/items_icon.png"),
            "Orders": tk.PhotoImage(file="images/icons/orders_icon.png"),
            "History": tk.PhotoImage(file="images/icons/categories_icon.png"),
            "Reports": tk.PhotoImage(file="images/icons/reports_icon.png"),
            "Settings": tk.PhotoImage(file="images/icons/settings_icon.png"),
            "Logout": tk.PhotoImage(file="images/icons/logout_icon.png"),
        }
    
        self.views = {}
        self.menu_buttons = {}
    
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=0)
        self.root.grid_columnconfigure(1, weight=1)
    
        self.content_container = tk.Frame(self.root, bg="white")
        self.content_container.grid(row=0, column=1, sticky="nsew")
        self.order_type = tk.StringVar(value="Issue")
    
        self.sidebar = tk.Frame(self.root, bg="#bac4d6", width=160)
        self.sidebar.grid(row=0, column=0, sticky="ns")
        self._build_sidebar()

        # Datos simulados para pruebas visuales
        self.inventory = [
            {"name": "Item 1"},
            {"name": "Item 2"},
            {"name": "Item 3"},
            {"name": "Item 4"},
        ]

        self.cart = {}  # Diccionario vacío que se irá llenando con los items agregados

        self._load_inventory_from_db()
    
        self._create_views()
        self.show_view("Home")
        self.selected_inventory_frame = None  # ← para guardar el frame seleccionado




    def _load_items_from_db(self, tree):
        conn = sqlite3.connect("Database/SunburyInventory.db")
        cursor = conn.cursor()
    
        try:
            cols = ["barcode"] + [col.lower().replace(" ", "_") for col in self.visible_columns]
            cursor.execute(f"SELECT {', '.join(cols)} FROM Item_Category_extended")
            rows = cursor.fetchall()
    
            self.all_data = rows  # 🧠 Guarda todos los datos para filtro
    
            tree.delete(*tree.get_children())
            for row in rows:
                barcode = row[0]
                values = row[1:]
                if barcode:
                    tree.insert("", "end", iid=str(barcode), values=[barcode] + list(values))
    
            self.root.after(100, lambda: self.items_tree.yview_moveto(1.0))
    
        except sqlite3.Error as e:
            print("Error al cargar datos:", e)
        finally:
            conn.close()



    def _show_item_details(self, event):
        tree = event.widget
        selected_item = tree.focus()
        if not selected_item:
            return

        barcode = selected_item  # ← usamos el iid directamente

        try:
            conn = sqlite3.connect("Database/SunburyInventory.db")
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(Item_Category_extended)")
            columns_info = cursor.fetchall()
            column_names = [col[1] for col in columns_info]

            cursor.execute("SELECT * FROM Item_Category_extended WHERE barcode = ?", (barcode,))
            row = cursor.fetchone()
            conn.close()
        except Exception as e:
            print(f"Error al cargar detalles: {e}")
            return

        if not row:
            return

        # Crear ventana centrada
        # Crear diccionario clave-valor con los datos del ítem
        data_dict = {column_names[i]: row[i] for i in range(len(column_names))}

        # Usar la clase reutilizable con scroll + inercia
        ScrollableDetailWindow(self.root, "Item Information", data_dict)

    def styled_button(self, parent, text, command=None, icon=None, active=False):
        bg_color = "#bac4d6" if active else "#bac4d6"
        fg_color = "#111827" #Button font color pasive

        btn = tk.Button(
            parent,
            text=text,
            image=icon,
            compound="left" if icon else None,
            anchor="w",
            bg=bg_color,
            fg=fg_color,
            activebackground="#bac4d6",
            activeforeground="#111827", #Button font color active
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            bd=0,
            padx=15,
            pady=8,
            command=command
        )

        if icon:
            btn.image = icon
        return btn


    def _build_sidebar(self):
        sidebar = tk.Frame(self.root, bg="#bac4d6", width=160)
        sidebar.grid(row=0, column=0, sticky="ns")  # 👈 usa grid en lugar de pack

        menu_items = ["Home", "Items", "Orders", "History", "Reports", "Settings"]
        for item in menu_items:
            btn = self.styled_button(
                parent=sidebar,
                text=item,
                icon=self.icons.get(item),
                command=lambda i=item: self.show_view(i),
                active=False
            )
            btn.pack(fill="x", pady=2)
            self.menu_buttons[item] = btn

        # Botón logout abajo
        bottom_frame = tk.Frame(sidebar, bg="#bac4d6")
        bottom_frame.pack(side="bottom", fill="x", pady=10)

        logout_btn = self.styled_button(
            parent=bottom_frame,
            text="Logout",
            icon=self.icons.get("Logout"),
            command=self.logout,
            active=False
        )
        logout_btn.pack(fill="x")



    def logout(self):
        # Aquí pones la lógica real de logout
        print("Logout pressed")
        self.root.destroy()  # O redirigir al login si es parte de app más grande


    def _create_views(self):
        for view_name in ["Home", "Items", "Orders", "History", "Reports", "Settings"]:
            frame = tk.Frame(self.content_container, bg="white")
            frame.grid(row=0, column=0, sticky="nsew")
            self.views[view_name] = frame

            if view_name == "Items":
                self._build_items_view(frame)
            elif view_name == "Settings":
                self._build_settings_view(frame)
            elif view_name == "Home":
                self._build_home_view(frame)
            elif view_name == "Orders":
                self._build_orders_view(frame)
            elif view_name == "Reports":
                self._build_reports_view(frame)
            else:
                self._build_placeholder_view(frame, view_name)

        self._build_home_view(self.views["Home"])

    def show_view(self, name):
        frame = self.views.get(name)
        if frame:
            frame.tkraise()
            frame.update_idletasks()  # 👈 recalcula layout y forzará ajuste de vista

        for btn_name, btn in self.menu_buttons.items():
            btn.config(bg="#6f83a3" if btn_name == name else "#bac4d6")



    def _build_home_view(self, frame):
        title_frame = tk.Frame(frame, bg="white")
        title_frame.pack(fill="x")

        tk.Label(title_frame, text="Inventory", font=("Arial", 20, "bold"), bg="white").pack(side="left")
        tk.Button(title_frame, text="Add Item", bg="#4267B2", fg="white").pack(side="right", padx=5)
        tk.Button(title_frame, text="Export", bg="#4267B2", fg="white").pack(side="right", padx=5)

        chart_section = tk.Frame(frame, bg="white")
        chart_section.pack(fill="x", pady=10)

        chart = tk.Canvas(chart_section, width=200, height=120, bg="white",
                          highlightthickness=1, highlightbackground="#ccc")
        chart.pack(side="left", padx=10)
        self._draw_bar_chart(chart)

        low_stock = tk.Frame(chart_section, bg="white", highlightbackground="#ccc", highlightthickness=1)
        low_stock.pack(side="left", padx=10, fill="both", expand=True)

        tk.Label(low_stock, text="Low Stock", font=("Arial", 10, "bold"), bg="white").pack(anchor="w", padx=5, pady=5)
        for i in range(3):
            tk.Label(low_stock, text=f"- Item {i+1} below threshold", bg="white", fg="#555").pack(anchor="w", padx=10)

        button_frame = tk.Frame(frame, bg="white")
        button_frame.pack(fill="x", pady=15)

        tk.Button(button_frame, text="Receive", width=15, bg="#3a75c4", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=10)
        tk.Button(button_frame, text="Issue", width=15, bg="#3a75c4", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=10)

        table_frame = tk.Frame(frame, bg="white")
        table_frame.pack(fill="both", expand=True)

        tk.Label(table_frame, text="Inventory List", font=("Arial", 12, "bold"), bg="white").pack(anchor="w", pady=(10, 5))

        columns = ("Item", "Quantity")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        tree.heading("Item", text="Item")
        tree.heading("Quantity", text="Quantity")

        for item, qty in [("Screws", 300), ("Wires", 330), ("Batteries", 200)]:
            tree.insert("", "end", values=(item, qty))

        tree.pack(fill="both", expand=True)

    def _draw_bar_chart(self, canvas):
        heights = [40, 80, 60, 100, 70]
        width = 20
        spacing = 15
        for i, h in enumerate(heights):
            x0 = 20 + i * (width + spacing)
            y0 = 100 - h
            x1 = x0 + width
            y1 = 100
            canvas.create_rectangle(x0, y0, x1, y1, fill="#3a75c4")


    def _build_settings_view(self, frame):
        # Configura la grilla principal para centrar el contenido
        for i in range(3):
            frame.grid_rowconfigure(i, weight=1)
            frame.grid_columnconfigure(i, weight=1)
    
        # Contenedor tipo tarjeta visual
        content = tk.Frame(frame, bg="white", highlightbackground="#ccc", highlightthickness=1)
        content.grid(row=0, column=1, padx=30, pady=(20, 10), sticky="n")
        content.grid_columnconfigure(0, weight=1)
    
        # Título
        tk.Label(
            content,
            text="Settings",
            font=("Arial", 18, "bold"),
            bg="white"
        ).grid(row=0, column=0, pady=(20, 10), padx=60)
    
        # Botones de configuración
        options = ["Change Password"]
    
        for i, option in enumerate(options):
            row = 1 + i
            bottom_padding = (5, 30) if i == len(options) - 1 else 5
    
            btn = tk.Button(
                content,
                text=option,
                width=30,
                anchor="center",
                bg="#3a75c4",
                fg="white",
                font=("Segoe UI", 10),
                relief="flat",
                padx=10,
                pady=6,
                command=lambda o=option: self.handle_setting(o)
            )
            btn.grid(row=row, column=0, pady=bottom_padding, padx=30)



    def handle_setting(self, option):
        if option == "Logout":
            self.logout()
        else:
            tk.messagebox.showinfo("Configuración", f"'{option}' aún no implementado.")

    def change_appearance_mode_event(self, new_appearance_mode: str):
        customtkinter.set_appearance_mode(new_appearance_mode)

    def change_scaling_event(self, new_scaling: str):
        new_scaling_float = int(new_scaling.replace("%", "")) / 100
        customtkinter.set_widget_scaling(new_scaling_float)

    def _build_items_view(self, frame):
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        # Contenedor principal
        center_frame = tk.Frame(frame, bg="white")
        center_frame.grid(row=0, column=0, sticky="nsew", padx=30, pady=20)
        center_frame.grid_columnconfigure(0, weight=1)

        # 🔹 Fila 0: Título y búsqueda al mismo nivel
        title_frame = tk.Frame(center_frame, bg="white")
        title_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        title_frame.grid_columnconfigure(0, weight=1)
        title_frame.grid_columnconfigure(1, weight=0)

        # Título "ITEMS"
        tk.Label(
            title_frame,
            text="ITEMS",
            font=("Arial", 20, "bold"),
            bg="white"
        ).grid(row=0, column=0, sticky="w")

        # Búsqueda
        search_frame = tk.Frame(title_frame, bg="white")
        search_frame.grid(row=0, column=1, sticky="e", padx=5)

        self.search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, textvariable=self.search_var, width=25, fg="gray")
        search_entry.pack(side="left", padx=(0, 5))

        placeholder_text = "Search by any field..."
        search_entry.insert(0, placeholder_text)

        def on_entry_focus_in(event):
            if search_entry.get() == placeholder_text:
                search_entry.delete(0, "end")
                search_entry.config(fg="black")

        def on_entry_focus_out(event):
            if not search_entry.get():
                search_entry.insert(0, placeholder_text)
                search_entry.config(fg="gray")

        search_entry.bind("<FocusIn>", on_entry_focus_in)
        search_entry.bind("<FocusOut>", on_entry_focus_out)
        search_entry.bind("<Return>", lambda e: self._apply_filter())
        search_entry.bind("<Escape>", lambda e: self._clear_filter())

        tk.Button(
            search_frame, text="Apply", bg="#3a75c4", fg="white",
            font=("Segoe UI", 9), command=self._apply_filter
        ).pack(side="left", padx=(0, 3))

        tk.Button(
            search_frame, text="Clear", bg="#6b7280", fg="white",
            font=("Segoe UI", 9), command=self._clear_filter
        ).pack(side="left")

        # 🔹 Fila 1: Botones Add/Edit/Delete/Columns centrados
        button_frame = tk.Frame(center_frame, bg="white")
        button_frame.grid(row=1, column=0, pady=5, sticky="n")

        for text, color in [("Add", "#3a75c4"), ("Edit", "#3a75c4"), ("Delete", "#e11d48")]:
            command = getattr(self, f"_{text.lower()}_item")
            tk.Button(
                button_frame,
                text=text,
                bg=color,
                fg="white",
                font=("Segoe UI", 11),
                width=16,
                relief="flat",
                command=command
            ).pack(side="left", padx=5)

        tk.Button(
            button_frame,
            text="Columns",
            bg="#6b7280",
            fg="white",
            font=("Segoe UI", 11),
            width=16,
            relief="flat",
            command=self._configure_columns
        ).pack(side="left", padx=5)

        # Define columnas visibles por defecto
        self.all_columns = [
            "Barcode", "Company", "CCN", "Deparment", "Address 1", "Address 2", "Item Name", "Is Asset",
            "System No", "Company Asset No", "In Stock", "Description", "Vendor", "FY21 Location",
            "FY22 Location", "FY23 Facility", "Room", "Cabinet", "Drawer", "Comments", "Condition",
            "Check Out", "Check In", "Date In", "Date Out", "Current User"
        ]
        self.visible_columns = ["Item Name", "In Stock", "Room", "Current User"]

        # Fila 2: Tabla
        self.table_frame = tk.Frame(center_frame, bg="white")
        self.table_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
        self.table_frame.grid_columnconfigure(0, weight=1)
        self.table_frame.grid_rowconfigure(0, weight=1)

        self._reload_treeview_columns()


    def _reload_treeview_columns(self):

        self.columns_treeview = ["Barcode"] + self.visible_columns

        # Limpia si ya existe tabla
        for widget in self.table_frame.winfo_children():
            widget.destroy()

        yscroll = tk.Scrollbar(self.table_frame, orient="vertical")
        yscroll.grid(row=0, column=1, sticky="ns")

        # Canvas para permitir scroll horizontal si hay muchas columnas
        canvas = tk.Canvas(self.table_frame, bg="white", highlightthickness=0)
        canvas.grid(row=0, column=0, sticky="nsew")
        
        xscroll = tk.Scrollbar(self.table_frame, orient="horizontal")
        xscroll.grid(row=1, column=0, sticky="ew")
        
        yscroll = tk.Scrollbar(self.table_frame, orient="vertical")
        yscroll.grid(row=0, column=1, sticky="ns")
        
        canvas.configure(xscrollcommand=xscroll.set, yscrollcommand=yscroll.set)
        
        # Frame contenedor dentro del canvas
        table_container = tk.Frame(canvas, bg="white")
        canvas_window = canvas.create_window((0, 0), window=table_container, anchor="nw")

        def update_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        table_container.bind("<Configure>", update_scroll_region)

        # Redimensionar scroll automáticamente
        def configure_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(canvas_window, width=canvas.winfo_width())  # Ajusta el ancho visible

        
        table_container.bind("<Configure>", configure_scroll_region)
        
        # Construcción de la tabla dentro del contenedor
        self.items_tree = ttk.Treeview(
            table_container,
            columns=self.columns_treeview,
            show="headings",
            height=13
        )

        yscroll.config(command=self.items_tree.yview)
        self.items_tree.config(yscrollcommand=yscroll.set)

        xscroll.config(command=self.items_tree.xview)
        self.items_tree.config(xscrollcommand=xscroll.set)

        self.items_tree.grid(row=0, column=0, sticky="nsew")
        table_container.grid_rowconfigure(0, weight=1)
        table_container.grid_columnconfigure(0, weight=1)


        def on_mousewheel(event):
            direction = -1 if event.delta > 0 else 1
            if event.state & 0x0001:  # Shift presionado
                for _ in range(3):
                    self.items_tree.xview_scroll(direction, "units")
            else:
                for _ in range(5):
                    self.items_tree.yview_scroll(direction, "units")

        self.items_tree.bind("<Enter>", lambda e: self.items_tree.bind_all("<MouseWheel>", on_mousewheel))
        self.items_tree.bind("<Leave>", lambda e: self.items_tree.unbind_all("<MouseWheel>"))


        def on_mouse_down(event):
            canvas.scan_mark(event.x, event.y)

        def on_mouse_drag(event):
            canvas.scan_dragto(event.x, event.y, gain=1)

        canvas.bind("<ButtonPress-1>", on_mouse_down)
        canvas.bind("<B1-Motion>", on_mouse_drag)
        

        for col in self.columns_treeview:
            self.items_tree.heading(col, text=col, command=lambda _col=col: self._sort_treeview_column(_col, False))

            if col == "Barcode":
                self.items_tree.column(col, width=0, stretch=False)  # Oculta visualmente
            elif col == "Item Name":
                self.items_tree.column(col, width=120)
            elif col == "Description":
                self.items_tree.column(col, width=120)
            else:
                self.items_tree.column(col, anchor="center", width=120)


        self.items_tree.grid(row=0, column=0, sticky="nsew")
        table_container.grid_rowconfigure(0, weight=1)
        table_container.grid_columnconfigure(0, weight=1)

        self.items_tree.bind("<Double-1>", self._show_item_details)

        self.items_tree.bind("<Double-1>", self._show_item_details)
        

        self._load_items_from_db(self.items_tree)
    
    def _sort_treeview_column(self, col, reverse):
        items = [(self.items_tree.set(k, col), k) for k in self.items_tree.get_children('')]
        try:
            items.sort(key=lambda t: int(t[0]), reverse=reverse)
        except ValueError:
            items.sort(key=lambda t: t[0], reverse=reverse)

        for index, (val, k) in enumerate(items):
            self.items_tree.move(k, '', index)

        self.items_tree.heading(col, command=lambda: self._sort_treeview_column(col, not reverse))


    def _configure_columns(self):
        # Crear ventana secundaria centrada
        window = tk.Toplevel(self.root)
        window.title("Select Columns")
        win_width, win_height = 300, 400

        # Centrar la ventana
        window.update_idletasks()
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = (screen_width // 2) - (win_width // 2)
        y = (screen_height // 2) - (win_height // 2)
        window.geometry(f"{win_width}x{win_height}+{x}+{y}")
        window.transient(self.root)
        window.grab_set()
        window.resizable(False, False)

        # Canvas scrollable
        canvas = tk.Canvas(window, bg="white")
        canvas.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(window, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")

        canvas.configure(yscrollcommand=scrollbar.set)

        scroll_frame = tk.Frame(canvas, bg="white")
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")

        scroll_frame.grid_columnconfigure(0, weight=1)

        # Scroll por mousewheel
        def on_mousewheel(event):
            try:
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            except tk.TclError:
                pass

        def bind_mousewheel():
            canvas.bind_all("<MouseWheel>", on_mousewheel)

        def unbind_mousewheel():
            canvas.unbind_all("<MouseWheel>")

        canvas.bind("<Enter>", lambda e: bind_mousewheel())
        canvas.bind("<Leave>", lambda e: unbind_mousewheel())

        # Scroll con arrastre
        def _on_mouse_down(event):
            canvas.scan_mark(event.x, event.y)

        def _on_mouse_drag(event):
            canvas.scan_dragto(0, event.y, gain=1)

        canvas.bind("<ButtonPress-1>", _on_mouse_down)
        canvas.bind("<B1-Motion>", _on_mouse_drag)

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        # Al cerrar, asegúrate de desvincular el scroll
        window.protocol("WM_DELETE_WINDOW", lambda: (unbind_mousewheel(), window.destroy()))

        # Opciones de columnas
        selections = {}
        for i, col in enumerate(self.all_columns):
            var = tk.BooleanVar(value=col in self.visible_columns)
            chk = tk.Checkbutton(scroll_frame, text=col, variable=var, bg="white", anchor="w")
            chk.grid(row=i, column=0, sticky="w", padx=15, pady=2)
            selections[col] = var

        # Botón aplicar
        apply_btn = tk.Button(
            scroll_frame,
            text="Apply",
            command=lambda: self._apply_column_selection(window, selections),
            bg="#3a75c4",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            width=15,
            height=1
        )
        apply_btn.grid(
            row=len(self.all_columns) + 1,
            column=0,
            columnspan=2,
            pady=15,
            sticky="ew",
            padx=90
        )


    def _apply_column_selection(self, window, selections):
        self.visible_columns = [col for col, var in selections.items() if var.get()]
        self._reload_treeview_columns()
        window.destroy()


    def _add_item(self):
        window = tk.Toplevel(self.root)
        window.title("Add Item")
        window.geometry("795x447")
        window.transient(self.root)
        window.grab_set()
        window.resizable(False, False)

        # ✅ Centrar ventana
        window.update_idletasks()  # Asegura que la geometría esté disponible

        # Obtener dimensiones de la pantalla
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()

        # Tamaño de la ventana
        win_width = 795
        win_height = 447

        # Calcular posición centrada
        x = (screen_width // 2) - (win_width // 2)
        y = (screen_height // 2) - (win_height // 2)

        window.geometry(f"{win_width}x{win_height}+{x}+{y}")


        # Scrollable canvas
        canvas = tk.Canvas(window, bg="#f8f8f8")
        canvas.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(window, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")

        canvas.configure(yscrollcommand=scrollbar.set)

        scroll_frame = tk.Frame(canvas, bg="#f8f8f8")
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")

        scroll_frame.grid_columnconfigure(0, weight=1)  # Columna de labels
        scroll_frame.grid_columnconfigure(1, weight=1)  # Columna de entries


        # Scroll con rueda del mouse (activado solo mientras el cursor esté dentro del canvas)
        def on_mousewheel(event):
            try:
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            except tk.TclError:
                pass  # El canvas ya no existe (por si acaso)
            
        def bind_mousewheel():
            canvas.bind_all("<MouseWheel>", on_mousewheel)

        def unbind_mousewheel():
            canvas.unbind_all("<MouseWheel>")

        canvas.bind("<Enter>", lambda e: bind_mousewheel())
        canvas.bind("<Leave>", lambda e: unbind_mousewheel())

        # También desvincula scroll al cerrar la ventana (por seguridad extra)
        window.protocol("WM_DELETE_WINDOW", lambda: (unbind_mousewheel(), window.destroy()))

        # Scroll con arrastre (drag-scroll)
        def _on_mouse_down(event):
            canvas.scan_mark(event.x, event.y)

        def _on_mouse_drag(event):
            canvas.scan_dragto(0, event.y, gain=1)

        canvas.bind("<ButtonPress-1>", _on_mouse_down)
        canvas.bind("<B1-Motion>", _on_mouse_drag)

        # Actualizar scrollregion automáticamente
        def configure_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        scroll_frame.bind("<Configure>", configure_scroll_region)

        # Campos a llenar
        fields = [
                    "Barcode", "Company", "CCN", "Deparment", "Address 1", "Address 2", "Item Name", "Is Asset",
                    "System No", "Company Asset No", "In Stock", "Description", "Vendor", "FY21 Location",
                    "FY22 Location", "FY23 Facility", "Room", "Cabinet", "Drawer", "Comments", "Condition",
                    "Check Out", "Check In", "Date In", "Date Out", "Current User"
                ]


        # Carga valores únicos desde la BD para autocompletar
        def get_distinct_values(column, table="Item_Category_extended"):
            try:
                conn = sqlite3.connect("Database/SunburyInventory.db")
                cursor = conn.cursor()
                cursor.execute(f"SELECT DISTINCT {column} FROM {table}")
                values = [row[0] for row in cursor.fetchall() if row[0] is not None]
                conn.close()
                return values
            except Exception as e:
                print(f"Error loading distinct values from {table}.{column}: {e}")
                return []

            
        autocomplete_fields = ["Room", "Cabinet", "Drawer", "Current User", "Condition", "Vendor"]

        entries = {}
        required_fields = ["Barcode", "Item Name", "In Stock"]

        for i, field in enumerate(fields):
            # Asterisco rojo si es campo obligatorio
            if field in required_fields:
                label_text = f"{field} *"
                label_color = "#d93025"  # rojo Google-style
            else:
                label_text = field
                label_color = "black"

            tk.Label(scroll_frame, text=label_text, fg=label_color, bg="#f8f8f8", font=("Segoe UI", 10))\
                .grid(row=i, column=0, sticky="e", padx=(20, 10), pady=3)

            db_column = field.lower().replace(" ", "_")

            # Verificamos si es current user para usar otra tabla
            if field == "Current User":
                entry = ttk.Combobox(scroll_frame, values=get_distinct_values("employee_fullname", "Employee_Account"))
            elif field in autocomplete_fields:
                entry = ttk.Combobox(scroll_frame, values=get_distinct_values(db_column))
            else:
                entry = tk.Entry(scroll_frame, width=40)

            entry.grid(row=i, column=1, sticky="w", padx=(0, 30), pady=3)
            entries[field] = entry

        # Validación y guardado
        def save():
            valid = True
            for field in required_fields:
                value = entries[field].get().strip()
                if not value:
                    entries[field].config(bg="#ffe6e6")  # rojo claro
                    valid = False
                else:
                    entries[field].config(bg="white")

            if not valid:
                messagebox.showerror("Validation Error", "Please fill all required fields.")
                return

            # Recolectar valores
            values = [entries[field].get() for field in fields]

            try:
                conn = sqlite3.connect("Database/SunburyInventory.db")
                cursor = conn.cursor()
                cursor.execute(f"""
                    INSERT INTO Item_Category_extended 
                    ({','.join([f.lower().replace(' ', '_') for f in fields])}) 
                    VALUES ({','.join(['?'] * len(fields))})
                """, values)
                conn.commit()
                conn.close()
                self._reload_treeview_columns()  # ← reconstruye todo incluyendo nueva tabla
                #self.items_tree.yview_moveto(1.0)  # ← ahora sí funciona

                window.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to insert: {e}")

        # Save button
        tk.Label(
            scroll_frame,
            text="* Required fields",
            fg="#d93025",
            bg="#f8f8f8",
            font=("Segoe UI", 9, "italic")
        ).grid(row=len(fields), column=0, columnspan=2, pady=(10, 0))

        tk.Button(
            scroll_frame,
            text="Save",
            command=save,
            bg="#3a75c4",
            fg="white",
            font=("Segoe UI", 11, "bold"),
            width=20,
            height=2
        ).grid(row=len(fields)+1, column=0, columnspan=2, pady=20)



    def _edit_item(self):
        selected = self.items_tree.focus()
        if not selected:
            messagebox.showinfo("Edit", "Please select an item.")
            return

        barcode = selected  # iid del Treeview

        try:
            conn = sqlite3.connect("Database/SunburyInventory.db")
            cursor = conn.cursor()

            # Obtener estructura de columnas
            cursor.execute("PRAGMA table_info(Item_Category_extended)")
            columns_info = cursor.fetchall()
            column_names = [col[1] for col in columns_info]

            # Obtener valores del ítem seleccionado
            cursor.execute("SELECT * FROM Item_Category_extended WHERE barcode = ?", (barcode,))
            row = cursor.fetchone()
            conn.close()

            if not row:
                messagebox.showerror("Error", "No se encontró el ítem.")
                return

            # Abrir ventana editable
            EditableItemWindow(self.root, "Edit Item", barcode, column_names, row, on_save_callback=lambda: self._load_items_from_db(self.items_tree))

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar el ítem: {e}")


    def _delete_item(self):
        selected = self.items_tree.focus()
        if not selected:
            messagebox.showinfo("Delete", "Please select an item.")
            return

        # El iid del Treeview es el barcode
        barcode = selected

        confirm = messagebox.askyesno("Confirm", f"Delete item with Barcode '{barcode}'?")
        if confirm:
            try:
                conn = sqlite3.connect("Database/SunburyInventory.db")
                cursor = conn.cursor()
                cursor.execute("DELETE FROM Item_Category_extended WHERE barcode = ?", (barcode,))
                conn.commit()
                conn.close()
                self._reload_treeview_columns()  # Recarga la tabla para reflejar el cambio
            except Exception as e:
                messagebox.showerror("Error", f"Could not delete item: {e}")

    def _apply_filter(self):
        text = self.search_var.get().strip().lower()
        if not text or text == "search by any field...":
            return

        filtered = []
        for row in self.all_data:
            if any(text in str(cell).lower() for cell in row):
                filtered.append(row)

        self.items_tree.delete(*self.items_tree.get_children())

        for row in filtered:
            barcode = row[0]
            values = row[1:]
            self.items_tree.insert("", "end", iid=str(barcode), values=[barcode] + list(values))


    def _clear_filter(self):
        self.search_var.set("")
        self.items_tree.delete(*self.items_tree.get_children())
        for row in self.all_data:
            barcode = row[0]
            values = row[1:]
            self.items_tree.insert("", "end", iid=str(barcode), values=[barcode] + list(values))


    def _build_placeholder_view(self, frame, title):
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        content = tk.Frame(frame, bg="white")
        content.grid(row=0, column=0, sticky="n", pady=40)

        tk.Label(
            content,
            text=title,
            font=("Arial", 16, "bold"),
            bg="white"
        ).pack(pady=10)

        tk.Label(
            content,
            text="Content coming soon...",
            font=("Arial", 10, "italic"),
            fg="gray",
            bg="white"
        ).pack(pady=5)

    def _build_orders_view(self, frame):
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        center_frame = tk.Frame(frame, bg="white")
        center_frame.grid(row=0, column=0, sticky="nsew", padx=30, pady=20)
        center_frame.grid_columnconfigure(0, weight=1)
        center_frame.grid_rowconfigure(3, weight=0)  # NO expandir lista
        center_frame.grid_rowconfigure(4, weight=0)  # NO expandir botón


        # 🔹 Fila 0: Título
        header_frame = tk.Frame(center_frame, bg="white")
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        header_frame.grid_columnconfigure(0, weight=1)

        tk.Label(
            header_frame,
            text="ORDERS",
            font=("Arial", 20, "bold"),
            bg="white"
        ).grid(row=0, column=0, sticky="w")

        # 🔹 Fila 1: Top bar (Scanner, Type + Search)
        top_bar = tk.Frame(center_frame, bg="white")
        top_bar.grid(row=1, column=0, sticky="ew", pady=(0, 5))
        top_bar.grid_columnconfigure(2, weight=1)

        tk.Button(top_bar, text="Scanner", width=12, bg="#3a75c4", fg="white").grid(row=0, column=0, padx=5)
        type_var = tk.StringVar(value="Issue")
        tk.OptionMenu(top_bar, self.order_type, "Issue", "Return").grid(row=0, column=1, padx=5)

        # 🟦 Buscador alineado a la derecha
        search_frame = tk.Frame(top_bar, bg="white")
        search_frame.grid(row=0, column=2, sticky="e", padx=(5, 10))

        self.search_orders_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, textvariable=self.search_orders_var, width=30, fg="gray")
        search_entry.pack(side="left", padx=(0, 5))

        placeholder_text = "Search inventory..."
        search_entry.insert(0, placeholder_text)

        def on_focus_in(event):
            if search_entry.get() == placeholder_text:
                search_entry.delete(0, "end")
                search_entry.config(fg="black")

        def on_focus_out(event):
            if not search_entry.get():
                search_entry.insert(0, placeholder_text)
                search_entry.config(fg="gray")

        search_entry.bind("<FocusIn>", on_focus_in)
        search_entry.bind("<FocusOut>", on_focus_out)
        search_entry.bind("<Return>", lambda e: self._apply_inventory_filter())
        search_entry.bind("<Escape>", lambda e: self._clear_inventory_filter())

        tk.Button(
            search_frame,
            text="Apply",
            bg="#3a75c4",
            fg="white",
            font=("Segoe UI", 9),
            width=8,
            command=self._apply_inventory_filter
        ).pack(side="left", padx=(0, 3))

        tk.Button(
            search_frame,
            text="Clear",
            bg="#6b7280",
            fg="white",
            font=("Segoe UI", 9),
            width=8,
            command=self._clear_inventory_filter
        ).pack(side="left")

        # 🔹 Fila 2: Etiquetas de listas
        label_frame = tk.Frame(center_frame, bg="white")
        label_frame.grid(row=2, column=0, sticky="ew", pady=(0, 5))
        label_frame.grid_columnconfigure(0, weight=1)
        label_frame.grid_columnconfigure(1, weight=1)

        # Título centrado en cada mitad del frame
        tk.Label(
            label_frame,
            text="Inventory List",
            font=("Arial", 10, "bold"),
            bg="white"
        ).grid(row=0, column=0, sticky="n", padx=5)

        tk.Label(
            label_frame,
            text="Cart",
            font=("Arial", 10, "bold"),
            bg="white"
        ).grid(row=0, column=1, sticky="n", padx=3)

        # 🔹 Fila 3: Tablas con scroll (ALTO LIMITADO)
        list_container = tk.Frame(center_frame, bg="white", height=260)
        list_container.grid(row=3, column=0, sticky="nsew")
        list_container.grid_propagate(False)  # <- Impide que se expanda más allá del alto definido
        list_container.grid_rowconfigure(0, weight=1)
        list_container.grid_columnconfigure(0, weight=1)
        list_container.grid_columnconfigure(1, weight=1)

        self._build_scrollable_list(list_container, side="left", attr_name="inventory_inner", column=0)
        self._build_scrollable_list(list_container, side="right", attr_name="cart_inner", column=1)

        # 🔹 Fila 4: Botón fijo
        button_frame = tk.Frame(center_frame, bg="white")
        button_frame.grid(row=4, column=0, pady=(10, 5), sticky="ew")

        tk.Button(
            button_frame,
            text="Place Order",
            bg="#3a75c4",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            width=25,
            command=self._place_order
        ).pack(anchor="center")


        # 🔃 Cargar inventario y renderizar
        self._load_inventory_descriptions()
        self._render_inventory_list()



    def _load_inventory_descriptions(self):
        try:
            conn = sqlite3.connect("Database/SunburyInventory.db")
            cursor = conn.cursor()
            cursor.execute("SELECT barcode, description, in_stock, quantity FROM Item_Category_extended")
            rows = cursor.fetchall()
            conn.close()

            self.inventory = []
            for row in rows:
                barcode = row[0]
                description = row[1]
                try:
                    in_stock = int(row[2]) if row[2] is not None else 99
                except (ValueError, TypeError):
                    in_stock = 99

                try:
                    quantity = int(row[3]) if row[3] is not None else 99
                except (ValueError, TypeError):
                    quantity = 99

                self.inventory.append({
                    "barcode": barcode,
                    "description": description,
                    "in_stock": in_stock,
                    "quantity": quantity
                })
        except Exception as e:
            print("Error loading inventory:", e)
            self.inventory = []



    def _render_inventory_list(self, items=None):
        if items is None:
            items = self.inventory

        for widget in self.inventory_inner.winfo_children():
            widget.destroy()

        for item in items:
            frame = tk.Frame(self.inventory_inner, bg="white")
            frame.pack(fill="x", pady=2, padx=5)

            label = tk.Label(
                frame,
                text=self._truncate_text(item["description"]),
                bg="white",
                font=("Segoe UI", 9),
                anchor="w",
                justify="left",
                width=20
            )
            label.pack(side="left", padx=5)

            add_button = tk.Button(
                frame,
                text="Add",
                bg="#3a75c4",
                fg="white",
                font=("Segoe UI", 8),
                width=6,
                command=lambda i=item: self._add_to_cart(i)
            )
            add_button.pack(side="right", padx=5)

            # 🟦 Evento de selección visual
            def on_click(event, current_frame=frame, current_label=label):
                if hasattr(self, "selected_inventory_frame") and self.selected_inventory_frame:
                    if self.selected_inventory_frame and self.selected_inventory_frame.winfo_exists():
                        self.selected_inventory_frame.config(bg="white")
                    if self.selected_inventory_label and self.selected_inventory_label.winfo_exists():
                        self.selected_inventory_label.config(bg="white")


                current_frame.config(bg="#e0f0ff")
                current_label.config(bg="#e0f0ff")

                self.selected_inventory_frame = current_frame
                self.selected_inventory_label = current_label

            frame.bind("<Button-1>", on_click)
            label.bind("<Button-1>", on_click)

            # 🔍 Doble clic para detalles
            for widget in (frame, label):
                widget.bind("<Double-1>", lambda event, b=item["barcode"]: self._show_item_details_by_barcode(b))





    def _add_to_cart(self, item):
        barcode = item["barcode"]
        in_stock = item.get("in_stock", 99)
        quantity_available = item.get("quantity", 99)  # Para Return

        is_return = self.order_type.get() == "Return"
        max_qty = quantity_available if is_return else in_stock

        if barcode in self.cart:
            self._change_cart_qty(barcode, 1)
        else:
            self.cart[barcode] = {
                "desc": item["description"],
                "qty": 1,
                "max": max_qty
            }
            self._render_cart_list()



    def _render_cart_list(self):
        for widget in self.cart_inner.winfo_children():
            widget.destroy()

        for barcode, data in self.cart.items():
            frame = tk.Frame(self.cart_inner, bg="white")
            frame.pack(anchor="w", pady=2, padx=5)

            label = tk.Label(
                frame,
                text=self._truncate_text(data["desc"]),
                bg="white",
                anchor="w",
                justify="left",
                font=("Segoe UI", 9),
                width=15
            )
            label.pack(side="left", padx=5)

            # Estos deben estar dentro del bucle, en el mismo bloque
            tk.Button(frame, text="-", width=2, command=lambda b=barcode: self._change_cart_qty(b, -1)).pack(side="left")
            tk.Label(frame, text=str(data["qty"]), width=3, bg="white").pack(side="left")
            tk.Button(frame, text="+", width=2, command=lambda b=barcode: self._change_cart_qty(b, 1)).pack(side="left")
            tk.Button(frame, text="🗑", fg="red", bg="white", command=lambda b=barcode: self._remove_from_cart(b))\
                .pack(side="right", padx=5)


    def _change_cart_qty(self, barcode, delta):
        if barcode in self.cart:
            current_qty = self.cart[barcode]["qty"]
            max_qty = self.cart[barcode].get("max", 99)

            new_qty = current_qty + delta

            if new_qty < 1:
                messagebox.showinfo("Invalid Quantity", "La cantidad mínima es 1.")
                return

            if new_qty > max_qty:
                messagebox.showinfo("Invalid Quantity", f"La cantidad máxima disponible es {max_qty}.")
                return

            self.cart[barcode]["qty"] = new_qty
            self._render_cart_list()


    def _remove_from_cart(self, barcode):
        if barcode in self.cart:
            del self.cart[barcode]
        self._render_cart_list()

    def _truncate_text(self, text, length=18):
        return text if len(text) <= length else text[:length] + "..."




    def _load_inventory_from_db(self):
        self.inventory = []  # Reinicia la lista

        try:
            conn = sqlite3.connect("Database/SunburyInventory.db")
            cursor = conn.cursor()
            cursor.execute("SELECT barcode, item_name FROM Item_Category_extended")
            rows = cursor.fetchall()
            conn.close()

            for row in rows:
                self.inventory.append({"barcode": row[0], "name": row[1]})

        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to load inventory: {e}")


    def _build_scrollable_list(self, parent, side, attr_name, column):
        container = tk.Frame(parent, bg="white", width=240, height=260, highlightthickness=1, highlightbackground="#ccc")
        container.grid(row=0, column=column, padx=(10, 10), sticky="nsew")
        container.grid_propagate(False)

        canvas = tk.Canvas(container, bg="white", highlightthickness=0)
        canvas.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")
        canvas.configure(yscrollcommand=scrollbar.set)

        inner = tk.Frame(canvas, bg="white")
        window = canvas.create_window((0, 0), window=inner, anchor="nw")

        def update_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def resize_inner_width(event):
            canvas.itemconfig(window, width=event.width)

        inner.bind("<Configure>", update_scroll_region)
        canvas.bind("<Configure>", resize_inner_width)

        def _on_mousewheel(event):
            direction = -1 if event.delta > 0 else 1
            canvas.yview_scroll(direction, "units")

        inner.bind("<Enter>", lambda e: inner.bind_all("<MouseWheel>", _on_mousewheel))
        inner.bind("<Leave>", lambda e: inner.unbind_all("<MouseWheel>"))

        setattr(self, attr_name, inner)

    def _show_item_details_by_barcode(self, barcode):
        try:
            conn = sqlite3.connect("Database/SunburyInventory.db")
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(Item_Category_extended)")
            columns_info = cursor.fetchall()
            column_names = [col[1] for col in columns_info]
    
            cursor.execute("SELECT * FROM Item_Category_extended WHERE barcode = ?", (barcode,))
            row = cursor.fetchone()
            conn.close()
        except Exception as e:
            print(f"Error al cargar detalles: {e}")
            return
    
        if not row:
            messagebox.showinfo("Details", "No data found for selected item.")
            return
    
        # Mostrar en ventana scrollable
        data_dict = dict(zip(column_names, row))
        detail_win = ScrollableDetailWindow(self.root, "Item Details", data_dict)

    def _apply_inventory_filter(self):
        query = self.search_orders_var.get().strip().lower()
        placeholder_text = "Search inventory..."
        if not query or query == placeholder_text.lower():
            self._render_inventory_list()
            return

        filtered = [
            item for item in self.inventory
            if query in item.get("description", "").lower()
            or query in item.get("barcode", "").lower()
        ]
        self._render_inventory_list(filtered)


    def _clear_inventory_filter(self):
        self.search_orders_var.set("")
        self._render_inventory_list()


    def _place_order(self):
        if not self.cart:
            messagebox.showinfo("Empty", "No items in the order.")
            return

        order_type = self.order_type.get()  # "Issue" o "Return"
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d %H:%M:%S")
        receipt_number = now.strftime("%Y%m%d%H%M%S")

        # Tokens temporales (reemplaza con login real más adelante)
        employee_name = "<<employee_name>>"
        badge_number = "<<badge_number>>"

        # Generar detalles del ticket
        ticket_lines = [
            "    SUNBURY INVENTORY",
            "",
            "    THANK YOU",
            "    WE HOPE TO SEE YOU NEXT TIME",
            "",
            " ITEM   -----   QUANTITY   -----   DESCRIPTION"
        ]

        total_qty = 0
        for barcode, item in self.cart.items():
            qty = item["qty"]
            desc = item["desc"]
            ticket_lines.append(f" {barcode}  -----  {qty}  -----  {desc}")
            total_qty += qty

        ticket_lines += [
            "----------------------------------------------------------------------",
            f" Total Items\t\t {total_qty}",
            "----------------------------------------------------------------------",
            "",
            f" Employee Name : {employee_name}",
            f" RECEIPT # : {receipt_number} \t   DATE : {date_str}",
            "----------------------------------------------------------------------",
            "	     FOR COMPLAINTS CALL : Karl"
        ]

        ticket_text = "\n".join(ticket_lines)

        # Guardar cambios en base de datos
        conn = sqlite3.connect("Database/SunburyInventory.db")
        cursor = conn.cursor()

        try:
            for barcode, item in self.cart.items():
                qty = item["qty"]
                if order_type == "Issue":
                    cursor.execute(
                        "UPDATE Item_Category_extended SET in_stock = in_stock - ? WHERE barcode = ?",
                        (qty, barcode)
                    )
                else:  # Return
                    cursor.execute(
                        "UPDATE Item_Category_extended SET in_stock = in_stock + ? WHERE barcode = ?",
                        (qty, barcode)
                    )

            cursor.execute("""
                INSERT INTO History (number, date, employee_name, badge_number, details)
                VALUES (?, ?, ?, ?, ?)
            """, (receipt_number, date_str, employee_name, badge_number, ticket_text))

            conn.commit()
            messagebox.showinfo("Success", "Order placed successfully!")

            self.cart.clear()
            self._render_inventory_list()
            self._render_cart_list()

        except Exception as e:
            conn.rollback()
            messagebox.showerror("Error", f"An error occurred: {e}")
        finally:
            conn.close()




    def _build_reports_view(self, frame):
        # Configura la grilla base
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        # Contenedor tipo tarjeta centrado
        card = tk.Frame(
            frame,
            bg="white",
            highlightbackground="#ccc",
            highlightthickness=1
        )
        card.grid(row=0, column=0, padx=40, pady=40, sticky="n")
        card.grid_columnconfigure(0, weight=1)

        # Título principal
        tk.Label(
            card,
            text="REPORTS",
            font=("Arial", 18, "bold"),
            bg="white",
            fg="#111827"
        ).grid(row=0, column=0, pady=(20, 10), padx=30)

        # Texto placeholder o botones futuros
        placeholder = tk.Label(
            card,
            text="Reports dashboard under construction...",
            font=("Segoe UI", 10),
            bg="white",
            fg="#6b7280"
        )
        placeholder.grid(row=1, column=0, pady=(10, 20), padx=30)

        # Botón de ejemplo para futuras funciones
        tk.Button(
                card,
                text="Generate Report",
                bg="#3a75c4",
                fg="white",
                font=("Segoe UI", 10),
                relief="flat",
                width=25,
                command=self._report_generation  # ← ahora sí accede como método
            ).grid(row=2, column=0, pady=(5, 20))

    def _report_generation(self):
        try:
            # 📊 Mapea columnas de la base de datos con celdas de Excel
            lookuptable = {
                4: "L",  # Company
                9: "C",  # Item Name
                10: "E", # In Stock
                11: "F", # Description
                12: "G", # Vendor
                13: "H", # FY21 Location
                16: "M"  # Room
            }

            starting_row = 10

            # 🔌 Conexión a la base de datos
            conn = sqlite3.connect("./Database/SunburyInventory.db")
            cur = conn.cursor()

            # 📥 Consulta los activos
            cur.execute("SELECT * FROM Item_Category_extended WHERE is_asset = 'Yes'")
            rows = cur.fetchall()

            # 📂 Cargar plantilla de Excel
            workbook = openpyxl.load_workbook("template/report template.xlsx")
            sheet = workbook.active

            # 📝 Llenar la hoja con los datos
            for offset, row in enumerate(rows):
                number = starting_row + offset
                for key, col in lookuptable.items():
                    if key < len(row):
                        sheet[f"{col}{number}"] = row[key]

            # 💾 Guardar nuevo archivo
            file_path = self._save_file_dialog()

            if file_path:
                workbook.save(file_path)
                messagebox.showinfo("Success", f"Report saved to:\n{file_path}")
            else:
                messagebox.showwarning("Cancelled", "Report generation was cancelled.")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate report:\n{e}")
        finally:
            conn.close()

    def _save_file_dialog(self):
            default_filename = f"report_{datetime.now().strftime('%Y-%m-%d')}.xlsx"

            # Carpeta por defecto (ajusta si prefieres otra)
            default_dir = os.path.join(os.path.expanduser("~"), "Desktop", "Reports")

            # Crea la carpeta si no existe
            os.makedirs(default_dir, exist_ok=True)

            return filedialog.asksaveasfilename(
                initialdir=default_dir,
                initialfile=default_filename,
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx")],
                title="Save report as"
            )



class ScrollableDetailWindow(tk.Toplevel):
    def __init__(self, master, title, data_dict, width=400, height=447):
        super().__init__(master)
        self.title(title)
        self.geometry(f"{width}x{height}")
        self.transient(master)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", lambda: (self._cleanup_scroll_binding(), self.destroy()))

        # Centrar en pantalla
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw // 2) - (width // 2)
        y = (sh // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

        # Canvas con scroll
        container = tk.Frame(self)
        container.pack(fill="both", expand=True)

        canvas = tk.Canvas(container, bg="white", highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        self.scroll_frame = tk.Frame(canvas, bg="white")
        self.canvas_window = canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw", width=width)

        def on_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(self.canvas_window, width=canvas.winfo_width())

        self.scroll_frame.bind("<Configure>", on_configure)

        # Scroll con rueda del mouse
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", on_mousewheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        # Scroll por arrastre (drag-scroll) en scroll_frame
        def _on_mouse_down(event):
            canvas.scan_mark(event.x, event.y)

        def _on_mouse_drag(event):
            canvas.scan_dragto(event.x, event.y, gain=1)

        self.scroll_frame.bind("<ButtonPress-1>", _on_mouse_down)
        self.scroll_frame.bind("<B1-Motion>", _on_mouse_drag)

        # Contenido
        tk.Label(self.scroll_frame, text=title, font=("Arial", 14, "bold"), bg="white")\
            .pack(pady=(10, 5))

        for label, val in data_dict.items():
            display = f"{label.replace('_', ' ').title()}: {val if val is not None else ''}"
            tk.Label(self.scroll_frame, text=display, font=("Arial", 10), anchor="w",
                     bg="white", justify="left", wraplength=width - 40)\
                .pack(pady=3, padx=10, anchor="w")

        # Botón cerrar
        tk.Button(self.scroll_frame, text="Close", command=lambda: (self._cleanup_scroll_binding(), self.destroy()), bg="#3a75c4", fg="white",
                  font=("Segoe UI", 10), width=12).pack(pady=20)
        
    def _cleanup_scroll_binding(self):
        self.unbind_all("<MouseWheel>")


class EditableItemWindow(tk.Toplevel):
    def __init__(self, master, title, barcode, column_names, values, on_save_callback=None):
        super().__init__(master)
        self.title(title)
        self.geometry("600x447")
        self.transient(master)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", lambda: (self._cleanup_scroll_binding(), self.destroy()))
        self.on_save_callback = on_save_callback
        self.barcode = barcode

        # Centrar
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw // 2) - (600 // 2)
        y = (sh // 2) - (447 // 2)
        self.geometry(f"600x447+{x}+{y}")

        # Scrollable area
        container = tk.Frame(self)
        container.pack(fill="both", expand=True)

        canvas = tk.Canvas(container, bg="white", highlightthickness=0)
        canvas.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")
        canvas.configure(yscrollcommand=scrollbar.set)

        self.scroll_frame = tk.Frame(canvas, bg="white")
        canvas_window = canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw", width=580)

        def on_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(canvas_window, width=canvas.winfo_width())

        self.scroll_frame.bind("<Configure>", on_configure)

        # Mouse y drag scroll
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _on_mouse_down(event):
            canvas.scan_mark(event.x, event.y)

        def _on_mouse_drag(event):
            canvas.scan_dragto(event.x, event.y, gain=1)

        self.scroll_frame.bind("<ButtonPress-1>", _on_mouse_down)
        self.scroll_frame.bind("<B1-Motion>", _on_mouse_drag)
        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        # Entradas editables
        self.entries = {}
        for i, field in enumerate(column_names):
            label_text = field.replace("_", " ").title()
            tk.Label(self.scroll_frame, text=label_text, font=("Segoe UI", 10), bg="white")\
                .grid(row=i, column=0, sticky="e", padx=(20, 10), pady=5)
            entry = tk.Entry(self.scroll_frame, width=40)
            entry.insert(0, values[i] if values[i] is not None else "")
            entry.grid(row=i, column=1, sticky="w", padx=(0, 20), pady=5)
            self.entries[field] = entry

        # Botón Guardar
        tk.Button(
            self.scroll_frame,
            text="Save",
            command=self.save_changes,
            bg="#3a75c4",
            fg="white",
            font=("Segoe UI", 10),
            width=20
        ).grid(row=len(column_names), column=0, columnspan=2, pady=20)

    def save_changes(self):
        values = {field: self.entries[field].get() for field in self.entries}
        try:
            conn = sqlite3.connect("Database/SunburyInventory.db")
            cursor = conn.cursor()
            update_stmt = ", ".join([f"{k} = ?" for k in values.keys()])
            cursor.execute(
                f"UPDATE Item_Category_extended SET {update_stmt} WHERE barcode = ?",
                list(values.values()) + [self.barcode]
            )
            conn.commit()
            conn.close()
            if self.on_save_callback:
                self.on_save_callback()
            self._cleanup_scroll_binding()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update: {e}")

    def _cleanup_scroll_binding(self):
        self.unbind_all("<MouseWheel>")





if __name__ == "__main__":
    root = tk.Tk()
    app = InventoryHome(root)
    root.mainloop()
