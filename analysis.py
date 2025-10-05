import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import Counter
from itertools import combinations, product
from datetime import datetime
import data_manager


def _split_triggers(trigger_string):
    if not trigger_string:
        return []
    return [item.strip() for item in trigger_string.split(',') if item.strip()]

def get_summary_stats(entries):
    """Calculates summary statistics from craving entries."""
    if not entries:
        return {
            "total_entries": 0,
            "avg_intensity": "N/A",
            "most_common_trigger": "N/A",
            "most_used_coping": "N/A",
            "most_common_pair": "N/A",
            "most_common_sequence": "N/A",
            "workday_weekend_distribution": {"workdays": 0, "weekend": 0},
        }

    total_entries = len(entries)

    intensities = []
    trigger_counts = Counter()
    coping_mechanisms = []
    for entry in entries:
        try:
            intensities.append(int(entry.get('intensity', 0)))
        except (TypeError, ValueError):
            pass
        trigger_list = _split_triggers(entry.get('triggers', ''))
        trigger_counts.update(trigger_list)
        coping_value = entry.get('coping_mechanism')
        if coping_value:
            coping_mechanisms.append(coping_value)

    avg_intensity = f"{(sum(intensities) / len(intensities)):.2f}" if intensities else "N/A"
    most_common_trigger = trigger_counts.most_common(1)[0][0] if trigger_counts else "N/A"
    most_used_coping = Counter(coping_mechanisms).most_common(1)[0][0] if coping_mechanisms else "N/A"

    pair_counter = Counter()
    for entry in entries:
        trigger_list = sorted(set(_split_triggers(entry.get('triggers', ''))))
        if len(trigger_list) < 2:
            continue
        for pair in combinations(trigger_list, 2):
            pair_counter[pair] += 1

    most_common_pair = "N/A"
    if pair_counter:
        pair, count = pair_counter.most_common(1)[0]
        most_common_pair = f"{pair[0]} + {pair[1]} ({count})"

    parsed_entries = []
    for entry in entries:
        timestamp = entry.get('timestamp')
        try:
            dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S") if timestamp else None
        except ValueError:
            try:
                dt = datetime.fromisoformat(timestamp)
            except (TypeError, ValueError):
                dt = None
        parsed_entries.append({
            'datetime': dt,
            'triggers': _split_triggers(entry.get('triggers', ''))
        })

    chronological_entries = [item for item in parsed_entries if item['datetime'] is not None]
    chronological_entries.sort(key=lambda item: item['datetime'])

    sequential_counter = Counter()
    for first, second in zip(chronological_entries, chronological_entries[1:]):
        first_triggers = first['triggers']
        second_triggers = second['triggers']
        if not first_triggers or not second_triggers:
            continue
        for combo in product(first_triggers, second_triggers):
            sequential_counter[combo] += 1

    most_common_sequence = "N/A"
    if sequential_counter:
        (first_trigger, second_trigger), count = sequential_counter.most_common(1)[0]
        most_common_sequence = f"{first_trigger} → {second_trigger} ({count})"

    workday_entries = 0
    weekend_entries = 0
    for item in chronological_entries:
        dt = item['datetime']
        if dt.weekday() < 5:
            workday_entries += 1
        else:
            weekend_entries += 1

    return {
        "total_entries": total_entries,
        "avg_intensity": avg_intensity,
        "most_common_trigger": most_common_trigger,
        "most_used_coping": most_used_coping,
        "most_common_pair": most_common_pair,
        "most_common_sequence": most_common_sequence,
        "workday_weekend_distribution": {
            "workdays": workday_entries,
            "weekend": weekend_entries,
        },
    }


def create_intensity_plot(parent_frame, entries):
    """Creates and embeds a plot of craving intensity over time."""
    for widget in parent_frame.winfo_children():
        widget.destroy()

    if not entries:
        return

    timestamps = []
    intensities = []
    for entry in entries:
        try:
            intensities.append(int(entry['intensity']))
            timestamps.append(entry['timestamp'])
        except (KeyError, TypeError, ValueError):
            continue

    if not intensities:
        return

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