import tkinter as tk
from tkinter import messagebox, filedialog
import json
import os
import shutil
from datetime import datetime
from typing import Dict, Optional


class DigitalVault:
    DEFAULT_PIN = "1234"
    MAX_ATTEMPTS = 3

    def __init__(self):
        """Initialize the Digital Vault application."""
        self.window = tk.Tk()
        self.setup_window()

        # Instance variables
        self.attempt_count = 0
        self.is_logged_in = False
        self.data_listbox: Optional[tk.Listbox] = None
        self.title_entry: Optional[tk.Entry] = None
        self.content_text: Optional[tk.Text] = None
        self.pin_entry: Optional[tk.Entry] = None

        # Load data
        self.vault_data = self.load_data()
        self.correct_pin = self.load_pin()

        # Create initial screen
        self.create_login_screen()

    def setup_window(self) -> None:
        """Set up the main window properties."""
        self.window.title("Gelişmiş Dijital Kasa")

        # Pencereyi ekranın ortasında başlatma
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width - 600) // 2
        y = (screen_height - 700) // 2
        self.window.geometry(f"600x700+{x}+{y}")

        self.window.configure(bg='#2c3e50')
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self) -> None:
        """Handle window closing event."""
        if self.is_logged_in:
            if messagebox.askokcancel("Çıkış", "Kasadan çıkmak istediğinize emin misiniz?"):
                self.window.destroy()
        else:
            self.window.destroy()

    @property
    def data_file(self) -> str:
        """Get the path to the data file."""
        return os.path.join(os.path.dirname(__file__), "vault_data.json")

    @property
    def pin_file(self) -> str:
        """Get the path to the PIN file."""
        return os.path.join(os.path.dirname(__file__), "pin.json")

    def load_pin(self) -> str:
        """Load PIN from file or create with default."""
        try:
            if os.path.exists(self.pin_file):
                with open(self.pin_file, 'r') as f:
                    return json.load(f)["pin"]
        except (json.JSONDecodeError, KeyError, IOError):
            pass

        self.save_pin(self.DEFAULT_PIN)
        return self.DEFAULT_PIN

    def save_pin(self, pin: str) -> None:
        """Save PIN to file."""
        try:
            with open(self.pin_file, 'w') as f:
                json.dump({"pin": pin}, f)
        except IOError:
            messagebox.showerror("Hata", "PIN kaydedilemedi!")

    def load_data(self) -> Dict:
        """Load vault data from file."""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
        return {}

    def save_data(self) -> None:
        """Save vault data to file."""
        try:
            with open(self.data_file, 'w') as f:
                json.dump(self.vault_data, f, ensure_ascii=False, indent=2)
        except IOError:
            messagebox.showerror("Hata", "Veriler kaydedilemedi!")

    def create_custom_button(self, parent: tk.Widget, text: str, command, width: int = None) -> tk.Button:
        """Create a styled button."""
        button = tk.Button(
            parent,
            text=text,
            command=command,
            font=('Helvetica', 12),
            bg='#3498db',
            fg='white',
            activebackground='#2980b9',
            relief=tk.RAISED,
            padx=10,
            pady=5
        )
        if width:
            button.configure(width=width)
        return button

    def create_custom_entry(self, parent: tk.Widget, show: str = None) -> tk.Entry:
        """Create a styled entry widget."""
        return tk.Entry(
            parent,
            show=show,
            font=('Helvetica', 12),
            bg='#34495e',
            fg='white',
            insertbackground='white'
        )

    def create_custom_label(self, parent: tk.Widget, text: str, size: int = 12) -> tk.Label:
        """Create a styled label."""
        return tk.Label(
            parent,
            text=text,
            font=('Helvetica', size),
            bg='#2c3e50',
            fg='white'
        )

    def clear_widgets(self) -> None:
        """Clear all widgets from the window."""
        for widget in self.window.winfo_children():
            widget.destroy()

    def create_login_screen(self) -> None:
        """Create the login screen."""
        self.clear_widgets()

        # Main frame
        login_frame = tk.Frame(self.window, bg='#2c3e50')
        login_frame.place(relx=0.5, rely=0.5, anchor='center')

        # Title
        self.create_custom_label(login_frame, "Dijital Kasa", 24).pack(pady=20)

        # PIN Entry
        pin_frame = tk.Frame(login_frame, bg='#2c3e50')
        pin_frame.pack(pady=20)

        self.create_custom_label(pin_frame, "PIN:").pack(side=tk.LEFT, padx=5)

        self.pin_entry = self.create_custom_entry(pin_frame, show="•")
        self.pin_entry.pack(side=tk.LEFT, padx=5)
        self.pin_entry.bind('<Return>', lambda e: self.check_pin())

        # Login button
        self.create_custom_button(login_frame, "Giriş", self.check_pin).pack(pady=10)

    def check_pin(self) -> None:
        """Check entered PIN and handle login."""
        entered_pin = self.pin_entry.get()
        if entered_pin == self.correct_pin:
            self.is_logged_in = True
            self.create_vault_screen()
        else:
            self.attempt_count += 1
            remaining = self.MAX_ATTEMPTS - self.attempt_count
            if remaining > 0:
                messagebox.showwarning(
                    "Hatalı PIN",
                    f"Yanlış PIN! {remaining} deneme hakkınız kaldı."
                )
                self.pin_entry.delete(0, tk.END)  # PIN'i burada temizle
            else:
                messagebox.showerror(
                    "Kasa Kilitlendi",
                    "3 kere yanlış PIN girdiniz. Tüm veriler siliniyor!"
                )
                self.vault_data = {}
                self.save_data()
                self.pin_entry.delete(0, tk.END)  # PIN'i burada temizle
                self.window.quit()

    def create_vault_screen(self) -> None:
        """Create the main vault screen."""
        self.clear_widgets()

        # Main frame
        main_frame = tk.Frame(self.window, bg='#2c3e50')
        main_frame.pack(expand=True, fill='both', padx=20, pady=20)

        # Menu bar
        menu_frame = tk.Frame(main_frame, bg='#2c3e50')
        menu_frame.pack(fill='x', pady=(0, 20))

        self.create_custom_button(menu_frame, "← Geri", self.logout).pack(side=tk.LEFT, padx=5)
        self.create_custom_button(menu_frame, "PIN Değiştir", self.show_change_pin_dialog).pack(side=tk.LEFT, padx=5)
        self.create_custom_button(menu_frame, "Yedekle", self.backup_data).pack(side=tk.LEFT, padx=5)
        self.create_custom_button(menu_frame, "Yedeği Geri Yükle", self.restore_backup).pack(side=tk.LEFT, padx=5)

        # Left panel
        left_frame = tk.Frame(main_frame, bg='#2c3e50')
        left_frame.pack(side=tk.LEFT, expand=True, fill='both', padx=(0, 10))

        self.create_custom_label(left_frame, "Veri Başlığı:").pack()
        self.title_entry = self.create_custom_entry(left_frame)
        self.title_entry.pack(pady=5, fill='x')

        self.create_custom_label(left_frame, "Veri İçeriği:").pack()
        self.content_text = tk.Text(
            left_frame,
            font=('Helvetica', 12),
            width=40,
            height=5,
            bg='#34495e',
            fg='white',
            insertbackground='white'
        )
        self.content_text.pack(pady=5, fill='both', expand=True)

        # Buttons
        button_frame = tk.Frame(left_frame, bg='#2c3e50')
        button_frame.pack(pady=10)

        self.create_custom_button(button_frame, "Kaydet", self.save_entry).pack(side=tk.LEFT, padx=5)
        self.create_custom_button(button_frame, "Sil", self.delete_entry).pack(side=tk.LEFT, padx=5)

        # Right panel
        right_frame = tk.Frame(main_frame, bg='#2c3e50')
        right_frame.pack(side=tk.LEFT, expand=True, fill='both')

        self.create_custom_label(right_frame, "Kayıtlı Veriler:").pack()
        list_frame = tk.Frame(right_frame, bg='#2c3e50')
        list_frame.pack(fill='both', expand=True)

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill='y')

        self.data_listbox = tk.Listbox(
            list_frame,
            font=('Helvetica', 12),
            width=30,
            height=15,
            bg='#34495e',
            fg='white',
            selectmode=tk.SINGLE,
            yscrollcommand=scrollbar.set
        )
        self.data_listbox.pack(side=tk.LEFT, fill='both', expand=True)
        scrollbar.config(command=self.data_listbox.yview)

        self.data_listbox.bind('<<ListboxSelect>>', self.show_content)
        self.update_data_list()

    def save_entry(self) -> None:
        """Save a new data entry or update existing one."""
        title = self.title_entry.get().strip()
        content = self.content_text.get("1.0", tk.END).strip()

        if not title or not content:
            messagebox.showwarning("Hata", "Başlık ve içerik boş olamaz!")
            return

        self.vault_data[title] = content
        self.save_data()
        self.update_data_list()
        self.clear_input_fields()
        messagebox.showinfo("Başarılı", "Veri kaydedildi!")

    def delete_entry(self) -> None:
        """Delete selected data entry."""
        selection = self.data_listbox.curselection()
        if not selection:
            messagebox.showwarning("Hata", "Silmek için bir öğe seçin!")
            return

        title = self.data_listbox.get(selection[0])
        if messagebox.askyesno("Onay", f"{title} silinecek. Emin misiniz?"):
            del self.vault_data[title]
            self.save_data()
            self.update_data_list()
            self.clear_input_fields()

    def show_content(self, event=None) -> None:
        """Show selected data entry content."""
        selection = self.data_listbox.curselection()
        if selection:
            title = self.data_listbox.get(selection[0])
            content = self.vault_data.get(title, "")
            self.clear_input_fields()
            self.title_entry.insert(0, title)
            self.content_text.insert("1.0", content)

    def clear_input_fields(self) -> None:
        """Clear input fields."""
        self.title_entry.delete(0, tk.END)
        self.content_text.delete("1.0", tk.END)

    def update_data_list(self) -> None:
        """Update the list of saved data entries."""
        self.data_listbox.delete(0, tk.END)
        sorted_titles = sorted(self.vault_data.keys())
        for title in sorted_titles:
            self.data_listbox.insert(tk.END, title)

    def backup_data(self) -> None:
        """Backup vault data."""
        backup_dir = os.path.join(os.path.dirname(__file__), "backups")
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(backup_dir, f"backup_{timestamp}.json")
        shutil.copy2(self.data_file, backup_file)
        messagebox.showinfo("Başarılı", f"Yedek oluşturuldu:\n{backup_file}")

    def restore_backup(self) -> None:
        """Restore data from a backup."""
        try:
            backup_file = filedialog.askopenfilename(
                title="Yedek Dosyası Seç",
                filetypes=[("JSON files", "*.json")],
                initialdir=os.path.join(os.path.dirname(__file__), "backups")
            )
            if backup_file:
                with open(backup_file, 'r') as f:
                    self.vault_data = json.load(f)
                self.save_data()
                self.update_data_list()
                messagebox.showinfo("Başarılı", "Yedek geri yüklendi!")
        except Exception as e:
            messagebox.showerror("Hata", f"Yedek geri yüklenemedi: {str(e)}")

    def logout(self) -> None:
        """Log out from the vault."""
        self.is_logged_in = False
        self.attempt_count = 0
        self.create_login_screen()

    def show_change_pin_dialog(self) -> None:
        """Show dialog to change the PIN."""
        dialog = tk.Toplevel(self.window)
        dialog.title("PIN Değiştir")
        dialog.geometry("300x200")
        dialog.configure(bg='#2c3e50')
        dialog.grab_set()

        self.create_custom_label(dialog, "Mevcut PIN:").pack(pady=5)
        current_pin = self.create_custom_entry(dialog, show="•")
        current_pin.pack(pady=5)

        self.create_custom_label(dialog, "Yeni PIN:").pack(pady=5)
        new_pin = self.create_custom_entry(dialog, show="•")
        new_pin.pack(pady=5)

        def change_pin():
            if current_pin.get() == self.correct_pin:
                if len(new_pin.get()) == 4 and new_pin.get().isdigit():
                    self.correct_pin = new_pin.get()
                    self.save_pin(new_pin.get())
                    messagebox.showinfo("Başarılı", "PIN değiştirildi!")
                    dialog.destroy()
                else:
                    messagebox.showerror("Hata", "Yeni PIN 4 haneli sayı olmalıdır!")
            else:
                messagebox.showerror("Hata", "Mevcut PIN yanlış!")

        self.create_custom_button(dialog, "Değiştir", change_pin).pack(pady=20)

    def run(self) -> None:
        """Start the application."""
        self.window.mainloop()


if __name__ == "__main__":
    app = DigitalVault()
    app.run()
