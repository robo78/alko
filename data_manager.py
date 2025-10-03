# This file will handle data storage.
import csv
import os

DATA_FILE = 'cravings.csv'
FIELDNAMES = ['timestamp', 'intensity', 'triggers', 'coping_mechanism', 'drank']

def initialize_data_file():
    """Creates the data file with headers if it doesn't exist."""
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(FIELDNAMES)

def save_craving(data):
    """Saves a single craving entry."""
    initialize_data_file()
    with open(DATA_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writerow(data)

def load_cravings():
    """Loads all craving entries."""
    initialize_data_file()
    with open(DATA_FILE, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)