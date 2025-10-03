import tkinter as tk
from tkinter import ttk, messagebox
import data_manager
import analysis
from datetime import datetime

class CravingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Dzienniczek Głodów Alkoholowych")
        self.root.geometry("800x600")

        # Create a Notebook (tabbed interface)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(pady=10, padx=10, fill="both", expand=True)

        # Create frames for each tab
        self.journal_frame = ttk.Frame(self.notebook, width=780, height=580)
        self.analysis_frame = ttk.Frame(self.notebook, width=780, height=580)

        self.notebook.add(self.journal_frame, text='Dziennik')
        self.notebook.add(self.analysis_frame, text='Analiza')

        self.create_journal_widgets()
        self.create_analysis_widgets()

        self.load_entries()
        self.update_analysis_tab()

    def create_journal_widgets(self):
        # Frame for input fields
        input_frame = ttk.LabelFrame(self.journal_frame, text="Nowy Wpis")
        input_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        ttk.Label(input_frame, text="Intensywność (1-10):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.intensity_var = tk.StringVar()
        self.intensity_entry = ttk.Entry(input_frame, textvariable=self.intensity_var)
        self.intensity_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(input_frame, text="Wyzwalacze:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.triggers_var = tk.StringVar()
        self.triggers_entry = ttk.Entry(input_frame, textvariable=self.triggers_var)
        self.triggers_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(input_frame, text="Sposób radzenia sobie:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.coping_var = tk.StringVar()
        self.coping_entry = ttk.Entry(input_frame, textvariable=self.coping_var)
        self.coping_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        self.drank_var = tk.BooleanVar()
        self.drank_check = ttk.Checkbutton(input_frame, text="Czy doszło do spożycia?", variable=self.drank_var)
        self.drank_check.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky="w")

        self.save_button = ttk.Button(input_frame, text="Zapisz", command=self.save_entry)
        self.save_button.grid(row=4, column=0, columnspan=2, pady=10)

        # Frame for displaying entries
        display_frame = ttk.LabelFrame(self.journal_frame, text="Historia Wpisów")
        display_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        self.tree = ttk.Treeview(display_frame, columns=data_manager.FIELDNAMES, show='headings')
        for col in data_manager.FIELDNAMES:
            self.tree.heading(col, text=col.replace('_', ' ').title())
        self.tree.pack(fill="both", expand=True)

        self.journal_frame.columnconfigure(0, weight=1)
        self.journal_frame.rowconfigure(1, weight=1)

    def create_analysis_widgets(self):
        # Frame for summary stats
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

        # Frame for the plot
        self.plot_frame = ttk.LabelFrame(self.analysis_frame, text="Wykres Intensywności")
        self.plot_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        self.analysis_frame.columnconfigure(0, weight=1)
        self.analysis_frame.rowconfigure(1, weight=1)

    def update_analysis_tab(self):
        entries = data_manager.load_cravings()
        stats = analysis.get_summary_stats(entries)

        self.total_entries_label.config(text=f"Liczba wpisów: {stats['total_entries']}")
        self.avg_intensity_label.config(text=f"Średnia intensywność: {stats['avg_intensity']}")
        self.common_trigger_label.config(text=f"Najczęstszy wyzwalacz: {stats['most_common_trigger']}")
        self.used_coping_label.config(text=f"Najczęstszy sposób radzenia sobie: {stats['most_used_coping']}")

        analysis.create_intensity_plot(self.plot_frame, entries)

    def load_entries(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        entries = data_manager.load_cravings()
        for entry in entries:
            self.tree.insert('', 'end', values=list(entry.values()))
        self.update_analysis_tab()

    def save_entry(self):
        intensity = self.intensity_var.get()
        triggers = self.triggers_var.get()
        coping = self.coping_var.get()
        drank = self.drank_var.get()

        if not intensity.isdigit() or not 1 <= int(intensity) <= 10:
            messagebox.showerror("Błąd", "Intensywność musi być liczbą od 1 do 10.")
            return

        entry_data = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'intensity': intensity,
            'triggers': triggers,
            'coping_mechanism': coping,
            'drank': 'Tak' if drank else 'Nie'
        }

        data_manager.save_craving(entry_data)
        self.load_entries()
        self.clear_fields()
        messagebox.showinfo("Sukces", "Wpis został zapisany.")

    def clear_fields(self):
        self.intensity_var.set("")
        self.triggers_var.set("")
        self.coping_var.set("")
        self.drank_var.set(False)

if __name__ == "__main__":
    root = tk.Tk()
    app = CravingApp(root)
    root.mainloop()