from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.properties import NumericProperty, ListProperty, DictProperty, ObjectProperty
from kivy.core.window import Window
from kivy.storage.jsonstore import JsonStore
from kivy.uix.dropdown import DropDown
from kivy.uix.filechooser import FileChooserListView
from kivy.graphics import Color, Ellipse, Line
from kivy.clock import Clock
import json
import os
from datetime import datetime

class CircularProgress(Label):
    progress = NumericProperty(0)  # 0-100
    max_value = NumericProperty(100)
    current_value = NumericProperty(0)
    bar_width = NumericProperty(10)
    bar_color = ListProperty([0, 0.7, 0, 1])  # Green color by default

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self.update_canvas)
        self.bind(size=self.update_canvas)
        self.bind(progress=self.update_canvas)
        self.bind(current_value=self.update_progress)
        self.font_size = self.height * 0.4

    def update_progress(self, instance, value):
        if self.max_value > 0:
            self.progress = (value / self.max_value) * 100
        self.text = str(value)

    def update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            # Background circle
            Color(0.9, 0.9, 0.9, 1)  # Light gray
            Ellipse(pos=self.pos, size=self.size)
            
            # Progress bar
            if self.progress > 0:
                Color(*self.bar_color)
                Line(
                    circle=(
                        self.center_x,
                        self.center_y,
                        min(self.width, self.height) / 2 - self.bar_width,
                        0,
                        self.progress * 3.6
                    ),
                    width=self.bar_width
                )

