import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import Counter
import data_manager

def get_summary_stats(entries):
    """Calculates summary statistics from craving entries."""
    if not entries:
        return {
            "total_entries": 0,
            "avg_intensity": 0,
            "most_common_trigger": "N/A",
            "most_used_coping": "N/A"
        }

    total_entries = len(entries)
    avg_intensity = sum(int(e['intensity']) for e in entries) / total_entries

    triggers = [e['triggers'] for e in entries if e['triggers']]
    most_common_trigger = Counter(triggers).most_common(1)[0][0] if triggers else "N/A"

    coping_mechanisms = [e['coping_mechanism'] for e in entries if e['coping_mechanism']]
    most_used_coping = Counter(coping_mechanisms).most_common(1)[0][0] if coping_mechanisms else "N/A"

    return {
        "total_entries": total_entries,
        "avg_intensity": f"{avg_intensity:.2f}",
        "most_common_trigger": most_common_trigger,
        "most_used_coping": most_used_coping
    }


def create_intensity_plot(parent_frame, entries):
    """Creates and embeds a plot of craving intensity over time."""
    for widget in parent_frame.winfo_children():
        widget.destroy()

    if not entries:
        return

    timestamps = [e['timestamp'] for e in entries]
    intensities = [int(e['intensity']) for e in entries]

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(timestamps, intensities, marker='o', linestyle='-')
    ax.set_title("Intensywność Głodów w Czasie")
    ax.set_xlabel("Data")
    ax.set_ylabel("Intensywność (1-10)")
    plt.xticks(rotation=45)
    plt.tight_layout()

    canvas = FigureCanvasTkAgg(fig, master=parent_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)