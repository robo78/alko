import tkinter as tk
from tkinter import ttk, messagebox
import data_manager
import analysis
import settings_manager
import email_notifier
import reminder_scheduler
import symptoms
import calendar_marks_manager
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
        self.templates = []
        self.cell_marks = calendar_marks_manager.load_marks()
        self.current_date = datetime.now()
        self.scale_levels = [str(level) for level in range(1, 11)]
        self.symptom_column_width = 200
        self._resizing_symptom_column = False

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
        self.load_entries()
        reminder_scheduler.start_scheduler_thread()

    def create_journal_widgets(self):
        control_frame = ttk.Frame(self.journal_frame)
        control_frame.pack(fill='x', padx=10, pady=5)
        ttk.Button(control_frame, text="< Poprzedni Miesiąc", command=self.prev_month).pack(side='left')
        self.month_year_label = ttk.Label(control_frame, text="", font=("Helvetica", 14, "bold"))
        self.month_year_label.pack(side='left', expand=True)
        ttk.Button(control_frame, text="Następny Miesiąc >", command=self.next_month).pack(side='right')

        self.calendar_frame = ttk.Frame(self.journal_frame)
        self.calendar_frame.pack(fill="both", expand=True, padx=10, pady=10)

    def draw_calendar_view(self):
        for widget in self.calendar_frame.winfo_children():
            widget.destroy()
        self.month_year_label.config(text=self.current_date.strftime("%B %Y"))

        all_entries = data_manager.load_cravings()
        df = pd.DataFrame(all_entries)
        if not df.empty and 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            month_df = df[df['timestamp'].dt.to_period('M') == pd.Period(self.current_date, 'M')]
        else:
            month_df = pd.DataFrame()

        days_in_month = calendar.monthrange(self.current_date.year, self.current_date.month)[1]

        self.symptom_labels = []

        header_label = ttk.Label(
            self.calendar_frame,
            text="Objaw / Wyzwalacz",
            font=("Helvetica", 10, "bold"),
            relief="solid",
            borderwidth=1,
            padding=5,
            anchor="w"
        )
        header_label.grid(row=0, column=0, sticky="nsew")
        header_label.configure(wraplength=self.symptom_column_width - 10)

        resizer = tk.Frame(self.calendar_frame, width=6, cursor="sb_h_double_arrow", bg="#d0d0d0")
        resizer.grid(row=0, column=1, rowspan=len(symptoms.SYMPTOM_LIST) + 1, sticky="ns")
        resizer.bind("<ButtonPress-1>", self.start_resizing_symptom_column)
        resizer.bind("<B1-Motion>", self.perform_resizing_symptom_column)
        resizer.bind("<ButtonRelease-1>", self.finish_resizing_symptom_column)
        self._symptom_header_label = header_label

        for day_num in range(1, days_in_month + 1):
            date = datetime(self.current_date.year, self.current_date.month, day_num)
            day_button = ttk.Button(self.calendar_frame, text=str(day_num), command=lambda d=date: self.open_new_entry_window(d))
            day_button.grid(row=0, column=day_num + 1, sticky="nsew")

        self.cell_marks = calendar_marks_manager.load_marks()

        for i, symptom in enumerate(symptoms.SYMPTOM_LIST, start=1):
            symptom_label = ttk.Label(
                self.calendar_frame,
                text=symptom,
                wraplength=self.symptom_column_width - 10,
                relief="solid",
                borderwidth=1,
                padding=5,
                anchor="w"
            )
            symptom_label.grid(row=i, column=0, sticky="nsew")
            self.symptom_labels.append(symptom_label)
            for day_num in range(1, days_in_month + 1):
                cell_color = "#f0f0f0"
                cell_text = ""
                date_str = datetime(self.current_date.year, self.current_date.month, day_num).strftime("%Y-%m-%d")
                mark_template = calendar_marks_manager.get_template(date_str, symptom, self.cell_marks)
                if mark_template is not None:
                    cell_color = "#ff7979"
                    cell_text = mark_template if mark_template else "✓"
                if not month_df.empty:
                    day_entries = month_df[month_df['timestamp'].dt.day == day_num]
                    if not day_entries.empty and 'triggers' in day_entries.columns:
                        symptom_present = day_entries['triggers'].str.contains(symptom, na=False).any()
                        if symptom_present:
                            cell_color = "#ffb3b3" if mark_template is None else cell_color
                cell = tk.Label(self.calendar_frame, bg=cell_color, relief="solid", borderwidth=1, text=cell_text)
                cell.grid(row=i, column=day_num + 1, sticky="nsew")
                cell.bind("<Button-1>", lambda e, s=symptom, d=day_num: self.handle_cell_click(e, s, d))
                cell.bind("<Button-3>", lambda e, s=symptom, d=day_num: self.open_cell_menu(e, s, d))
                cell.configure(cursor="hand2")

        self.calendar_frame.grid_columnconfigure(0, weight=0, minsize=self.symptom_column_width)
        self.calendar_frame.grid_columnconfigure(1, weight=0, minsize=6)
        for col in range(2, days_in_month + 2):
            self.calendar_frame.grid_columnconfigure(col, weight=1, uniform="group1")
        for row in range(len(symptoms.SYMPTOM_LIST) + 1):
            self.calendar_frame.grid_rowconfigure(row, weight=1, uniform="group1")

    def handle_cell_click(self, event, symptom, day_num):
        date = datetime(self.current_date.year, self.current_date.month, day_num)
        date_str = date.strftime("%Y-%m-%d")
        if calendar_marks_manager.is_marked(date_str, symptom, self.cell_marks):
            previous_value = calendar_marks_manager.get_template(date_str, symptom, self.cell_marks)
            self.cell_marks = calendar_marks_manager.remove_mark(date_str, symptom, self.cell_marks)
            self.draw_calendar_view()
            self.open_cell_menu(event, symptom, day_num, date_str=date_str, previous_value=previous_value)
        else:
            default_template = self.templates[0] if self.templates else ""
            self.cell_marks = calendar_marks_manager.set_mark(date_str, symptom, default_template, self.cell_marks)
            self.draw_calendar_view()
            self.open_cell_menu(event, symptom, day_num, date_str=date_str)

    def open_cell_menu(self, event, symptom, day_num, date_str=None, previous_value=None):
        if date_str is None:
            date = datetime(self.current_date.year, self.current_date.month, day_num)
            date_str = date.strftime("%Y-%m-%d")
        menu = tk.Menu(self.root, tearoff=0)
        is_marked = calendar_marks_manager.is_marked(date_str, symptom, self.cell_marks)
        if is_marked:
            menu.add_command(label="Usuń zaznaczenie", command=lambda: self.remove_cell_mark(date_str, symptom))
        else:
            menu.add_command(label="Zaznacz głód", command=lambda: self.assign_template(date_str, symptom, self.templates[0] if self.templates else ""))

        scale_menu = tk.Menu(menu, tearoff=0)
        current_value = calendar_marks_manager.get_template(date_str, symptom, self.cell_marks)
        if current_value:
            menu.add_command(label=f"Aktualna skala: {current_value}", state="disabled")
            menu.add_separator()
        elif previous_value:
            menu.add_command(label=f"Poprzednia skala: {previous_value}", state="disabled")
            menu.add_separator()
        menu.add_cascade(label="Skala głodu", menu=scale_menu)
        for level in self.scale_levels:
            scale_menu.add_command(
                label=f"{level}",
                command=lambda l=level: self.assign_template(date_str, symptom, l)
            )

        if self.templates:
            templates_menu = tk.Menu(menu, tearoff=0)
            for template in self.templates:
                templates_menu.add_command(
                    label=template,
                    command=lambda t=template: self.assign_template(date_str, symptom, t)
                )
            menu.add_cascade(label="Szablony", menu=templates_menu)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def start_resizing_symptom_column(self, event):
        self._resizing_symptom_column = True
        self._resize_start_x = event.x_root
        self._initial_symptom_width = self.symptom_column_width

    def perform_resizing_symptom_column(self, event):
        if not self._resizing_symptom_column:
            return
        delta = event.x_root - self._resize_start_x
        new_width = max(80, self._initial_symptom_width + delta)
        self.symptom_column_width = new_width
        self.calendar_frame.grid_columnconfigure(0, minsize=self.symptom_column_width)
        wrap_value = max(10, self.symptom_column_width - 10)
        if hasattr(self, "_symptom_header_label"):
            self._symptom_header_label.configure(wraplength=wrap_value)
        for label in getattr(self, "symptom_labels", []):
            label.configure(wraplength=wrap_value)

    def finish_resizing_symptom_column(self, event):
        self._resizing_symptom_column = False

    def assign_template(self, date_str, symptom, template):
        self.cell_marks = calendar_marks_manager.set_mark(date_str, symptom, template, self.cell_marks)
        self.draw_calendar_view()

    def remove_cell_mark(self, date_str, symptom):
        self.cell_marks = calendar_marks_manager.remove_mark(date_str, symptom, self.cell_marks)
        self.draw_calendar_view()

    def prev_month(self):
        self.current_date -= pd.DateOffset(months=1)
        self.draw_calendar_view()

    def next_month(self):
        self.current_date += pd.DateOffset(months=1)
        self.draw_calendar_view()

    def open_new_entry_window(self, date):
        entry_window = tk.Toplevel(self.root)
        entry_window.title(f"Nowy Wpis - {date.strftime('%Y-%m-%d')}")
        input_frame = ttk.LabelFrame(entry_window, text="Dodaj szczegóły głodu")
        input_frame.pack(padx=10, pady=10, fill="both", expand=True)
        ttk.Label(input_frame, text="Intensywność (1-10):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        intensity_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=intensity_var).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ttk.Label(input_frame, text="Objawy/Wyzwalacze:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.symptoms_display = tk.Text(input_frame, height=4, width=50, state="disabled", wrap="word")
        self.symptoms_display.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        ttk.Button(input_frame, text="Wybierz z listy", command=lambda: self.open_symptom_selector(entry_window)).grid(row=1, column=1, padx=5, pady=5, sticky="w")
        ttk.Label(input_frame, text="Sposób radzenia sobie:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        coping_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=coping_var).grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        drank_var = tk.BooleanVar()
        ttk.Checkbutton(input_frame, text="Czy doszło do spożycia?", variable=drank_var).grid(row=4, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        def save_and_close():
            self.save_entry(date, intensity_var.get(), coping_var.get(), drank_var.get())
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

    def save_entry(self, date, intensity, coping, drank):
        triggers = ", ".join(self.selected_symptoms)
        if not intensity.isdigit() or not 1 <= int(intensity) <= 10:
            messagebox.showerror("Błąd", "Intensywność musi być liczbą od 1 do 10.")
            return
        if not triggers:
            messagebox.showerror("Błąd", "Proszę wybrać co najmniej jeden objaw/wyzwalacz.")
            return
        now = datetime.now()
        timestamp_obj = date.replace(hour=now.hour, minute=now.minute, second=now.second)
        timestamp = timestamp_obj.strftime("%Y-%m-%d %H:%M:%S")
        entry_data = {'timestamp': timestamp, 'intensity': intensity, 'triggers': triggers, 'coping_mechanism': coping, 'drank': 'Tak' if drank else 'Nie'}
        data_manager.save_craving(entry_data)
        self.load_entries()
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
        self.update_analysis_tab()

    def create_analysis_widgets(self):
        stats_frame = ttk.LabelFrame(self.analysis_frame, text="Podsumowanie")
        stats_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.total_entries_label = ttk.Label(stats_frame, text="Liczba wpisów: N/A")
        self.total_entries_label.grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.avg_intensity_label = ttk.Label(stats_frame, text="Średnia intensywność: N/A")
        self.avg_intensity_label.grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.common_trigger_label = ttk.Label(stats_frame, text="Najczęstszy wyzwalacz: N/A")
        self.common_trigger_label.grid(row=2, column=0, padx=5, pady=2, sticky="w")
        self.used_coping_label = ttk.Label(stats_frame, text="Najczęstszy sposób radzenia sobie: N/A")
        self.used_coping_label.grid(row=3, column=0, padx=5, pady=2, sticky="w")
        self.plot_frame = ttk.LabelFrame(self.analysis_frame, text="Wykres Intensywności")
        self.plot_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        ttk.Button(self.analysis_frame, text="Uruchom Zaawansowany Panel Analizy (Streamlit)", command=self.launch_streamlit).grid(row=2, column=0, pady=20)
        self.analysis_frame.columnconfigure(0, weight=1)
        self.analysis_frame.rowconfigure(1, weight=1)

    def update_analysis_tab(self):
        entries = data_manager.load_cravings()
        if not entries: return
        stats = analysis.get_summary_stats(entries)
        self.total_entries_label.config(text=f"Liczba wpisów: {stats['total_entries']}")
        self.avg_intensity_label.config(text=f"Średnia intensywność: {stats['avg_intensity']}")
        self.common_trigger_label.config(text=f"Najczęstszy wyzwalacz: {stats['most_common_trigger']}")
        self.used_coping_label.config(text=f"Najczęstszy sposób radzenia sobie: {stats['most_used_coping']}")
        analysis.create_intensity_plot(self.plot_frame, entries)

    def launch_streamlit(self):
        try:
            subprocess.Popen(["streamlit", "run", "viewer.py"])
        except FileNotFoundError:
            messagebox.showerror("Błąd", "Nie można uruchomić Streamlit. Upewnij się, że jest zainstalowany i dostępny w PATH.")

    def create_settings_widgets(self):
        email_settings_frame = ttk.LabelFrame(self.settings_frame, text="Ustawienia E-mail (SMTP)")
        email_settings_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.smtp_server_var, self.smtp_port_var, self.smtp_user_var, self.smtp_password_var, self.recipient_email_var = tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.StringVar()
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
        self.reminders_enabled_var, self.reminder_time_var = tk.BooleanVar(), tk.StringVar()
        ttk.Checkbutton(reminder_frame, text="Włącz codzienne przypomnienia", variable=self.reminders_enabled_var).grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        ttk.Label(reminder_frame, text="Godzina przypomnienia (HH:MM):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(reminder_frame, textvariable=self.reminder_time_var).grid(row=1, column=1, padx=5, pady=5, sticky="w")
        templates_frame = ttk.LabelFrame(self.settings_frame, text="Szablony zaznaczeń")
        templates_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        ttk.Label(templates_frame, text="Podaj nazwy szablonów (jeden na linię):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.templates_text = tk.Text(templates_frame, height=5, width=40)
        self.templates_text.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        templates_frame.columnconfigure(0, weight=1)
        ttk.Button(self.settings_frame, text="Zapisz Ustawienia", command=self.save_app_settings).grid(row=3, column=0, padx=10, pady=10)
        ttk.Button(self.settings_frame, text="Wyślij E-mail Testowy", command=self.send_test_email_action).grid(row=4, column=0, padx=10, pady=10)

    def load_app_settings(self):
        settings = settings_manager.load_settings()
        self.smtp_server_var.set(settings.get("smtp_server", ""))
        self.smtp_port_var.set(str(settings.get("smtp_port", 587)))
        self.smtp_user_var.set(settings.get("smtp_user", ""))
        self.smtp_password_var.set(settings.get("smtp_password", ""))
        self.recipient_email_var.set(settings.get("recipient_email", ""))
        self.reminders_enabled_var.set(settings.get("reminders_enabled", False))
        self.reminder_time_var.set(settings.get("reminder_time", "20:00"))
        self.templates = settings.get("templates", [])
        if hasattr(self, 'templates_text'):
            self.templates_text.delete("1.0", tk.END)
            self.templates_text.insert(tk.END, "\n".join(self.templates))
        self.draw_calendar_view()

    def save_app_settings(self):
        try: port = int(self.smtp_port_var.get())
        except ValueError: messagebox.showerror("Błąd", "Port SMTP musi być liczbą."); return
        templates_raw = self.templates_text.get("1.0", tk.END) if hasattr(self, 'templates_text') else ""
        templates = [line.strip() for line in templates_raw.splitlines() if line.strip()]
        settings = {"smtp_server": self.smtp_server_var.get(), "smtp_port": port, "smtp_user": self.smtp_user_var.get(), "smtp_password": self.smtp_password_var.get(), "recipient_email": self.recipient_email_var.get(), "reminders_enabled": self.reminders_enabled_var.get(), "reminder_time": self.reminder_time_var.get(), "templates": templates}
        self.templates = templates
        settings_manager.save_settings(settings)
        messagebox.showinfo("Sukces", "Ustawienia zostały zapisane. Aplikacja może wymagać ponownego uruchomienia, aby zmiany w harmonogramie zostały zastosowane.")
        self.draw_calendar_view()

    def send_test_email_action(self):
        result = email_notifier.send_email("Testowy e-mail z Dzienniczka Głodów Alkoholowych", "To jest testowa wiadomość, aby sprawdzić, czy ustawienia e-mail są poprawne.")
        messagebox.showinfo("Wynik Wysyłania E-maila", result)

if __name__ == "__main__":
    root = tk.Tk()
    app = CravingApp(root)
    root.mainloop()