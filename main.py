import json
from typing import List, Dict

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView

DATA_FILE = "app.json"

def load_data() -> List[Dict]:
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_data(data: List[Dict]):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

class HomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        title = Label(text="Restaurant Review App", font_size=32, size_hint_y=None, height=60)
        layout.add_widget(title)

        grid = GridLayout(cols=2, spacing=10, size_hint_y=None)
        grid.bind(minimum_height=grid.setter('height'))

        buttons = [
            ("Add Entry", 'add'),
            ("View All Entries", 'view'),
            ("Search Food & Location", 'search_fl'),
            ("Search Food for Rating", 'search_fr'),
            ("Edit Entry", 'edit'),
            ("Delete Entry", 'delete')
        ]

        for label, screen_name in buttons:
            btn = Button(text=label, size_hint_y=None, height=80)
            btn.bind(on_press=lambda btn, name=screen_name: setattr(self.manager, 'current', name))
            grid.add_widget(btn)

        scroll = ScrollView()
        scroll.add_widget(grid)

        layout.add_widget(scroll)
        self.add_widget(layout)

class AddEntryScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical')

        self.inputs = {}
        for field in ["Date", "Restaurant", "Location", "Food", "Review", "Rating"]:
            layout.add_widget(Label(text=field))
            input_box = TextInput(multiline=True, size_hint_y=None, height=40, width=180)
            self.inputs[field.lower()] = input_box
            layout.add_widget(input_box)

        submit_btn = Button(text="Save Entry", size_hint_y=None, height=50)
        submit_btn.bind(on_press=self.save_entry)
        layout.add_widget(submit_btn)

        back = Button(text="Back", size_hint_y=None, height=50)
        back.bind(on_press=self.go_home)
        layout.add_widget(back)

        self.add_widget(layout)

    def clear_inputs(self):
        for key in self.inputs:
            self.inputs[key].text = ""

    def go_home(self, instance):
        self.clear_inputs()
        self.manager.current = 'home'

    def save_entry(self, instance):
        entry = {
            "date": self.inputs["date"].text,
            "restaurant": self.inputs["restaurant"].text.lower(),
            "location": self.inputs["location"].text.lower(),
            "food": self.inputs["food"].text.lower(),
            "review": self.inputs["review"].text,
            "rating": float(self.inputs["rating"].text)
        }
        data = load_data()
        data.append(entry)
        save_data(data)
        self.clear_inputs()
        self.manager.current = 'home'

class ViewEntriesScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical')
        self.scroll = ScrollView()
        self.container = BoxLayout(orientation='vertical', size_hint_y=None)
        self.container.bind(minimum_height=self.container.setter('height'))

        self.scroll.add_widget(self.container)
        self.layout.add_widget(self.scroll)

        back = Button(text="Back", size_hint_y=None, height=50)
        back.bind(on_press=lambda x: setattr(self.manager, 'current', 'home'))
        self.layout.add_widget(back)

        self.add_widget(self.layout)

    def on_enter(self, *args):
        self.update_entries()

    def update_entries(self):
        self.container.clear_widgets()
        data = load_data()
        if not data:
            self.container.add_widget(Label(text="No entries yet.", size_hint_y=None, height=50))
            return
        
        for entry in data:
            info = f"Date: {entry['date']}\nRestaurant: {entry['restaurant']}\nLocation: {entry['location']}\nFood: {entry['food']}\nReview: {entry['review']}\nRating: {entry['rating']}\n"
            entry_label = Label(text=info, size_hint_y=None, height=150, text_size=(self.container.width, None), halign='left')
            self.container.add_widget(entry_label)

class EditEntryScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical')

        self.inputs = {}
        self.dynamic_input_widgets = {}

        initial_fields = ["Restaurant", "Location", "Food"]
        dynamic_fields = ["Date", "Review", "Rating"]

        for field in initial_fields:
            label = Label(text=field)
            input_box = TextInput(multiline=True, size_hint_y=None, height=40)
            self.inputs[field.lower()] = input_box
            self.layout.add_widget(label)
            self.layout.add_widget(input_box)

        for field in dynamic_fields:
            label_text = f"{field} (DD/MM/YY)" if field == "Date" else (f"{field} (1-5)" if field == "Rating" else field)
            label = Label(text=label_text)
            input_box = TextInput(multiline=True, size_hint_y=None, height=40, readonly=True)
            self.inputs[field.lower()] = input_box
            self.dynamic_input_widgets[field.lower()] = input_box
            self.layout.add_widget(label)
            self.layout.add_widget(input_box)

        self.find_btn = Button(text="Find Entry to Edit", size_hint_y=None, height=50)
        self.find_btn.bind(on_press=self.find_entry)
        self.layout.add_widget(self.find_btn)

        self.save_btn = Button(text="Save Edited Entry", size_hint_y=None, height=50)
        self.save_btn.bind(on_press=self.save_edit)
        self.save_btn.opacity = 0.5
        self.save_btn.disabled = True
        self.layout.add_widget(self.save_btn)

        back = Button(text="Back", size_hint_y=None, height=50)
        back.bind(on_press=self.go_home)
        self.layout.add_widget(back)

        self.add_widget(self.layout)

    def clear_inputs(self):
        for key in self.inputs:
            self.inputs[key].text = ""
            self.set_dynamic_inputs_readonly(readonly=True)
            self.save_btn.opacity = 0.5
            self.save_btn.disabled = True
            self.match_index = None

    def go_home(self, instance):
        self.clear_inputs()
        self.manager.current = 'home'

    def set_dynamic_inputs_readonly(self, readonly=True):
        for key in self.dynamic_input_widgets:
            self.dynamic_input_widgets[key].readonly = readonly
            self.dynamic_input_widgets[key].color = (1, 1, 1, 0.7) if readonly else (1, 1, 1, 1)

    def find_entry(self, instance):
        restaurant = self.inputs["restaurant"].text.lower()
        location = self.inputs["location"].text.lower()
        food = self.inputs["food"].text.lower()

        for key in self.dynamic_input_widgets:
            self.dynamic_input_widgets[key].text = ""
        self.set_dynamic_inputs_readonly(readonly=True)
        self.save_btn.opacity = 0.5
        self.save_btn.disabled = True
        self.match_index = None

        self.data = load_data()
        self.match_index = next((i for i, entry in enumerate(self.data)
                                 if entry["restaurant"] == restaurant and entry["location"] == location and entry["food"] == food), None)

        if self.match_index is not None:
            entry = self.data[self.match_index]
            for key in self.inputs:
                self.inputs[key].text = str(entry.get(key, ""))

            self.set_dynamic_inputs_readonly(readonly=False)
            self.save_btn.opacity = 1
            self.save_btn.disabled = False
        else:
            self.set_dynamic_inputs_readonly(readonly=True)
            for key in self.dynamic_input_widgets:
                 self.dynamic_input_widgets[key].text = ""
            self.save_btn.opacity = 0
            self.save_btn.disabled = True
            label = Label(text="Entry not found")

    def save_edit(self, instance):
        if hasattr(self, 'match_index') and self.match_index is not None:
            edited_entry = {key: self.inputs[key].text for key in self.inputs}
            try:
                edited_entry["rating"] = float(edited_entry["rating"])
            except ValueError:
                label = Label(text="Invalid rating input. Please enter a number.")
                return
        
            edited_entry["restaurant"] = edited_entry["restaurant"].lower()
            edited_entry["location"] = edited_entry["location"].lower()
            edited_entry["food"] = edited_entry["food"].lower()
            self.data[self.match_index] = edited_entry
            save_data(self.data)
            self.clear_inputs()
            self.manager.current = 'home'
        else:
            label = Label(text="Entry saved successfully")

class SearchFoodLocationScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical')

        self.food_input = TextInput(hint_text="Enter food", multiline=False, size_hint_y=None, height=40)
        self.location_input = TextInput(hint_text="Enter location", multiline=False, size_hint_y=None, height=40)
        search_btn = Button(text="Search", size_hint_y=None, height=50)
        search_btn.bind(on_press=self.search)

        self.results_container = BoxLayout(orientation='vertical', size_hint_y=None)
        self.results_container.bind(minimum_height=self.results_container.setter('height'))

        self.scroll = ScrollView(size_hint=(1, 1))
        self.scroll.add_widget(self.results_container)

        self.layout.add_widget(self.food_input)
        self.layout.add_widget(self.location_input)
        self.layout.add_widget(search_btn)
        self.layout.add_widget(self.scroll)

        back = Button(text="Back", size_hint_y=None, height=50)
        back.bind(on_press=self.go_home)
        self.layout.add_widget(back)

        self.add_widget(self.layout)

    def clear_inputs(self):
        self.food_input.text = ""
        self.location_input.text = ""
        self.results_container.clear_widgets()

    def go_home(self, instance):
        self.clear_inputs()
        self.manager.current = 'home'

    def search(self, instance):
        food = self.food_input.text.lower()
        location = self.location_input.text.lower()
        data = load_data()
        matches = [entry for entry in data if entry["food"] == food and entry["location"] == location]
        
        self.results_container.clear_widgets()

        if matches:
            for e in matches:
                info = f"Date: {e.get('date', 'N/A')}\nRestaurant: {e.get('restaurant', 'N/A')}\nLocation: {e.get('location', 'N/A')}\nFood: {e.get('food', 'N/A')}\nReview: {e.get('review', 'N/A')}\nRating: {e.get('rating', 'N/A')}\n"
                entry_label = Label(text=info, size_hint_y=None, height=150, text_size=(self.results_container.width, None), halign='left')
                self.results_container.add_widget(entry_label)
        else:
            self.results_container.add_widget(Label(text="No matches found.", size_hint_y=None, height=50))


class SearchFoodRatingScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical')

        self.food_input = TextInput(hint_text="Enter food", multiline=False)
        search_btn = Button(text="Search", size_hint_y=None, height=50)
        search_btn.bind(on_press=self.search)

        self.results_container = BoxLayout(orientation='vertical', size_hint_y=None)
        self.results_container.bind(minimum_height=self.results_container.setter('height'))

        self.scroll = ScrollView(size_hint=(1, 1))
        self.scroll.add_widget(self.results_container)


        self.layout.add_widget(self.food_input)
        self.layout.add_widget(search_btn)
        self.layout.add_widget(self.scroll)

        back = Button(text="Back", size_hint_y=None, height=50)
        back.bind(on_press=self.go_home)
        self.layout.add_widget(back)

        self.add_widget(self.layout)

    def clear_inputs(self):
        self.food_input.text = ""
        self.results_container.clear_widgets()

    def go_home(self, instance):
        self.clear_inputs()
        self.manager.current = 'home'

    def search(self, instance):
        food = self.food_input.text.lower()
        data = load_data()
        matches = [entry for entry in data if entry["food"] == food]
        
        self.results_container.clear_widgets()

        if matches:
            result_text = f"{len(matches)} entries found.\n\n"
            self.results_container.add_widget(Label(text=result_text, size_hint_y=None, height=80, text_size=(self.results_container.width, None), halign='left'))

            for e in matches:
                info = f"Date: {e.get('date', 'N/A')}\nRestaurant: {e.get('restaurant', 'N/A')}\nLocation: {e.get('location', 'N/A')}\nFood: {e.get('food', 'N/A')}\nReview: {e.get('review', 'N/A')}\nRating: {e.get('rating', 'N/A')}\n"
                entry_label = Label(text=info, size_hint_y=None, height=150, text_size=(self.results_container.width, None), halign='left')
                self.results_container.add_widget(entry_label)
        else:
            self.results_container.add_widget(Label(text="No matches found.", size_hint_y=None, height=50))

class DeleteEntryScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', spacing=10, padding=10)

        self.food_input = TextInput(hint_text="Enter food to delete", multiline=False, size_hint_y=None, height=40)
        self.restaurant_input = TextInput(hint_text="Enter restaurant to delete", multiline=False, size_hint_y=None, height=40)
        self.search_btn = Button(text="Search", size_hint_y=None, height=50)
        self.search_btn.bind(on_press=self.search_entry)

        self.result_container = BoxLayout(orientation='vertical', size_hint_y=None)
        self.result_container.bind(minimum_height=self.result_container.setter('height'))

        scroll = ScrollView(size_hint=(1, 1))
        scroll.add_widget(self.result_container)

        back = Button(text="Back", size_hint_y=None, height=50)
        back.bind(on_press=self.go_home)

        self.layout.add_widget(self.food_input)
        self.layout.add_widget(self.restaurant_input)
        self.layout.add_widget(self.search_btn)
        self.layout.add_widget(scroll)
        self.layout.add_widget(back)

        self.add_widget(self.layout)

    def on_enter(self, *args):
        self.clear_inputs()
    
    def clear_inputs(self):
        self.food_input.text = ""
        self.restaurant_input.text = ""
        self.result_container.clear_widgets()

    def go_home(self, instance):
        self.clear_inputs()
        self.manager.current = 'home'

    def search_entry(self, instance):
        food = self.food_input.text.strip().lower()
        restaurant = self.restaurant_input.text.strip().lower()
        data = load_data()
        matches = [e for e in data if e['food'].lower() == food and e['restaurant'].lower() == restaurant]

        self.result_container.clear_widgets()

        if matches:
            for entry in matches:
                info = f"Date: {entry['date']}\nRestaurant: {entry['restaurant']}\nLocation: {entry['location']}\nReview: {entry['review']}\nRating: {entry['rating']}"
                entry_box = BoxLayout(orientation='vertical', size_hint_y=None, height=150, padding=5)
                entry_box.add_widget(Label(text=info, text_size=(self.result_container.width - 10, None), halign='left', valign='top', size_hint_y=None))

                delete_btn = Button(text="Delete", size_hint_y=None, height=40)
                delete_btn.bind(on_press=lambda btn, e=entry: self.delete_entry(e))
                entry_box.add_widget(delete_btn)
                self.result_container.add_widget(entry_box)
        else:
            self.result_container.add_widget(Label(text="No entries found."))

    def delete_entry(self, entry):
        data = load_data()
        if entry in data:
            data.remove(entry)
            save_data(data)
            self.result_container.clear_widgets()
            self.result_container.add_widget(Label(text="Entry deleted successfully."))
        else:
            self.result_container.add_widget(Label(text="Entry no longer exists."))


class RestaurantApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(HomeScreen(name='home'))
        add_screen = AddEntryScreen(name='add')
        sm.add_widget(add_screen)

        view_screen = ViewEntriesScreen(name='view')
        sm.add_widget(view_screen)
        view_screen.bind(on_enter=view_screen.on_enter)

        search_fl_screen = SearchFoodLocationScreen(name='search_fl')
        sm.add_widget(search_fl_screen)
        search_fl_screen.bind(on_enter=search_fl_screen.on_enter)

        search_fr_screen = SearchFoodRatingScreen(name='search_fr')
        sm.add_widget(search_fr_screen)
        search_fr_screen.bind(on_enter=search_fr_screen.on_enter)

        edit_screen = EditEntryScreen(name='edit')
        sm.add_widget(edit_screen)
        edit_screen.bind(on_enter=edit_screen.on_enter)

        delete_screen = DeleteEntryScreen(name='delete')
        sm.add_widget(delete_screen)
        delete_screen.bind(on_enter=delete_screen.on_enter)

        return sm

if __name__ == '__main__':
    RestaurantApp().run()