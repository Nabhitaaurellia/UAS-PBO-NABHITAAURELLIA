from enum import Enum

class Role(str, Enum):
    PARTICIPANT = "participant"
    ORGANIZER = "organizer"
    JUDGE = "judge"

class RegistrationStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    PAID = "paid"
    VERIFIED = "verified"
    REJECTED = "rejected"
    SCHEDULED = "scheduled"

class PaymentMethod(str, Enum):
    TRANSFER_BANK = "transfer_bank"
    EWALLET = "ewallet"
    CASH_ON_SITE = "cash_on_site"