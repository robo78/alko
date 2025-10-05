import json
import os
from typing import Dict, Optional

MARKS_FILE = 'calendar_marks.json'


def _load_from_disk() -> Dict[str, Dict[str, str]]:
    if not os.path.exists(MARKS_FILE):
        return {}
    try:
        with open(MARKS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
    except (json.JSONDecodeError, OSError):
        pass
    return {}


def load_marks() -> Dict[str, Dict[str, str]]:
    return _load_from_disk()


def save_marks(marks: Dict[str, Dict[str, str]]) -> None:
    with open(MARKS_FILE, 'w', encoding='utf-8') as f:
        json.dump(marks, f, ensure_ascii=False, indent=2)


def is_marked(date_key: str, symptom: str, marks: Optional[Dict[str, Dict[str, str]]] = None) -> bool:
    marks = load_marks() if marks is None else marks
    return symptom in marks.get(date_key, {})


def get_template(date_key: str, symptom: str, marks: Optional[Dict[str, Dict[str, str]]] = None) -> Optional[str]:
    marks = load_marks() if marks is None else marks
    day_marks = marks.get(date_key, {})
    if symptom in day_marks:
        return day_marks[symptom]
    return None


def set_mark(date_key: str, symptom: str, template: str = '', marks: Optional[Dict[str, Dict[str, str]]] = None) -> Dict[str, Dict[str, str]]:
    marks = load_marks() if marks is None else marks
    day_marks = marks.setdefault(date_key, {})
    day_marks[symptom] = template
    save_marks(marks)
    return marks


def remove_mark(date_key: str, symptom: str, marks: Optional[Dict[str, Dict[str, str]]] = None) -> Dict[str, Dict[str, str]]:
    marks = load_marks() if marks is None else marks
    day_marks = marks.get(date_key)
    if day_marks and symptom in day_marks:
        del day_marks[symptom]
        if not day_marks:
            del marks[date_key]
        save_marks(marks)
    return marks
