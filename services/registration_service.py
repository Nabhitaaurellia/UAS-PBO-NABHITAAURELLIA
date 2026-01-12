from datetime import date
from core.kesalahan import ValidationError, NotFoundError
from domain.enumerasi import RegistrationStatus, PaymentMethod
from domain.model import Registration, Payment
from domain.aturan import ensure_age_in_category, ensure_deadline_not_passed, ensure_quota_available
from infrastruktur.repositori import CompetitionRepo, RegistrationRepo, UserRepo

class RegistrationService:
    def __init__(self, users: UserRepo, comp_repo: CompetitionRepo, regs: RegistrationRepo):
        self.users = users
        self.comp_repo = comp_repo
        self.regs = regs

    def create_registration(self, participant_id: str, category_id: str, song_title: str, song_creator: str, media_link: str, today: date) -> Registration:
        comp = self.comp_repo.get_competition()
        ensure_deadline_not_passed(comp, today)

        participant = self.users.get(participant_id)
        prof = getattr(participant, "profile", None)
        if not prof:
            raise ValidationError("profil peserta belum lengkap")

        cat = comp.categories.get(category_id)
        if not cat:
            raise NotFoundError("kategori tidak ditemukan")

        ensure_age_in_category(prof.age, cat)
        ensure_quota_available(self.regs.count_in_category(category_id), cat)

        reg = Registration(
            id=self.regs.next_id(),
            participant_id=participant_id,
            category_id=category_id,
            song_title=song_title.strip(),
            song_creator=song_creator.strip(),
            media_link=media_link.strip(),
        )
        self.regs.add(reg)
        return reg

    def submit(self, reg_id: str, participant_id: str) -> Registration:
        reg = self.regs.get(reg_id)
        if reg.participant_id != participant_id:
            raise ValidationError("bukan pendaftaran milikmu")
        reg.submit()
        self.regs.update(reg)
        return reg

    def pay(self, reg_id: str, participant_id: str, method: PaymentMethod, proof: str) -> Registration:
        reg = self.regs.get(reg_id)
        if reg.participant_id != participant_id:
            raise ValidationError("bukan pendaftaran milikmu")

        comp = self.comp_repo.get_competition()
        cat = comp.categories.get(reg.category_id)
        if not cat:
            raise NotFoundError("kategori tidak ditemukan")

        payment = Payment(method=method, amount=cat.fee, proof=proof.strip())
        reg.mark_paid(payment)
        self.regs.update(reg)
        return reg

    def organizer_verify(self, reg_id: str) -> Registration:
        reg = self.regs.get(reg_id)
        reg.verify()
        self.regs.update(reg)
        return reg

    def list_my_regs(self, participant_id: str):
        return self.regs.list_by_participant(participant_id)

    def list_by_status(self, status: RegistrationStatus):
        return self.regs.list_by_status(status)