
import requests
import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
import json
import csv
import io

class PokeAPI:
    BASE_URL = "https://pokeapi.co/api/v2/"

    def get_pokemon_list(self, limit=10):
        response = requests.get(f"{self.BASE_URL}pokemon?limit={limit}")
        response.raise_for_status()
        return response.json()['results']

    def get_pokemon_details(self, pokemon_url):
        response = requests.get(pokemon_url)
        response.raise_for_status()
        return response.json()

class Pokemon:
    def __init__(self, name, height, weight, types, abilities, stats, image_url):
        self.name = name
        self.height = height
        self.weight = weight
        self.types = types
        self.abilities = abilities
        self.stats = stats
        self.image_url = image_url

    def to_dict(self):
        data = {
            "name": self.name,
            "height": self.height,
            "weight": self.weight,
            "types": ', '.join(self.types),
            "abilities": ', '.join(self.abilities)
        }
        data.update(self.stats)
        return data

class PokemonDataManager:
    def __init__(self):
        self.api = PokeAPI()
        self.pokemon_data = []

    def fetch_and_store_data(self, limit=10):
        self.pokemon_data.clear()
        pokemon_list = self.api.get_pokemon_list(limit)
        for item in pokemon_list:
            details = self.api.get_pokemon_details(item['url'])
            types = [t['type']['name'] for t in details['types']]
            abilities = [a['ability']['name'] for a in details['abilities']]
            stats = {stat['stat']['name']: stat['base_stat'] for stat in details['stats']}
            image_url = details['sprites']['front_default']
            pokemon = Pokemon(details['name'], details['height'], details['weight'], types, abilities, stats, image_url)
            self.pokemon_data.append(pokemon)

    def save_to_json(self, filename="pokemon_data.json"):
        with open(filename, 'w') as f:
            json.dump([p.to_dict() for p in self.pokemon_data], f, indent=4)

    def save_to_csv(self, filename="pokemon_data.csv"):
        fieldnames = ["name", "height", "weight", "types", "abilities", 
                      "hp", "attack", "defense", "special-attack", "special-defense", "speed"]
        with open(filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for p in self.pokemon_data:
                writer.writerow(p.to_dict())

class PokemonApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Pokémon Viewer with Images")
        self.geometry("1050x600")
        self.data_manager = PokemonDataManager()
        self.image_label = None
        self.image_cache = {}
        self.create_widgets()

    def create_widgets(self):
        input_frame = tk.Frame(self)
        input_frame.pack(pady=10)
        label = tk.Label(input_frame, text="Number of Pokémon to fetch:")
        label.pack(side=tk.LEFT, padx=5)
        self.entry = tk.Entry(input_frame, width=5)
        self.entry.pack(side=tk.LEFT)
        self.entry.insert(0, "10")
        fetch_button = tk.Button(input_frame, text="Fetch Pokémon", command=self.fetch_pokemon)
        fetch_button.pack(side=tk.LEFT, padx=5)
        save_button = tk.Button(input_frame, text="Save to File", command=self.save_data)
        save_button.pack(side=tk.LEFT, padx=5)

        columns = ("Name", "Height", "Weight", "Types", "Abilities", "HP", "Attack", "Defense", "SpAtk", "SpDef", "Speed")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=90, anchor="center")
        self.tree.bind("<<TreeviewSelect>>", self.on_pokemon_select)
        self.tree.pack(expand=True, fill="both")

        self.image_label = tk.Label(self)
        self.image_label.pack(pady=10)

    def fetch_pokemon(self):
        try:
            limit = int(self.entry.get())
            self.data_manager.fetch_and_store_data(limit=limit)
            self.tree.delete(*self.tree.get_children())
            for p in self.data_manager.pokemon_data:
                stats = p.stats
                self.tree.insert("", "end", iid=p.name, values=(
                    p.name.title(),
                    p.height,
                    p.weight,
                    ', '.join(p.types),
                    ', '.join(p.abilities),
                    stats.get("hp", "N/A"),
                    stats.get("attack", "N/A"),
                    stats.get("defense", "N/A"),
                    stats.get("special-attack", "N/A"),
                    stats.get("special-defense", "N/A"),
                    stats.get("speed", "N/A")
                ))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def on_pokemon_select(self, event):
        selected = self.tree.selection()
        if selected:
            pokemon_name = selected[0].lower()
            for p in self.data_manager.pokemon_data:
                if p.name == pokemon_name:
                    if p.image_url:
                        response = requests.get(p.image_url)
                        image_data = response.content
                        image = Image.open(io.BytesIO(image_data))
                        image = image.resize((120, 120))
                        photo = ImageTk.PhotoImage(image)
                        self.image_label.configure(image=photo)
                        self.image_label.image = photo
                    else:
                        self.image_label.configure(image='', text="No image available")

    def save_data(self):
        try:
            self.data_manager.save_to_json()
            self.data_manager.save_to_csv()
            messagebox.showinfo("Success", "Data saved to JSON and CSV files.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    app = PokemonApp()
    app.mainloop()
