import json
import os
from typing import Dict, Optional


def _normalize_mark_value(value):
    if isinstance(value, dict):
        scale = value.get("scale")
        if scale is None and value.get("template"):
            scale = ""
        return {"scale": str(scale) if scale is not None else ""}
    if isinstance(value, str):
        return {"scale": value}
    return {"scale": ""}

MARKS_FILE = 'calendar_marks.json'


def _load_from_disk() -> Dict[str, Dict[str, Dict[str, str]]]:
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


def load_marks() -> Dict[str, Dict[str, Dict[str, str]]]:
    return _load_from_disk()


def save_marks(marks: Dict[str, Dict[str, Dict[str, str]]]) -> None:
    with open(MARKS_FILE, 'w', encoding='utf-8') as f:
        json.dump(marks, f, ensure_ascii=False, indent=2)


def is_marked(
    date_key: str,
    symptom: str,
    marks: Optional[Dict[str, Dict[str, Dict[str, str]]]] = None,
) -> bool:
    marks = load_marks() if marks is None else marks
    day_marks = marks.get(date_key, {})
    if symptom not in day_marks:
        return False
    value = day_marks[symptom]
    if isinstance(value, dict):
        return True
    if isinstance(value, str) and value:
        return True
    return isinstance(value, str)


def get_mark(
    date_key: str,
    symptom: str,
    marks: Optional[Dict[str, Dict[str, Dict[str, str]]]] = None,
) -> Optional[Dict[str, str]]:
    marks = load_marks() if marks is None else marks
    day_marks = marks.get(date_key, {})
    if symptom not in day_marks:
        return None
    value = day_marks[symptom]
    normalized = _normalize_mark_value(value)
    if normalized != value:
        day_marks[symptom] = normalized
        save_marks(marks)
    return normalized


def get_scale(
    date_key: str,
    symptom: str,
    marks: Optional[Dict[str, Dict[str, Dict[str, str]]]] = None,
) -> Optional[str]:
    mark = get_mark(date_key, symptom, marks)
    if mark is None:
        return None
    return mark.get("scale") or None


def update_mark(
    date_key: str,
    symptom: str,
    *,
    scale: Optional[str] = None,
    marks: Optional[Dict[str, Dict[str, Dict[str, str]]]] = None,
) -> Dict[str, Dict[str, Dict[str, str]]]:
    marks = load_marks() if marks is None else marks
    day_marks = marks.setdefault(date_key, {})
    current = _normalize_mark_value(day_marks.get(symptom, {}))
    if scale is not None:
        current["scale"] = scale
    day_marks[symptom] = current
    save_marks(marks)
    return marks


def set_mark(
    date_key: str,
    symptom: str,
    scale: str = '',
    marks: Optional[Dict[str, Dict[str, Dict[str, str]]]] = None,
) -> Dict[str, Dict[str, Dict[str, str]]]:
    return update_mark(date_key, symptom, scale=scale, marks=marks)


def remove_mark(
    date_key: str,
    symptom: str,
    marks: Optional[Dict[str, Dict[str, Dict[str, str]]]] = None,
) -> Dict[str, Dict[str, Dict[str, str]]]:
    marks = load_marks() if marks is None else marks
    day_marks = marks.get(date_key)
    if day_marks and symptom in day_marks:
        del day_marks[symptom]
        if not day_marks:
            del marks[date_key]
        save_marks(marks)
    return marks
