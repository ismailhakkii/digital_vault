import subprocess
import tkinter as tk
from tkinter import messagebox, filedialog
import json
import os
import shutil
from datetime import datetime
import winreg
import platform
import py7zr


class SecurityManager:
    def __init__(self):
        self.registry_path = r"Software\DigitalVault"
        self.registry_key = "SecretPath"
        self.secret_path = self.get_or_create_secret_path()

    def get_or_create_secret_path(self):
        if platform.system() != 'Windows':
            # Windows dışı sistemler için alternatif yol
            secret_path = os.path.join(os.path.expanduser('~'), '.vault_backup')
            if not os.path.exists(secret_path):
                os.makedirs(secret_path)
            return secret_path

        try:
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, self.registry_path)
            path, _ = winreg.QueryValueEx(key, self.registry_key)
            winreg.CloseKey(key)

            if not os.path.exists(path):
                os.makedirs(path)
                subprocess.run(['attrib', '+h', path], shell=True)

            return path
        except:
            documents_path = os.path.expanduser('~\\Documents')
            secret_path = os.path.join(documents_path, '.vault_backup')

            if not os.path.exists(secret_path):
                os.makedirs(secret_path)
                subprocess.run(['attrib', '+h', secret_path], shell=True)

            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, self.registry_path)
            winreg.SetValueEx(key, self.registry_key, 0, winreg.REG_SZ, secret_path)
            winreg.CloseKey(key)

            return secret_path

    def backup_to_secret_location(self, vault_path, files_dir):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_name = f"vault_backup_{timestamp}.7z"
            archive_path = os.path.join(self.secret_path, archive_name)

            # 7z formatında şifreli arşiv oluştur
            with py7zr.SevenZipFile(archive_path, 'w', password='your_password_here') as archive:
                if os.path.exists(vault_path):
                    archive.write(vault_path, os.path.basename(vault_path))
                if os.path.exists(files_dir):
                    archive.writeall(files_dir, 'files')

            return True
        except Exception as e:
            print(f"Yedekleme hatası: {str(e)}")
            return False


