from core.kesalahan import ValidationError
from domain.enumerasi import RegistrationStatus
from domain.model import ScheduleSlot
from infrastruktur.repositori import RegistrationRepo, ScheduleRepo

class ScheduleService:
    def __init__(self, regs: RegistrationRepo, slots: ScheduleRepo):
        self.regs = regs
        self.slots = slots

    def assign_manual_slot(self, reg_id: str, date_time: str, stage: str, order_no: int) -> ScheduleSlot:
        reg = self.regs.get(reg_id)
        if reg.status != RegistrationStatus.VERIFIED:
            raise ValidationError("Jadwal hanya bisa diatur untuk peserta berstatus VERIFIED.")
        
        slot_id = self.slots.next_id()
        slot = ScheduleSlot(
            id=slot_id,
            order_no=order_no,
            date_time=date_time,
            stage=stage,
            registration_id=reg_id
        )
        self.slots.add(slot)
        reg.schedule(slot_id)
        self.regs.update(reg)
        return slot

    def get_slot_for_registration(self, reg_id: str):
        return self.slots.get_by_registration(reg_id)

    def list_all_slots(self):
        return self.slots.list_all()