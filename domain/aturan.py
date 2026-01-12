from datetime import date
from core.kesalahan import ValidationError
from domain.model import Category, Competition

def parse_date(d: str) -> date:
    parts = d.split("-")
    if len(parts) != 3:
        raise ValidationError("format tanggal harus YYYY-MM-DD")
    y, m, dd = map(int, parts)
    return date(y, m, dd)

def ensure_deadline_not_passed(comp: Competition, today: date) -> None:
    if today > parse_date(comp.deadline):
        raise ValidationError("pendaftaran sudah melewati deadline")

def ensure_age_in_category(age: int, cat: Category) -> None:
    if age < cat.min_age or age > cat.max_age:
        raise ValidationError(f"umur {age} tidak sesuai kategori {cat.name}")

def ensure_quota_available(current_count: int, cat: Category) -> None:
    if current_count >= cat.quota:
        raise ValidationError(f"kuota kategori {cat.name} sudah penuh")