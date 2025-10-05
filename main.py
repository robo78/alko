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
        self.default_template_background = "#ff7979"
        self.default_template_foreground = "#000000"
        self.font_size = 10
        self.cell_marks = calendar_marks_manager.load_marks()
        self.current_date = datetime.now()
        self.scale_levels = [str(level) for level in range(1, 11)]
        self.symptom_column_width = 200
        self._resizing_symptom_column = False
        self._resizer_width = 6
        self._calendar_cells = []

        # --- Main Layout ---
        self.style = ttk.Style()

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
        self.month_year_label = ttk.Label(control_frame, text="", font=self._get_title_font())
        self.month_year_label.pack(side='left', expand=True)
        ttk.Button(control_frame, text="Następny Miesiąc >", command=self.next_month).pack(side='right')

        self.calendar_frame = ttk.Frame(self.journal_frame)
        self.calendar_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.calendar_frame.bind("<Configure>", self._on_calendar_resize)

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
        self._days_in_current_month = days_in_month

        self.symptom_labels = []
        self._calendar_cells = []

        header_label = ttk.Label(
            self.calendar_frame,
            text="Objaw / Wyzwalacz",
            font=self._get_font(weight="bold"),
            relief="solid",
            borderwidth=1,
            padding=5,
            anchor="w"
        )
        header_label.grid(row=0, column=0, sticky="nsew")
        header_label.configure(wraplength=self.symptom_column_width - 10)

        resizer = tk.Frame(self.calendar_frame, width=self._resizer_width, cursor="sb_h_double_arrow", bg="#d0d0d0")
        resizer.grid(row=0, column=1, rowspan=len(symptoms.SYMPTOM_LIST) + 1, sticky="ns")
        resizer.bind("<ButtonPress-1>", self.start_resizing_symptom_column)
        resizer.bind("<B1-Motion>", self.perform_resizing_symptom_column)
        resizer.bind("<ButtonRelease-1>", self.finish_resizing_symptom_column)
        self._symptom_header_label = header_label

        for day_num in range(1, days_in_month + 1):
            date = datetime(self.current_date.year, self.current_date.month, day_num)
            day_button = ttk.Button(
                self.calendar_frame,
                text=str(day_num),
                command=lambda d=date: self.open_new_entry_window(d)
            )
            day_button.configure(style="Day.TButton")
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
                anchor="w",
                font=self._get_font()
            )
            symptom_label.grid(row=i, column=0, sticky="nsew")
            self.symptom_labels.append(symptom_label)
            for day_num in range(1, days_in_month + 1):
                cell_color = "#f0f0f0"
                cell_text = ""
                date_str = datetime(self.current_date.year, self.current_date.month, day_num).strftime("%Y-%m-%d")
                mark_data = calendar_marks_manager.get_mark(date_str, symptom, self.cell_marks)
                text_color = "#000000"
                if mark_data is not None:
                    template_name = mark_data.get("template")
                    scale_value = mark_data.get("scale")
                    template_info = self._get_template_by_name(template_name) if template_name else None
                    if template_info:
                        cell_color = template_info.get("background", cell_color)
                        text_color = template_info.get("foreground", text_color)
                    else:
                        cell_color = "#ff7979"
                    cell_text = scale_value if scale_value else "✓"
                if not month_df.empty:
                    day_entries = month_df[month_df['timestamp'].dt.day == day_num]
                    if not day_entries.empty and 'triggers' in day_entries.columns:
                        symptom_present = day_entries['triggers'].str.contains(symptom, na=False).any()
                        if symptom_present and mark_data is None:
                            cell_color = "#ffb3b3"
                cell = tk.Label(
                    self.calendar_frame,
                    bg=cell_color,
                    fg=text_color,
                    relief="solid",
                    borderwidth=1,
                    text=cell_text,
                    font=self._get_font()
                )
                cell.grid(row=i, column=day_num + 1, sticky="nsew")
                cell.bind("<Button-1>", lambda e, s=symptom, d=day_num: self.handle_cell_click(e, s, d))
                cell.bind("<Button-3>", lambda e, s=symptom, d=day_num: self.open_cell_menu(e, s, d))
                cell.bind("<Enter>", lambda e, c=cell: self._on_cell_enter(c))
                cell.bind("<Leave>", lambda e, c=cell: self._on_cell_leave(c))
                cell.original_bg = cell_color
                cell.original_fg = text_color
                initial_thickness = int(cell.cget("highlightthickness") or 0)
                cell.original_highlightthickness = max(1, initial_thickness)
                cell.configure(
                    cursor="hand2",
                    highlightthickness=cell.original_highlightthickness,
                    highlightbackground="#b3b3b3"
                )
                cell.original_highlightbackground = "#b3b3b3"
                self._calendar_cells.append(cell)

        self.calendar_frame.grid_columnconfigure(0, weight=0, minsize=self.symptom_column_width)
        self.calendar_frame.grid_columnconfigure(1, weight=0, minsize=self._resizer_width)
        for col in range(2, days_in_month + 2):
            self.calendar_frame.grid_columnconfigure(col, weight=1, uniform="group1")
        for row in range(len(symptoms.SYMPTOM_LIST) + 1):
            self.calendar_frame.grid_rowconfigure(row, weight=1, uniform="group1")
        self._apply_current_fonts()

        self.calendar_frame.after_idle(lambda: self._on_calendar_resize(None))

    def handle_cell_click(self, event, symptom, day_num):
        if event:
            event.widget.focus_set()
        date = datetime(self.current_date.year, self.current_date.month, day_num)
        date_str = date.strftime("%Y-%m-%d")
        if calendar_marks_manager.is_marked(date_str, symptom, self.cell_marks):
            previous_value = calendar_marks_manager.get_template(date_str, symptom, self.cell_marks)
            self.cell_marks = calendar_marks_manager.remove_mark(date_str, symptom, self.cell_marks)
            self.draw_calendar_view()
            self.open_cell_menu(event, symptom, day_num, date_str=date_str, previous_value=previous_value)
        else:
            default_template = self.templates[0]["name"] if self.templates else ""
            self.cell_marks = calendar_marks_manager.set_mark(date_str, symptom, template=default_template, marks=self.cell_marks)
        self.draw_calendar_view()

    def open_cell_menu(self, event, symptom, day_num, date_str=None, previous_value=None):
        if date_str is None:
            date = datetime(self.current_date.year, self.current_date.month, day_num)
            date_str = date.strftime("%Y-%m-%d")
        menu = tk.Menu(self.root, tearoff=0)
        is_marked = calendar_marks_manager.is_marked(date_str, symptom, self.cell_marks)
        if is_marked:
            menu.add_command(label="Usuń zaznaczenie", command=lambda: self.remove_cell_mark(date_str, symptom))
        else:
            menu.add_command(label="Zaznacz głód", command=lambda: self.assign_template(date_str, symptom, self.templates[0]["name"] if self.templates else ""))

        scale_menu = tk.Menu(menu, tearoff=0)
        current_mark = calendar_marks_manager.get_mark(date_str, symptom, self.cell_marks)
        current_value = current_mark.get("scale") if current_mark else None
        current_template = current_mark.get("template") if current_mark else None
        if current_value:
            menu.add_command(label=f"Aktualna skala: {current_value}", state="disabled")
            menu.add_separator()
        menu.add_cascade(label="Skala głodu", menu=scale_menu)
        for level in self.scale_levels:
            scale_menu.add_command(
                label=f"{level}",
                command=lambda l=level: self.assign_scale(date_str, symptom, l)
            )

        if self.templates:
            templates_menu = tk.Menu(menu, tearoff=0)
            for template in self.templates:
                label = template["name"]
                if current_template and current_template == label:
                    label = f"{label} (aktywny)"
                templates_menu.add_command(
                    label=label,
                    command=lambda t=template["name"]: self.assign_template(date_str, symptom, t)
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
        self._on_calendar_resize(None)

    def finish_resizing_symptom_column(self, event):
        self._resizing_symptom_column = False

    def _on_cell_enter(self, cell):
        original_bg = getattr(cell, "original_bg", cell.cget("bg"))
        hover_color = self._calculate_hover_color(original_bg)
        cell.configure(
            bg=hover_color,
            highlightthickness=max(2, getattr(cell, "original_highlightthickness", 1)),
            highlightbackground="#333333"
        )

    def _on_cell_leave(self, cell):
        cell.configure(
            bg=getattr(cell, "original_bg", cell.cget("bg")),
            highlightthickness=getattr(cell, "original_highlightthickness", 1),
            highlightbackground=getattr(cell, "original_highlightbackground", "#b3b3b3")
        )

    def _calculate_hover_color(self, hex_color):
        if not hex_color.startswith("#") or len(hex_color) not in (4, 7):
            return "#d9d9d9"
        if len(hex_color) == 4:
            hex_color = "#" + "".join(ch * 2 for ch in hex_color[1:])
        try:
            r = int(hex_color[1:3], 16)
            g = int(hex_color[3:5], 16)
            b = int(hex_color[5:7], 16)
        except ValueError:
            return "#d9d9d9"
        lighten = lambda component: min(255, int(component + (255 - component) * 0.35))
        hover_r = lighten(r)
        hover_g = lighten(g)
        hover_b = lighten(b)
        return f"#{hover_r:02x}{hover_g:02x}{hover_b:02x}"

    def _on_calendar_resize(self, event):
        days_in_month = getattr(self, "_days_in_current_month", 0)
        if not days_in_month:
            return
        total_width = max(1, self.calendar_frame.winfo_width())
        total_height = max(1, self.calendar_frame.winfo_height())
        row_count = len(symptoms.SYMPTOM_LIST) + 1
        if row_count <= 0:
            return
        available_width = max(1, total_width - self.symptom_column_width - self._resizer_width)
        available_height = max(1, total_height)
        cell_size = min(available_width / days_in_month, available_height / row_count)
        cell_size = max(1, cell_size)
        for col in range(2, days_in_month + 2):
            self.calendar_frame.grid_columnconfigure(col, minsize=int(cell_size))
        for row in range(0, len(symptoms.SYMPTOM_LIST) + 1):
            self.calendar_frame.grid_rowconfigure(row, minsize=int(cell_size))
        for cell in getattr(self, "_calendar_cells", []):
            cell.original_bg = cell.original_bg if hasattr(cell, "original_bg") else cell.cget("bg")

    def _get_template_by_name(self, name):
        if not name:
            return None
        for template in self.templates:
            if template.get("name") == name:
                return template
        return None

    def _normalize_font_size(self, value):
        try:
            size = int(value)
        except (TypeError, ValueError):
            size = self.font_size
        return max(8, min(32, size))

    def _get_font(self, weight="normal"):
        size = max(8, int(self.font_size))
        weight = (weight or "").lower()
        if weight == "bold":
            return ("Helvetica", size, "bold")
        return ("Helvetica", size)

    def _get_title_font(self):
        base_size = max(8, int(self.font_size))
        return ("Helvetica", max(base_size + 4, 12), "bold")

    def _apply_current_fonts(self):
        if hasattr(self, "month_year_label"):
            self.month_year_label.configure(font=self._get_title_font())
        if hasattr(self, "style"):
            self.style.configure("Day.TButton", font=self._get_font())
        if hasattr(self, "_symptom_header_label"):
            self._symptom_header_label.configure(font=self._get_font(weight="bold"))
        for label in getattr(self, "symptom_labels", []):
            label.configure(font=self._get_font())
        for cell in getattr(self, "_calendar_cells", []):
            cell.configure(font=self._get_font())

    def _normalize_templates(self, templates_raw):
        normalized = []
        for item in templates_raw:
            if isinstance(item, dict):
                name = str(item.get("name", "")).strip()
                if not name:
                    continue
                background = item.get("background") or item.get("bg") or self.default_template_background
                foreground = item.get("foreground") or item.get("fg") or self.default_template_foreground
                normalized.append({
                    "name": name,
                    "background": background,
                    "foreground": foreground,
                })
            elif isinstance(item, str):
                name = item.strip()
                if not name:
                    continue
                normalized.append({
                    "name": name,
                    "background": self.default_template_background,
                    "foreground": self.default_template_foreground,
                })
        return normalized

    def _format_template_line(self, template):
        name = template.get("name", "")
        background = template.get("background", self.default_template_background)
        foreground = template.get("foreground", self.default_template_foreground)
        if foreground == self.default_template_foreground:
            return f"{name};{background}"
        return f"{name};{background};{foreground}"

    def _parse_templates_input(self, raw_text):
        templates = []
        for line in raw_text.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = [part.strip() for part in line.split(';')]
            if not parts:
                continue
            name = parts[0]
            if not name:
                continue
            background = parts[1] if len(parts) > 1 and parts[1] else self.default_template_background
            foreground = parts[2] if len(parts) > 2 and parts[2] else self.default_template_foreground
            templates.append({
                "name": name,
                "background": background,
                "foreground": foreground,
            })
        return templates

    def assign_template(self, date_str, symptom, template):
        self.cell_marks = calendar_marks_manager.update_mark(date_str, symptom, template=template, marks=self.cell_marks)
        self.draw_calendar_view()

    def assign_scale(self, date_str, symptom, scale):
        self.cell_marks = calendar_marks_manager.update_mark(date_str, symptom, scale=scale, marks=self.cell_marks)
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
        self.common_pair_label = ttk.Label(stats_frame, text="Najczęstsza para wyzwalaczy: N/A")
        self.common_pair_label.grid(row=4, column=0, padx=5, pady=2, sticky="w")
        self.sequence_label = ttk.Label(stats_frame, text="Najczęstsza sekwencja dni: N/A")
        self.sequence_label.grid(row=5, column=0, padx=5, pady=2, sticky="w")
        self.weekday_weekend_label = ttk.Label(stats_frame, text="Dni robocze vs weekend: N/A")
        self.weekday_weekend_label.grid(row=6, column=0, padx=5, pady=2, sticky="w")
        self.plot_frame = ttk.LabelFrame(self.analysis_frame, text="Wykres Intensywności")
        self.plot_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        ttk.Button(self.analysis_frame, text="Uruchom Zaawansowany Panel Analizy (Streamlit)", command=self.launch_streamlit).grid(row=2, column=0, pady=20)
        self.analysis_frame.columnconfigure(0, weight=1)
        self.analysis_frame.rowconfigure(1, weight=1)

    def update_analysis_tab(self):
        entries = data_manager.load_cravings()
        stats = analysis.get_summary_stats(entries)
        self.total_entries_label.config(text=f"Liczba wpisów: {stats['total_entries']}")
        self.avg_intensity_label.config(text=f"Średnia intensywność: {stats['avg_intensity']}")
        self.common_trigger_label.config(text=f"Najczęstszy wyzwalacz: {stats['most_common_trigger']}")
        self.used_coping_label.config(text=f"Najczęstszy sposób radzenia sobie: {stats['most_used_coping']}")
        self.common_pair_label.config(text=f"Najczęstsza para wyzwalaczy: {stats['most_common_pair']}")
        self.sequence_label.config(text=f"Najczęstsza sekwencja dni: {stats['most_common_sequence']}")
        distribution = stats.get('workday_weekend_distribution', {"workdays": 0, "weekend": 0})
        self.weekday_weekend_label.config(
            text=f"Dni robocze vs weekend: {distribution.get('workdays', 0)} / {distribution.get('weekend', 0)}"
        )
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
        ttk.Label(
            templates_frame,
            text="Podaj szablony kolorów w formacie: nazwa;#kolor_tła;#kolor_tekstu (ostatni parametr opcjonalny)"
        ).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.templates_text = tk.Text(templates_frame, height=5, width=40)
        self.templates_text.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        templates_frame.columnconfigure(0, weight=1)
        appearance_frame = ttk.LabelFrame(self.settings_frame, text="Wygląd")
        appearance_frame.grid(row=3, column=0, padx=10, pady=10, sticky="ew")
        ttk.Label(appearance_frame, text="Rozmiar czcionki (8-32):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.font_size_var = tk.IntVar(value=self.font_size)
        self.font_size_spinbox = tk.Spinbox(
            appearance_frame,
            from_=8,
            to=32,
            increment=1,
            textvariable=self.font_size_var,
            width=5,
            wrap=False
        )
        self.font_size_spinbox.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        appearance_frame.columnconfigure(1, weight=1)
        ttk.Button(self.settings_frame, text="Zapisz Ustawienia", command=self.save_app_settings).grid(row=4, column=0, padx=10, pady=10)
        ttk.Button(self.settings_frame, text="Wyślij E-mail Testowy", command=self.send_test_email_action).grid(row=5, column=0, padx=10, pady=10)

    def load_app_settings(self):
        settings = settings_manager.load_settings()
        self.smtp_server_var.set(settings.get("smtp_server", ""))
        self.smtp_port_var.set(str(settings.get("smtp_port", 587)))
        self.smtp_user_var.set(settings.get("smtp_user", ""))
        self.smtp_password_var.set(settings.get("smtp_password", ""))
        self.recipient_email_var.set(settings.get("recipient_email", ""))
        self.reminders_enabled_var.set(settings.get("reminders_enabled", False))
        self.reminder_time_var.set(settings.get("reminder_time", "20:00"))
        self.font_size = self._normalize_font_size(settings.get("font_size", self.font_size))
        if hasattr(self, "font_size_var"):
            self.font_size_var.set(self.font_size)
        self.templates = self._normalize_templates(settings.get("templates", []))
        if hasattr(self, 'templates_text'):
            self.templates_text.delete("1.0", tk.END)
            formatted = "\n".join(self._format_template_line(tpl) for tpl in self.templates)
            self.templates_text.insert(tk.END, formatted)
        self._apply_current_fonts()
        self.draw_calendar_view()

    def save_app_settings(self):
        try:
            port = int(self.smtp_port_var.get())
        except ValueError:
            messagebox.showerror("Błąd", "Port SMTP musi być liczbą.")
            return
        templates_raw = self.templates_text.get("1.0", tk.END) if hasattr(self, 'templates_text') else ""
        templates = self._normalize_templates(self._parse_templates_input(templates_raw))
        font_size_value = self._normalize_font_size(self.font_size_var.get() if hasattr(self, 'font_size_var') else self.font_size)
        self.font_size = font_size_value
        settings = {
            "smtp_server": self.smtp_server_var.get(),
            "smtp_port": port,
            "smtp_user": self.smtp_user_var.get(),
            "smtp_password": self.smtp_password_var.get(),
            "recipient_email": self.recipient_email_var.get(),
            "reminders_enabled": self.reminders_enabled_var.get(),
            "reminder_time": self.reminder_time_var.get(),
            "templates": templates,
            "font_size": font_size_value,
        }
        self.templates = templates
        if hasattr(self, 'templates_text'):
            self.templates_text.delete("1.0", tk.END)
            formatted = "\n".join(self._format_template_line(tpl) for tpl in self.templates)
            self.templates_text.insert(tk.END, formatted)
        settings_manager.save_settings(settings)
        self._apply_current_fonts()
        messagebox.showinfo(
            "Sukces",
            "Ustawienia zostały zapisane. Aplikacja może wymagać ponownego uruchomienia, aby zmiany w harmonogramie zostały zastosowane."
        )
        self.draw_calendar_view()

    def send_test_email_action(self):
        result = email_notifier.send_email("Testowy e-mail z Dzienniczka Głodów Alkoholowych", "To jest testowa wiadomość, aby sprawdzić, czy ustawienia e-mail są poprawne.")
        messagebox.showinfo("Wynik Wysyłania E-maila", result)

if __name__ == "__main__":
    root = tk.Tk()
    app = CravingApp(root)
    root.mainloop()
