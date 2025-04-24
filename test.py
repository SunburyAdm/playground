import tkinter as tk
from tkinter import ttk

class InventoryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Inventory and Cart")

        # Inventory data (example)
        self.inventory = [
            {"name": "Laptop", "price": 1200, "quantity": 10},
            {"name": "Mouse", "price": 25, "quantity": 50},
            {"name": "Keyboard", "price": 75, "quantity": 30},
        ]
        self.cart = {}

        # Inventory Display
        self.inventory_label = ttk.Label(root, text="Inventory:")
        self.inventory_label.grid(row=0, column=0, sticky="w")
        self.inventory_listbox = tk.Listbox(root, width=40)
        self.inventory_listbox.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.update_inventory_display()

        # Quantity Input
        self.quantity_label = ttk.Label(root, text="Quantity:")
        self.quantity_label.grid(row=2, column=0, sticky="w", padx=5)
        self.quantity_entry = ttk.Entry(root, width=10)
        self.quantity_entry.grid(row=2, column=0, sticky="e", padx=5)

        # Add to Cart Button
        self.add_button = ttk.Button(root, text="Add to Cart", command=self.add_to_cart)
        self.add_button.grid(row=3, column=0, sticky="e", padx=5, pady=5)

        # Cart Display
        self.cart_label = ttk.Label(root, text="Cart:")
        self.cart_label.grid(row=0, column=1, sticky="w")
        self.cart_listbox = tk.Listbox(root, width=40)
        self.cart_listbox.grid(row=1, column=1, sticky="nsew", padx=5, pady=5, rowspan=3)
        self.update_cart_display()

        # Configure grid weights for resizing
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(1, weight=1)

    def update_inventory_display(self):
        self.inventory_listbox.delete(0, tk.END)
        for item in self.inventory:
            self.inventory_listbox.insert(tk.END, f"{item['name']} - Price: ${item['price']} - Quantity: {item['quantity']}")

    def update_cart_display(self):
        self.cart_listbox.delete(0, tk.END)
        for item_name, quantity in self.cart.items():
            self.cart_listbox.insert(tk.END, f"{item_name} - Quantity: {quantity}")

    def add_to_cart(self):
        selected_index = self.inventory_listbox.curselection()
        if not selected_index:
            return  # No item selected

        selected_item = self.inventory[selected_index[0]]
        quantity_str = self.quantity_entry.get()

        try:
            quantity = int(quantity_str)
            if quantity <= 0:
                raise ValueError("Quantity must be a positive number.")
            if quantity > selected_item["quantity"]:
                raise ValueError("Not enough stock available.")
        except ValueError as e:
            print(f"Invalid quantity: {e}")
            return

        item_name = selected_item["name"]
        if item_name in self.cart:
            self.cart[item_name] += quantity
        else:
            self.cart[item_name] = quantity

        selected_item["quantity"] -= quantity
        self.update_inventory_display()
        self.update_cart_display()
        self.quantity_entry.delete(0, tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = InventoryApp(root)
    root.mainloop()