class TasbihCounter(BoxLayout):
    count = NumericProperty(0)
    tasbih_list = ListProperty(['SubhanAllah', 'Alhamdulillah', 'AllahuAkbar'])
    tasbih_limits = DictProperty({'SubhanAllah': 33, 'Alhamdulillah': 33, 'AllahuAkbar': 33})
    progress_widget = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 10
        self.spacing = 10
        Window.size = (360, 640)  # Mobile-friendly size

        # Load saved tasbihs and limits
        self.store = JsonStore('tasbih_data.json')
        if self.store.exists('tasbihs'):
            self.tasbih_list = self.store.get('tasbihs')['list']
        if self.store.exists('limits'):
            self.tasbih_limits = self.store.get('limits')['values']
        if self.store.exists('counts'):
            self.count = self.store.get('counts')['value']

        # Options menu
        self.options_menu = DropDown()
        about_btn = Button(text='About', size_hint_y=None, height=40)
        about_btn.bind(on_release=lambda btn: self.show_about_popup())
        
        backup_btn = Button(text='Create Backup', size_hint_y=None, height=40)
        backup_btn.bind(on_release=lambda btn: self.create_backup())
        
        restore_btn = Button(text='Restore Backup', size_hint_y=None, height=40)
        restore_btn.bind(on_release=lambda btn: self.show_restore_popup())
        
        exit_btn = Button(text='Exit', size_hint_y=None, height=40)
        exit_btn.bind(on_release=lambda btn: App.get_running_app().stop())
        
        self.options_menu.add_widget(about_btn)
        self.options_menu.add_widget(backup_btn)
        self.options_menu.add_widget(restore_btn)
        self.options_menu.add_widget(exit_btn)
        
        menu_btn = Button(text='☰', size_hint=(0.2, 0.1), pos_hint={'top': 1})
        menu_btn.bind(on_release=self.options_menu.open)
        self.add_widget(menu_btn)

        # Tasbih display
        self.tasbih_label = Label(
            text='Select Tasbih' if not self.tasbih_list else self.tasbih_list[0],
            font_size=24,
            size_hint=(1, 0.1)
        )
        self.add_widget(self.tasbih_label)

        # Navigation and counter
        nav_layout = BoxLayout(size_hint=(1, 0.4), spacing=10)
        self.prev_btn = Button(text='←', font_size=24, size_hint=(0.3, 1), background_color=(0.5, 0.5, 0.5, 1))
        self.prev_btn.bind(on_press=self.prev_tasbih)
        
        # Circular progress counter
        self.progress_widget = CircularProgress(
            size_hint=(0.4, 1),
            current_value=self.count,
            max_value=self.tasbih_limits.get(self.tasbih_label.text, 33) if self.tasbih_list else 33
        )
        
        self.next_btn = Button(text='→', font_size=24, size_hint=(0.3, 1), background_color=(0.5, 0.5, 0.5, 1))
        self.next_btn.bind(on_press=self.next_tasbih)
        nav_layout.add_widget(self.prev_btn)
        nav_layout.add_widget(self.progress_widget)
        nav_layout.add_widget(self.next_btn)
        self.add_widget(nav_layout)

        # Count button
        self.count_btn = Button(
            text='Count',
            size_hint=(1, 0.2),
            background_color=(0, 1, 0, 1)
        )
        self.count_btn.bind(on_press=self.increment_count)
        self.add_widget(self.count_btn)

        # Reset button
        self.reset_btn = Button(
            text='Reset',
            size_hint=(1, 0.1),
            background_color=(1, 0, 0, 1)
        )
        self.reset_btn.bind(on_press=self.reset_count)
        self.add_widget(self.reset_btn)

        # Edit tasbih button
        self.edit_btn = Button(
            text='Edit Tasbihs',
            size_hint=(1, 0.1),
            background_color=(0, 0, 1, 1)
        )
        self.edit_btn.bind(on_press=self.show_edit_popup)
        self.add_widget(self.edit_btn)

        # Initialize tasbih label if list is not empty
        if self.tasbih_list and self.tasbih_label.text == 'Select Tasbih':
            self.tasbih_label.text = self.tasbih_list[0]
            self.update_progress_max()

    def update_progress_max(self):
        current_tasbih = self.tasbih_label.text
        if current_tasbih in self.tasbih_limits:
            self.progress_widget.max_value = self.tasbih_limits[current_tasbih]
        else:
            self.progress_widget.max_value = 33
        self.progress_widget.current_value = self.count

    def increment_count(self, instance):
        current_tasbih = self.tasbih_label.text
        if current_tasbih in self.tasbih_limits:
            limit = self.tasbih_limits[current_tasbih]
            if self.count < limit:
                self.count += 1
                self.progress_widget.current_value = self.count
                self.store.put('counts', value=self.count)
            else:
                # Show completion message
                self.show_completion_popup(current_tasbih)
        else:
            self.count += 1
            self.progress_widget.current_value = self.count
            self.store.put('counts', value=self.count)

    def show_completion_popup(self, tasbih):
        popup_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        popup_layout.add_widget(Label(
            text=f'Congratulations!\nYou have completed {tasbih}',
            font_size=18,
            text_size=(None, None),
            halign='center'
        ))
        close_btn = Button(text='Continue', size_hint=(1, 0.3))
        popup_layout.add_widget(close_btn)
        popup = Popup(title='Completed!', content=popup_layout, size_hint=(0.8, 0.4))
        close_btn.bind(on_press=popup.dismiss)
        popup.open()

    def reset_count(self, instance):
        self.count = 0
        self.progress_widget.current_value = self.count
        self.store.put('counts', value=self.count)

    def prev_tasbih(self, instance):
        if self.tasbih_list:
            current = self.tasbih_label.text
            if current in self.tasbih_list:
                index = self.tasbih_list.index(current)
                next_index = (index - 1) % len(self.tasbih_list)
                self.tasbih_label.text = self.tasbih_list[next_index]
            else:
                self.tasbih_label.text = self.tasbih_list[0]
            self.count = 0
            self.update_progress_max()
            self.store.put('counts', value=self.count)

    def next_tasbih(self, instance):
        if self.tasbih_list:
            current = self.tasbih_label.text
            if current in self.tasbih_list:
                index = self.tasbih_list.index(current)
                next_index = (index + 1) % len(self.tasbih_list)
                self.tasbih_label.text = self.tasbih_list[next_index]
            else:
                self.tasbih_label.text = self.tasbih_list[0]
            self.count = 0
            self.update_progress_max()
            self.store.put('counts', value=self.count)

    def show_edit_popup(self, instance):
        popup_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Scrollable list of tasbihs
        scroll = ScrollView()
        tasbih_grid = GridLayout(cols=1, size_hint_y=None)
        tasbih_grid.bind(minimum_height=tasbih_grid.setter('height'))
        self.tasbih_inputs = []
        
        for tasbih in self.tasbih_list:
            tasbih_row = BoxLayout(size_hint_y=None, height=60, spacing=5)
            tasbih_input = TextInput(text=tasbih, size_hint=(0.5, 1))
            limit_input = TextInput(text=str(self.tasbih_limits.get(tasbih, 33)), size_hint=(0.3, 1), input_filter='int')
            delete_btn = Button(text='🗑', size_hint=(0.2, 1))
            
            tasbih_row.add_widget(tasbih_input)
            tasbih_row.add_widget(limit_input)
            tasbih_row.add_widget(delete_btn)
            self.tasbih_inputs.append((tasbih_input, limit_input, tasbih))
            tasbih_grid.add_widget(tasbih_row)
            
        scroll.add_widget(tasbih_grid)
        popup_layout.add_widget(scroll)

        # Add new tasbih
        new_tasbih_layout = BoxLayout(size_hint=(1, 0.1), spacing=5)
        new_tasbih = TextInput(hint_text='Add new tasbih', size_hint=(0.5, 1))
        new_tasbih_limit = TextInput(hint_text='Limit', size_hint=(0.3, 1), input_filter='int')
        add_btn = Button(text='+', size_hint=(0.2, 1))
        new_tasbih_layout.add_widget(new_tasbih)
        new_tasbih_layout.add_widget(new_tasbih_limit)
        new_tasbih_layout.add_widget(add_btn)
        popup_layout.add_widget(new_tasbih_layout)

        # Save and Cancel buttons
        btn_layout = BoxLayout(size_hint=(1, 0.1), spacing=10)
        save_btn = Button(text='Save', background_color=(0, 1, 0, 1))
        cancel_btn = Button(text='Cancel', background_color=(1, 0, 0, 1))
        btn_layout.add_widget(save_btn)
        btn_layout.add_widget(cancel_btn)
        popup_layout.add_widget(btn_layout)

        popup = Popup(
            title='Edit Tasbihs',
            content=popup_layout,
            size_hint=(0.9, 0.9)
        )

        def add_tasbih(instance):
            if new_tasbih.text.strip():
                self.tasbih_list.append(new_tasbih.text.strip())
                limit = int(new_tasbih_limit.text) if new_tasbih_limit.text.isdigit() else 33
                self.tasbih_limits[new_tasbih.text.strip()] = limit
                self.store.put('tasbihs', list=self.tasbih_list)
                self.store.put('limits', values=self.tasbih_limits)
                popup.dismiss()
                self.show_edit_popup(None)  # Refresh popup

        # Bind delete buttons
        for i, (tasbih_input, limit_input, original_tasbih) in enumerate(self.tasbih_inputs):
            delete_btn = tasbih_grid.children[-(i+1)].children[0]  # Get delete button
            delete_btn.bind(on_press=lambda btn, t=original_tasbih: self.delete_tasbih(t, popup))

        add_btn.bind(on_press=add_tasbih)

        def save_changes(instance):
            new_list = []
            new_limits = {}
            for tasbih_input, limit_input, _ in self.tasbih_inputs:
                if tasbih_input.text.strip():
                    new_list.append(tasbih_input.text.strip())
                    limit = int(limit_input.text) if limit_input.text.isdigit() else 33
                    new_limits[tasbih_input.text.strip()] = limit
            
            self.tasbih_list = new_list
            self.tasbih_limits = new_limits
            
            if self.tasbih_list:
                if self.tasbih_label.text not in self.tasbih_list:
                    self.tasbih_label.text = self.tasbih_list[0]
            else:
                self.tasbih_label.text = 'Select Tasbih'
                
            self.update_progress_max()
            self.store.put('tasbihs', list=self.tasbih_list)
            self.store.put('limits', values=self.tasbih_limits)
            popup.dismiss()

        save_btn.bind(on_press=save_changes)
        cancel_btn.bind(on_press=popup.dismiss)
        popup.open()

    def delete_tasbih(self, tasbih, popup):
        if tasbih in self.tasbih_list:
            self.tasbih_list.remove(tasbih)
            self.tasbih_limits.pop(tasbih, None)
            if self.tasbih_label.text == tasbih:
                self.tasbih_label.text = self.tasbih_list[0] if self.tasbih_list else 'Select Tasbih'
                self.update_progress_max()
            self.store.put('tasbihs', list=self.tasbih_list)
            self.store.put('limits', values=self.tasbih_limits)
            popup.dismiss()
            self.show_edit_popup(None)  # Refresh popup

    def create_backup(self):
        try:
            # Create backup data
            backup_data = {
                'tasbihs': self.tasbih_list,
                'limits': self.tasbih_limits,
                'current_count': self.count,
                'backup_date': datetime.now().isoformat(),
                'app_version': '1.1'
            }
            
            # Create backup filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'tasbih_backup_{timestamp}.json'
            
            # Save backup file
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
            
            # Show success message
            self.show_message_popup('Backup Created', f'Backup saved as:\n{filename}')
            
        except Exception as e:
            self.show_message_popup('Error', f'Failed to create backup:\n{str(e)}')

    def show_restore_popup(self):
        popup_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # File chooser
        filechooser = FileChooserListView(
            filters=['*.json'],
            size_hint=(1, 0.8)
        )
        popup_layout.add_widget(filechooser)
        
        # Buttons
        btn_layout = BoxLayout(size_hint=(1, 0.2), spacing=10)
        restore_btn = Button(text='Restore', background_color=(0, 1, 0, 1))
        cancel_btn = Button(text='Cancel', background_color=(1, 0, 0, 1))
        btn_layout.add_widget(restore_btn)
        btn_layout.add_widget(cancel_btn)
        popup_layout.add_widget(btn_layout)
        
        popup = Popup(
            title='Restore Backup',
            content=popup_layout,
            size_hint=(0.9, 0.9)
        )
        
        def restore_backup(instance):
            if filechooser.selection:
                try:
                    with open(filechooser.selection[0], 'r', encoding='utf-8') as f:
                        backup_data = json.load(f)
                    
                    # Restore data
                    if 'tasbihs' in backup_data:
                        self.tasbih_list = backup_data['tasbihs']
                    if 'limits' in backup_data:
                        self.tasbih_limits = backup_data['limits']
                    if 'current_count' in backup_data:
                        self.count = backup_data['current_count']
                        self.progress_widget.current_value = self.count
                    
                    # Update UI
                    if self.tasbih_list:
                        self.tasbih_label.text = self.tasbih_list[0]
                    else:
                        self.tasbih_label.text = 'Select Tasbih'
                    
                    # Update progress max value
                    self.update_progress_max()
                    
                    # Save to storage
                    self.store.put('tasbihs', list=self.tasbih_list)
                    self.store.put('limits', values=self.tasbih_limits)
                    self.store.put('counts', value=self.count)
                    
                    popup.dismiss()
                    self.show_message_popup('Success', 'Backup restored successfully!')
                    
                except Exception as e:
                    self.show_message_popup('Error', f'Failed to restore backup:\n{str(e)}')
            else:
                self.show_message_popup('Error', 'Please select a backup file.')
        
        restore_btn.bind(on_press=restore_backup)
        cancel_btn.bind(on_press=popup.dismiss)
        popup.open()

    def show_message_popup(self, title, message):
        popup_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        popup_layout.add_widget(Label(
            text=message,
            font_size=16,
            text_size=(300, None),
            halign='center'
        ))
        close_btn = Button(text='OK', size_hint=(1, 0.3))
        popup_layout.add_widget(close_btn)
        popup = Popup(title=title, content=popup_layout, size_hint=(0.8, 0.5))
        close_btn.bind(on_press=popup.dismiss)
        popup.open()

    def show_about_popup(self):
        popup_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        about_text = '''Tasbih Counter App
Version 1.1

Features:
• Count tasbihs with custom limits
• Add/Edit/Delete tasbihs  
• Navigate between different tasbihs
• Create and restore backups
• Completion notifications

Developed for Android'''
        
        popup_layout.add_widget(Label(
            text=about_text,
            font_size=16,
            text_size=(300, None),
            halign='center'
        ))
        close_btn = Button(text='Close', size_hint=(1, 0.2))
        popup_layout.add_widget(close_btn)
        popup = Popup(title='About', content=popup_layout, size_hint=(0.8, 0.6))
        close_btn.bind(on_press=popup.dismiss)
        popup.open()

class TasbihApp(App):
    def build(self):
        return TasbihCounter()

if __name__ == '__main__':
    TasbihApp().run()  # Comment this out
    counter = TasbihCounter()
    print("Tasbih List:", counter.tasbih_list)
    print("Tasbih Limits:", counter.tasbih_limits)
    counter.increment_count(None)
    print("Count after increment:", counter.count)
    counter.next_tasbih(None)
    print("Current Tasbih after next:", counter.tasbih_label.text)