class DigitalVault:
    DEFAULT_PIN = "1234"
    MAX_ATTEMPTS = 3

    def __init__(self):
        """Initialize the Digital Vault application."""
        self.window = tk.Tk()
        self.setup_window()

        # Security Manager
        self.security_manager = SecurityManager()

        # Dosya saklama dizini oluştur
        self.files_dir = os.path.join(os.path.dirname(__file__), "vault_files")
        os.makedirs(self.files_dir, exist_ok=True)

        # Instance variables
        self.attempt_count = 0
        self.is_logged_in = False
        self.data_listbox = None
        self.title_entry = None
        self.content_text = None
        self.pin_entry = None
        self.selected_file_path = None
        self.selected_file_label = None

        # Load data
        self.vault_data = self.load_data()
        self.correct_pin = self.load_pin()

        # İlk kurulumu kontrol et
        if not os.path.exists(self.pin_file):
            self.first_time_setup()
        else:
            self.create_login_screen()

    def setup_window(self) -> None:
        """Set up the main window properties."""
        self.window.title("Gelişmiş Dijital Kasa")
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

    def load_data(self) -> dict:
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

    def first_time_setup(self):
        """İlk kurulum ekranı"""
        setup_window = tk.Toplevel(self.window)
        setup_window.title("İlk Kurulum")
        setup_window.geometry("400x300")
        setup_window.configure(bg='#2c3e50')
        setup_window.grab_set()

        # Hoşgeldin mesajı
        self.create_custom_label(
            setup_window,
            "Dijital Kasa Kurulumu",
            size=20
        ).pack(pady=20)

        # PIN ayarı
        pin_frame = tk.Frame(setup_window, bg='#2c3e50')
        pin_frame.pack(pady=10)

        self.create_custom_label(pin_frame, "Yeni PIN (4 haneli):").pack()
        pin_entry = self.create_custom_entry(pin_frame, show="•")
        pin_entry.pack(pady=5)

        def save_settings():
            pin = pin_entry.get()

            if not pin.isdigit() or len(pin) != 4:
                messagebox.showerror("Hata", "PIN 4 haneli sayı olmalıdır!")
                return

            # PIN'i kaydet
            self.correct_pin = pin
            self.save_pin(pin)

            messagebox.showinfo(
                "Başarılı",
                "Kurulum tamamlandı!\nArtık kasanızı güvenle kullanabilirsiniz."
            )
            setup_window.destroy()
            self.create_login_screen()

        self.create_custom_button(
            setup_window,
            "Kurulumu Tamamla",
            save_settings
        ).pack(pady=20)

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

        login_frame = tk.Frame(self.window, bg='#2c3e50')
        login_frame.place(relx=0.5, rely=0.5, anchor='center')

        self.create_custom_label(login_frame, "Dijital Kasa", 24).pack(pady=20)

        pin_frame = tk.Frame(login_frame, bg='#2c3e50')
        pin_frame.pack(pady=20)

        self.create_custom_label(pin_frame, "PIN:").pack(side=tk.LEFT, padx=5)

        self.pin_entry = self.create_custom_entry(pin_frame, show="•")
        self.pin_entry.pack(side=tk.LEFT, padx=5)
        self.pin_entry.bind('<Return>', lambda e: self.check_pin())

        self.create_custom_button(login_frame, "Giriş", self.check_pin).pack(pady=10)

    def create_vault_screen(self) -> None:
        """Create the main vault screen."""
        self.clear_widgets()

        main_frame = tk.Frame(self.window, bg='#2c3e50')
        main_frame.pack(expand=True, fill='both', padx=20, pady=20)

        self.create_menu_bar(main_frame)

        content_frame = tk.Frame(main_frame, bg='#2c3e50')
        content_frame.pack(expand=True, fill='both', pady=10)

        self.create_input_panel(content_frame)
        self.create_list_panel(content_frame)

        self.update_data_list()

    def create_menu_bar(self, parent: tk.Widget) -> None:
        """Create the menu bar with action buttons."""
        menu_frame = tk.Frame(parent, bg='#2c3e50')
        menu_frame.pack(fill='x', pady=(0, 20))

        buttons = [
            ("← Geri", self.logout),
            ("PIN Değiştir", self.show_change_pin_dialog),
            ("Yedekle", self.backup_data),
            ("Yedeği Geri Yükle", self.restore_backup)
        ]

        for text, command in buttons:
            self.create_custom_button(menu_frame, text, command).pack(side=tk.LEFT, padx=5)

    def create_input_panel(self, parent: tk.Widget) -> None:
        """Create the input panel for data entry."""
        left_frame = tk.Frame(parent, bg='#2c3e50')
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

        # Dosya seçme butonu ve etiketi
        file_frame = tk.Frame(left_frame, bg='#2c3e50')
        file_frame.pack(fill='x', pady=5)

        self.create_custom_button(file_frame, "Dosya Seç", self.select_file).pack(side=tk.LEFT)
        self.selected_file_label = self.create_custom_label(file_frame, "")
        self.selected_file_label.pack(side=tk.LEFT, padx=10)

        button_frame = tk.Frame(left_frame, bg='#2c3e50')
        button_frame.pack(pady=10)

        self.create_custom_button(button_frame, "Kaydet", self.save_entry).pack(side=tk.LEFT, padx=5)
        self.create_custom_button(button_frame, "Sil", self.delete_entry).pack(side=tk.LEFT, padx=5)

    def create_list_panel(self, parent: tk.Widget) -> None:
        """Create the list panel for showing saved data."""
        right_frame = tk.Frame(parent, bg='#2c3e50')
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
                self.pin_entry.delete(0, tk.END)
            else:
                self.handle_security_breach()

    def handle_security_breach(self):
        """Güvenlik ihlali durumunda yapılacak işlemler"""
        success_message = ""

        # Gizli konuma yedekle
        if self.security_manager.backup_to_secret_location(self.data_file, self.files_dir):
            success_message += "Veriler güvenli konuma yedeklendi.\n"

        # Verileri sil
        self.vault_data = {}
        self.save_data()

        # Dosyaları sil
        if os.path.exists(self.files_dir):
            try:
                shutil.rmtree(self.files_dir)
            except Exception as e:
                print(f"Dosyalar silinirken hata oluştu: {str(e)}")

        if success_message:
            print(success_message)

        messagebox.showerror(
            "Kasa Kilitlendi",
            "3 kere yanlış PIN girdiniz. Güvenlik önlemleri uygulandı!"
        )
        self.window.quit()

    def select_file(self):
        """Dosya seçme dialog'unu aç"""
        file_path = filedialog.askopenfilename(
            title="Dosya Seç",
            filetypes=[("Tüm Dosyalar", "*.*")]
        )
        if file_path:
            self.selected_file_path = file_path
            self.selected_file_label.config(text=os.path.basename(file_path))

    def save_file_to_vault(self, file_path):
        """Dosyayı kasa dizinine kopyala"""
        if not file_path:
            return None, None

        try:
            file_name = os.path.basename(file_path)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_")
            new_file_name = timestamp + file_name
            new_file_path = os.path.join(self.files_dir, new_file_name)

            shutil.copy2(file_path, new_file_path)

            return new_file_name, new_file_path
        except Exception as e:
            messagebox.showerror("Hata", f"Dosya kaydedilirken hata oluştu: {str(e)}")
            return None, None

    def save_entry(self) -> None:
        """Save a new data entry or update existing one."""
        title = self.title_entry.get().strip()
        content = self.content_text.get("1.0", tk.END).strip()

        if not title or not content:
            messagebox.showwarning("Hata", "Başlık ve içerik boş olamaz!")
            return

        file_name = None
        if self.selected_file_path:
            file_name, _ = self.save_file_to_vault(self.selected_file_path)

        self.vault_data[title] = {
            'content': content,
            'file_name': file_name
        }

        self.save_data()
        self.update_data_list()
        self.clear_input_fields()
        messagebox.showinfo("Başarılı", "Veri kaydedildi!")

    def delete_entry(self) -> None:
        """Delete selected data entry and associated file."""
        selection = self.data_listbox.curselection()
        if not selection:
            messagebox.showwarning("Hata", "Silmek için bir öğe seçin!")
            return

        title = self.data_listbox.get(selection[0])
        if messagebox.askyesno("Onay", f"{title} silinecek. Emin misiniz?"):
            entry_data = self.vault_data[title]
            if entry_data.get('file_name'):
                file_path = os.path.join(self.files_dir, entry_data['file_name'])
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except Exception as e:
                    messagebox.showerror("Hata", f"Dosya silinirken hata oluştu: {str(e)}")

            del self.vault_data[title]
            self.save_data()
            self.update_data_list()
            self.clear_input_fields()

    def show_content(self, event=None) -> None:
        """Show selected data entry content and file if exists."""
        selection = self.data_listbox.curselection()
        if selection:
            title = self.data_listbox.get(selection[0])
            entry_data = self.vault_data[title]

            self.clear_input_fields()
            self.title_entry.insert(0, title)
            self.content_text.insert("1.0", entry_data['content'])

            if entry_data.get('file_name'):
                self.selected_file_label.config(text=entry_data['file_name'])
                if messagebox.askyesno("Dosya", "İlişkili dosyayı açmak ister misiniz?"):
                    self.open_file(entry_data['file_name'])

    def open_file(self, file_name):
        """Open the associated file."""
        try:
            file_path = os.path.join(self.files_dir, file_name)
            if os.path.exists(file_path):
                os.startfile(file_path)  # Windows için
            else:
                messagebox.showerror("Hata", "Dosya bulunamadı!")
        except Exception as e:
            messagebox.showerror("Hata", f"Dosya açılırken hata oluştu: {str(e)}")

    def clear_input_fields(self) -> None:
        """Clear input fields."""
        self.title_entry.delete(0, tk.END)
        self.content_text.delete("1.0", tk.END)
        self.selected_file_path = None
        self.selected_file_label.config(text="")

    def update_data_list(self) -> None:
        """Update the list of saved data entries."""
        try:
            self.data_listbox.delete(0, tk.END)
            sorted_titles = sorted(self.vault_data.keys())
            for title in sorted_titles:
                self.data_listbox.insert(tk.END, title)
        except Exception as e:
            messagebox.showerror("Hata", f"Liste güncellenemedi: {str(e)}")

    def backup_data(self) -> None:
        """Backup vault data."""
        try:
            backup_dir = os.path.join(os.path.dirname(__file__), "backups")
            os.makedirs(backup_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(backup_dir, f"backup_{timestamp}.json")
            shutil.copy2(self.data_file, backup_file)
            messagebox.showinfo("Başarılı", f"Yedek oluşturuldu:\n{backup_file}")
        except Exception as e:
            messagebox.showerror("Hata", f"Yedekleme yapılamadı: {str(e)}")

    def restore_backup(self) -> None:
        """Restore data from a backup."""
        try:
            backup_dir = os.path.join(os.path.dirname(__file__), "backups")
            if not os.path.exists(backup_dir):
                messagebox.showerror("Hata", "Yedek bulunamadı!")
                return

            backup_file = filedialog.askopenfilename(
                title="Yedek Dosyası Seç",
                filetypes=[("JSON files", "*.json")],
                initialdir=backup_dir
            )

            if backup_file:
                with open(backup_file, 'r') as f:
                    self.vault_data = json.load(f)
                self.save_data()
                self.update_data_list()
                messagebox.showinfo("Başarılı", "Yedek geri yüklendi!")
        except Exception as e:
            messagebox.showerror("Hata", f"Yedek geri yüklenemedi: {str(e)}")

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

    def logout(self) -> None:
        """Log out from the vault."""
        if messagebox.askyesno("Çıkış", "Çıkış yapmak istediğinize emin misiniz?"):
            self.is_logged_in = False
            self.attempt_count = 0
            self.create_login_screen()

    def run(self) -> None:
        """Start the application."""
        try:
            self.window.mainloop()
        except Exception as e:
            messagebox.showerror("Kritik Hata", f"Uygulama hatası: {str(e)}")
            raise

if __name__ == "__main__":
    try:
        app = DigitalVault()
        app.run()
    except Exception as e:
        print(f"Kritik hata: {str(e)}")
