from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from domain.enumerasi import Role, RegistrationStatus, PaymentMethod

def now_iso() -> str:
    return datetime.utcnow().isoformat()

@dataclass
class User:
    id: str
    username: str
    password_salt_hex: str
    password_hash_hex: str
    role: Role

@dataclass
class ParticipantProfile:
    full_name: str
    age: int
    phone: str

@dataclass
class Participant(User):
    profile: ParticipantProfile

@dataclass
class Category:
    id: str
    name: str
    min_age: int
    max_age: int
    fee: int
    quota: int

@dataclass
class Competition:
    id: str
    name: str
    location: str
    date: str
    deadline: str
    categories: Dict[str, Category]

@dataclass
class Payment:
    method: PaymentMethod
    amount: int
    proof: str
    paid_at: str = field(default_factory=now_iso)

@dataclass
class Registration:
    id: str
    participant_id: str
    category_id: str
    song_title: str
    song_creator: str
    media_link: str
    status: RegistrationStatus = RegistrationStatus.DRAFT
    submitted_at: Optional[str] = None
    payment: Optional[Payment] = None
    verified_at: Optional[str] = None
    rejected_reason: Optional[str] = None
    schedule_slot_id: Optional[str] = None

    def submit(self) -> None:
        if self.status not in (RegistrationStatus.DRAFT,):
            raise ValueError("status tidak valid untuk submit")
        self.status = RegistrationStatus.SUBMITTED
        self.submitted_at = now_iso()

    def mark_paid(self, payment: Payment) -> None:
        if self.status != RegistrationStatus.SUBMITTED:
            raise ValueError("pembayaran hanya bisa setelah submitted")
        self.payment = payment
        self.status = RegistrationStatus.PAID

    def verify(self) -> None:
        if self.status != RegistrationStatus.PAID:
            raise ValueError("verifikasi hanya bisa setelah paid")
        self.status = RegistrationStatus.VERIFIED
        self.verified_at = now_iso()
        self.rejected_reason = None

    def reject(self, reason: str) -> None:
        if self.status not in (RegistrationStatus.PAID, RegistrationStatus.SUBMITTED):
            raise ValueError("reject hanya bisa ketika submitted/paid")
        self.status = RegistrationStatus.REJECTED
        self.rejected_reason = reason
        self.verified_at = None

    def schedule(self, slot_id: str) -> None:
        if self.status != RegistrationStatus.VERIFIED:
            raise ValueError("jadwal hanya untuk verified")
        self.status = RegistrationStatus.SCHEDULED
        self.schedule_slot_id = slot_id

@dataclass
class ScheduleSlot:
    id: str
    order_no: int
    date_time: str
    stage: str
    registration_id: str

@dataclass
class Score:
    id: str
    registration_id: str
    judge_id: str
    vocal: int
    intonation: int
    stage: int
    created_at: str = field(default_factory=now_iso)

    def total(self, weights: Dict[str, float]) -> float:
        return (
            self.vocal * weights["vocal"]
            + self.intonation * weights["intonation"]
            + self.stage * weights["stage"]
        )