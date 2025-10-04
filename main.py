import tkinter as tk
from tkinter import ttk, messagebox
import data_manager
import analysis
import settings_manager
import email_notifier
import reminder_scheduler
import symptoms
from datetime import datetime
import calendar
import subprocess
import pandas as pd

class CravingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Dzienniczek Głodów Alkoholowych")
        self.root.geometry("1200x800")
        self.selected_symptoms = []
        self.current_date = datetime.now()

        # --- Main Layout ---
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(pady=10, padx=10, fill="both", expand=True)

        self.journal_frame = ttk.Frame(self.notebook)
        self.analysis_frame = ttk.Frame(self.notebook)
        self.settings_frame = ttk.Frame(self.notebook)

        self.notebook.add(self.journal_frame, text='Kalendarz Głodów')
        self.notebook.add(self.analysis_frame, text='Analiza')
        self.notebook.add(self.settings_frame, text='Ustawienia')

        self.create_journal_widgets()
        self.create_analysis_widgets()
        self.create_settings_widgets()

        self.load_app_settings()
        self.load_entries() # This will now draw the calendar
        reminder_scheduler.start_scheduler_thread()

    def create_journal_widgets(self):
        # --- Top control frame ---
        control_frame = ttk.Frame(self.journal_frame)
        control_frame.pack(fill='x', padx=10, pady=5)

        ttk.Button(control_frame, text="< Poprzedni Miesiąc", command=self.prev_month).pack(side='left')
        self.month_year_label = ttk.Label(control_frame, text="", font=("Helvetica", 14, "bold"))
        self.month_year_label.pack(side='left', expand=True)
        ttk.Button(control_frame, text="Następny Miesiąc >", command=self.next_month).pack(side='right')

        ttk.Button(control_frame, text="Dodaj Nowy Wpis", command=self.open_new_entry_window).pack(pady=10)

        # --- Calendar grid frame ---
        self.calendar_frame = ttk.Frame(self.journal_frame)
        self.calendar_frame.pack(fill="both", expand=True, padx=10, pady=10)

    def draw_calendar_view(self):
        # Clear previous view
        for widget in self.calendar_frame.winfo_children():
            widget.destroy()

        # Update month/year label
        self.month_year_label.config(text=self.current_date.strftime("%B %Y"))

        # Load data for the current month
        all_entries = data_manager.load_cravings()
        df = pd.DataFrame(all_entries)
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            month_df = df[df['timestamp'].dt.to_period('M') == self.current_date.to_period('M')]
        else:
            month_df = pd.DataFrame()

        # Get calendar data
        cal = calendar.monthcalendar(self.current_date.year, self.current_date.month)
        days_in_month = calendar.monthrange(self.current_date.year, self.current_date.month)[1]

        # --- Create Grid ---
        # Header: Symptom labels
        ttk.Label(self.calendar_frame, text="Objaw / Wyzwalacz", font=("Helvetica", 10, "bold"), relief="solid", borderwidth=1, padding=5).grid(row=0, column=0, sticky="nsew")

        # Header: Day numbers
        for day_num in range(1, days_in_month + 1):
            ttk.Label(self.calendar_frame, text=str(day_num), font=("Helvetica", 10, "bold"), relief="solid", borderwidth=1, padding=5).grid(row=0, column=day_num, sticky="nsew")

        # Rows: Symptoms and their status per day
        for i, symptom in enumerate(symptoms.SYMPTOM_LIST, start=1):
            # Symptom Label
            symptom_label = ttk.Label(self.calendar_frame, text=symptom, wraplength=200, relief="solid", borderwidth=1, padding=5)
            symptom_label.grid(row=i, column=0, sticky="nsew")

            # Daily status cells
            for day_num in range(1, days_in_month + 1):
                cell_color = "#f0f0f0" # Default color
                if not month_df.empty:
                    day_entries = month_df[month_df['timestamp'].dt.day == day_num]
                    if not day_entries.empty:
                        # Check if the symptom was present on this day
                        if any(symptom in entry_triggers for entry_triggers in day_entries['triggers'].str.split(', ')):
                            cell_color = "#ff7979" # Highlight color

                cell = tk.Label(self.calendar_frame, bg=cell_color, relief="solid", borderwidth=1)
                cell.grid(row=i, column=day_num, sticky="nsew")

        # Configure grid resizing
        self.calendar_frame.grid_columnconfigure(0, weight=1)
        for col in range(1, days_in_month + 2):
            self.calendar_frame.grid_columnconfigure(col, weight=1)
        for row in range(len(symptoms.SYMPTOM_LIST) + 1):
            self.calendar_frame.grid_rowconfigure(row, weight=1)

    def prev_month(self):
        self.current_date = self.current_date.replace(day=1) - pd.DateOffset(months=1)
        self.draw_calendar_view()

    def next_month(self):
        self.current_date = self.current_date.replace(day=1) + pd.DateOffset(months=1)
        self.draw_calendar_view()

    def open_new_entry_window(self):
        entry_window = tk.Toplevel(self.root)
        entry_window.title("Nowy Wpis")

        input_frame = ttk.LabelFrame(entry_window, text="Dodaj szczegóły głodu")
        input_frame.pack(padx=10, pady=10, fill="both", expand=True)

        ttk.Label(input_frame, text="Intensywność (1-10):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        intensity_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=intensity_var).grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(input_frame, text="Objawy/Wyzwalacze:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        ttk.Button(input_frame, text="Wybierz z listy", command=lambda: self.open_symptom_selector(entry_window)).grid(row=1, column=1, padx=5, pady=5, sticky="w")

        self.symptoms_display = tk.Text(input_frame, height=4, width=50, state="disabled", wrap="word")
        self.symptoms_display.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

        ttk.Label(input_frame, text="Sposób radzenia sobie:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        coping_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=coping_var).grid(row=3, column=1, padx=5, pady=5, sticky="ew")

        drank_var = tk.BooleanVar()
        ttk.Checkbutton(input_frame, text="Czy doszło do spożycia?", variable=drank_var).grid(row=4, column=0, columnspan=2, padx=5, pady=5, sticky="w")

        def save_and_close():
            self.save_entry(
                intensity_var.get(),
                coping_var.get(),
                drank_var.get()
            )
            entry_window.destroy()

        ttk.Button(input_frame, text="Zapisz", command=save_and_close).grid(row=5, column=0, columnspan=2, pady=10)

    def open_symptom_selector(self, parent):
        selector_window = tk.Toplevel(parent)
        selector_window.title("Wybierz Objawy")

        vars = []
        for symptom_text in symptoms.SYMPTOM_LIST:
            var = tk.BooleanVar()
            cb = ttk.Checkbutton(selector_window, text=symptom_text, variable=var, onvalue=True, offvalue=False)
            cb.pack(anchor='w', padx=10, pady=2)
            vars.append((var, symptom_text))

        def confirm_selection():
            self.selected_symptoms = [symptom_text for var, symptom_text in vars if var.get()]
            self.symptoms_display.config(state="normal")
            self.symptoms_display.delete(1.0, tk.END)
            self.symptoms_display.insert(tk.END, ", ".join(self.selected_symptoms))
            self.symptoms_display.config(state="disabled")
            selector_window.destroy()

        ttk.Button(selector_window, text="Zatwierdź", command=confirm_selection).pack(pady=10)

    def save_entry(self, intensity, coping, drank):
        triggers = ", ".join(self.selected_symptoms)
        if not intensity.isdigit() or not 1 <= int(intensity) <= 10:
            messagebox.showerror("Błąd", "Intensywność musi być liczbą od 1 do 10.")
            return
        if not triggers:
            messagebox.showerror("Błąd", "Proszę wybrać co najmniej jeden objaw/wyzwalacz.")
            return

        entry_data = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'intensity': intensity,
            'triggers': triggers,
            'coping_mechanism': coping,
            'drank': 'Tak' if drank else 'Nie'
        }
        data_manager.save_craving(entry_data)
        self.load_entries() # Redraw calendar
        self.clear_fields()
        messagebox.showinfo("Sukces", "Wpis został zapisany.")

    def clear_fields(self):
        self.selected_symptoms = []
        if hasattr(self, 'symptoms_display'):
            self.symptoms_display.config(state="normal")
            self.symptoms_display.delete(1.0, tk.END)
            self.symptoms_display.config(state="disabled")

    def load_entries(self):
        self.draw_calendar_view()

    # --- Other Tabs (Analysis, Settings) ---
    def create_analysis_widgets(self):
        # ... (This can be simplified or just launch Streamlit)
        ttk.Label(self.analysis_frame, text="Zaawansowana analiza jest dostępna w zewnętrznym panelu.", font=("Helvetica", 12)).pack(pady=20)
        ttk.Button(self.analysis_frame, text="Uruchom Panel Analizy (Streamlit)", command=self.launch_streamlit).pack(pady=10)

    def launch_streamlit(self):
        try:
            subprocess.Popen(["streamlit", "run", "viewer.py"])
        except FileNotFoundError:
            messagebox.showerror("Błąd", "Nie można uruchomić Streamlit. Upewnij się, że jest zainstalowany i dostępny w PATH.")

    def create_settings_widgets(self):
        email_settings_frame = ttk.LabelFrame(self.settings_frame, text="Ustawienia E-mail (SMTP)")
        email_settings_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.smtp_server_var = tk.StringVar()
        self.smtp_port_var = tk.StringVar()
        self.smtp_user_var = tk.StringVar()
        self.smtp_password_var = tk.StringVar()
        self.recipient_email_var = tk.StringVar()
        ttk.Label(email_settings_frame, text="Serwer SMTP:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(email_settings_frame, textvariable=self.smtp_server_var).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ttk.Label(email_settings_frame, text="Port SMTP:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(email_settings_frame, textvariable=self.smtp_port_var).grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        ttk.Label(email_settings_frame, text="Użytkownik (e-mail):").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(email_settings_frame, textvariable=self.smtp_user_var).grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        ttk.Label(email_settings_frame, text="Hasło:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(email_settings_frame, textvariable=self.smtp_password_var, show="*").grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        ttk.Label(email_settings_frame, text="E-mail odbiorcy:").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(email_settings_frame, textvariable=self.recipient_email_var).grid(row=4, column=1, padx=5, pady=5, sticky="ew")
        email_settings_frame.columnconfigure(1, weight=1)
        reminder_frame = ttk.LabelFrame(self.settings_frame, text="Ustawienia Przypomnień")
        reminder_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        self.reminders_enabled_var = tk.BooleanVar()
        ttk.Checkbutton(reminder_frame, text="Włącz codzienne przypomnienia", variable=self.reminders_enabled_var).grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        ttk.Label(reminder_frame, text="Godzina przypomnienia (HH:MM):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.reminder_time_var = tk.StringVar()
        ttk.Entry(reminder_frame, textvariable=self.reminder_time_var).grid(row=1, column=1, padx=5, pady=5, sticky="w")
        ttk.Button(self.settings_frame, text="Zapisz Ustawienia", command=self.save_app_settings).grid(row=2, column=0, padx=10, pady=10)
        ttk.Button(self.settings_frame, text="Wyślij E-mail Testowy", command=self.send_test_email_action).grid(row=3, column=0, padx=10, pady=10)

    def load_app_settings(self):
        settings = settings_manager.load_settings()
        self.smtp_server_var.set(settings.get("smtp_server", ""))
        self.smtp_port_var.set(str(settings.get("smtp_port", 587)))
        self.smtp_user_var.set(settings.get("smtp_user", ""))
        self.smtp_password_var.set(settings.get("smtp_password", ""))
        self.recipient_email_var.set(settings.get("recipient_email", ""))
        self.reminders_enabled_var.set(settings.get("reminders_enabled", False))
        self.reminder_time_var.set(settings.get("reminder_time", "20:00"))

    def save_app_settings(self):
        try:
            port = int(self.smtp_port_var.get())
        except ValueError:
            messagebox.showerror("Błąd", "Port SMTP musi być liczbą.")
            return
        settings = {
            "smtp_server": self.smtp_server_var.get(),
            "smtp_port": port,
            "smtp_user": self.smtp_user_var.get(),
            "smtp_password": self.smtp_password_var.get(),
            "recipient_email": self.recipient_email_var.get(),
            "reminders_enabled": self.reminders_enabled_var.get(),
            "reminder_time": self.reminder_time_var.get()
        }
        settings_manager.save_settings(settings)
        messagebox.showinfo("Sukces", "Ustawienia zostały zapisane. Aplikacja może wymagać ponownego uruchomienia, aby zmiany w harmonogramie zostały zastosowane.")

    def send_test_email_action(self):
        subject = "Testowy e-mail z Dzienniczka Głodów Alkoholowych"
        body = "To jest testowa wiadomość, aby sprawdzić, czy ustawienia e-mail są poprawne."
        result = email_notifier.send_email(subject, body)
        messagebox.showinfo("Wynik Wysyłania E-maila", result)

if __name__ == "__main__":
    root = tk.Tk()
    app = CravingApp(root)
    root.mainloop()