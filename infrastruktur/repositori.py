from __future__ import annotations
from dataclasses import asdict
from typing import Any, Dict, List, Optional
from core.kesalahan import NotFoundError
from domain.enumerasi import Role, RegistrationStatus, PaymentMethod
from domain.model import (
    User, Participant, ParticipantProfile, Competition, Category,
    Registration, Payment, ScheduleSlot, Score
)
from infrastruktur.penyimpanan_json import JsonStore

def _require(obj, msg: str):
    if obj is None:
        raise NotFoundError(msg)
    return obj

class IdGenerator:
    def __init__(self, prefix: str):
        self.prefix = prefix

    def new_id(self, db: Dict[str, Any]) -> str:
        counter_key = f"__counter_{self.prefix}"
        n = int(db.get(counter_key, 0)) + 1
        db[counter_key] = n
        return f"{self.prefix}_{n:04d}"

class BaseRepo:
    def __init__(self, store: JsonStore):
        self.store = store

class UserRepo(BaseRepo):
    def __init__(self, store: JsonStore):
        super().__init__(store)
        self.ids = IdGenerator("user")

    def find_by_username(self, username: str) -> Optional[User]:
        db = self.store.read()
        for u in db["users"]:
            if u["username"] == username:
                return self._from_dict(u)
        return None

    def get(self, user_id: str) -> User:
        db = self.store.read()
        for u in db["users"]:
            if u["id"] == user_id:
                return self._from_dict(u)
        raise NotFoundError("user tidak ditemukan")

    def add(self, user: User) -> None:
        db = self.store.read()
        db["users"].append(self._to_dict(user))
        self.store.write(db)

    def next_id(self) -> str:
        db = self.store.read()
        new_id = self.ids.new_id(db)
        self.store.write(db)
        return new_id

    def _to_dict(self, user: User) -> Dict[str, Any]:
        d = asdict(user)
        d["role"] = user.role.value
        return d

    def _from_dict(self, d: Dict[str, Any]) -> User:
        role = Role(d["role"])
        if role == Role.PARTICIPANT:
            prof = d.get("profile") or {}
            profile = ParticipantProfile(
                full_name=prof.get("full_name", ""),
                age=int(prof.get("age", 0)),
                phone=prof.get("phone", "")
            )
            return Participant(**{**d, "role": role, "profile": profile})
        return User(**{**d, "role": role})

class CompetitionRepo(BaseRepo):
    def set_competition(self, comp: Competition) -> None:
        db = self.store.read()
        db["competition"] = self._to_dict(comp)
        self.store.write(db)

    def get_competition(self) -> Competition:
        db = self.store.read()
        raw = _require(db.get("competition"), "competition belum di-seed")
        return self._from_dict(raw)

    def _to_dict(self, comp: Competition) -> Dict[str, Any]:
        return {
            "id": comp.id,
            "name": comp.name,
            "location": comp.location,
            "date": comp.date,
            "deadline": comp.deadline,
            "categories": {
                cid: asdict(cat) for cid, cat in comp.categories.items()
            }
        }

    def _from_dict(self, d: Dict[str, Any]) -> Competition:
        cats = {cid: Category(**c) for cid, c in d["categories"].items()}
        return Competition(
            id=d["id"], name=d["name"], location=d["location"],
            date=d["date"], deadline=d["deadline"], categories=cats
        )

class RegistrationRepo(BaseRepo):
    def __init__(self, store: JsonStore):
        super().__init__(store)
        self.ids = IdGenerator("reg")

    def next_id(self) -> str:
        db = self.store.read()
        new_id = self.ids.new_id(db)
        self.store.write(db)
        return new_id

    def add(self, reg: Registration) -> None:
        db = self.store.read()
        db["registrations"].append(self._to_dict(reg))
        self.store.write(db)

    def update(self, reg: Registration) -> None:
        db = self.store.read()
        for i, r in enumerate(db["registrations"]):
            if r["id"] == reg.id:
                db["registrations"][i] = self._to_dict(reg)
                self.store.write(db)
                return
        raise NotFoundError("registration tidak ditemukan")

    def get(self, reg_id: str) -> Registration:
        db = self.store.read()
        for r in db["registrations"]:
            if r["id"] == reg_id:
                return self._from_dict(r)
        raise NotFoundError("registration tidak ditemukan")

    def list_by_participant(self, participant_id: str) -> List[Registration]:
        db = self.store.read()
        return [self._from_dict(r) for r in db["registrations"] if r["participant_id"] == participant_id]

    def list_by_status(self, status: RegistrationStatus) -> List[Registration]:
        db = self.store.read()
        return [self._from_dict(r) for r in db["registrations"] if r["status"] == status.value]

    def count_in_category(self, category_id: str) -> int:
        db = self.store.read()
        return sum(1 for r in db["registrations"] if r["category_id"] == category_id and r["status"] != RegistrationStatus.REJECTED.value)

    def _to_dict(self, reg: Registration) -> Dict[str, Any]:
        d = asdict(reg)
        d["status"] = reg.status.value
        if reg.payment:
            d["payment"]["method"] = reg.payment.method.value
        return d

    def _from_dict(self, d: Dict[str, Any]) -> Registration:
        payment = None
        if d.get("payment"):
            p = d["payment"]
            payment = Payment(
                method=PaymentMethod(p["method"]),
                amount=int(p["amount"]),
                proof=p["proof"],
                paid_at=p.get("paid_at", "")
            )
        return Registration(
            id=d["id"],
            participant_id=d["participant_id"],
            category_id=d["category_id"],
            song_title=d["song_title"],
            song_creator=d["song_creator"],
            media_link=d["media_link"],
            status=RegistrationStatus(d["status"]),
            submitted_at=d.get("submitted_at"),
            payment=payment,
            verified_at=d.get("verified_at"),
            rejected_reason=d.get("rejected_reason"),
            schedule_slot_id=d.get("schedule_slot_id"),
        )

class ScheduleRepo(BaseRepo):
    def __init__(self, store: JsonStore):
        super().__init__(store)
        self.ids = IdGenerator("slot")

    def next_id(self) -> str:
        db = self.store.read()
        new_id = self.ids.new_id(db)
        self.store.write(db)
        return new_id

    def add(self, slot: ScheduleSlot) -> None:
        db = self.store.read()
        db["schedule_slots"].append(asdict(slot))
        self.store.write(db)

    def list_all(self) -> List[ScheduleSlot]:
        db = self.store.read()
        return [ScheduleSlot(**s) for s in db["schedule_slots"]]

    def get_by_registration(self, reg_id: str) -> Optional[ScheduleSlot]:
        db = self.store.read()
        for s in db["schedule_slots"]:
            if s["registration_id"] == reg_id:
                return ScheduleSlot(**s)
        return None

class ScoreRepo(BaseRepo):
    def __init__(self, store: JsonStore):
        super().__init__(store)
        self.ids = IdGenerator("score")

    def next_id(self) -> str:
        db = self.store.read()
        new_id = self.ids.new_id(db)
        self.store.write(db)
        return new_id

    def upsert(self, score: Score) -> None:
        db = self.store.read()
        for i, s in enumerate(db["scores"]):
            if s["registration_id"] == score.registration_id and s["judge_id"] == score.judge_id:
                db["scores"][i] = asdict(score)
                self.store.write(db)
                return
        db["scores"].append(asdict(score))
        self.store.write(db)

    def list_all(self) -> List[Score]:
        db = self.store.read()
        return [Score(**s) for s in db["scores"]]