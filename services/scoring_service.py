from core.kesalahan import ValidationError
from domain.model import Score
from infrastruktur.repositori import ScoreRepo, RegistrationRepo, UserRepo

DEFAULT_WEIGHTS = {"vocal": 0.4, "intonation": 0.3, "stage": 0.3}

class ScoringService:
    def __init__(self, regs: RegistrationRepo, scores: ScoreRepo, users: UserRepo):
        self.regs = regs
        self.scores = scores
        self.users = users

    def submit_score(self, reg_id: str, judge_id: str, vocal: int, intonation: int, stage: int) -> Score:
        reg = self.regs.get(reg_id)
        if not reg.schedule_slot_id:
            raise ValidationError("peserta belum dijadwalkan")

        for val, name in [(vocal, "vocal"), (intonation, "intonation"), (stage, "stage")]:
            if val < 0 or val > 100:
                raise ValidationError(f"nilai {name} harus 0..100")

        score = Score(
            id=self.scores.next_id(),
            registration_id=reg_id,
            judge_id=judge_id,
            vocal=int(vocal),
            intonation=int(intonation),
            stage=int(stage),
        )
        self.scores.upsert(score)
        return score

    def get_unscored_scheduled(self, judge_id: str):
        from domain.enumerasi import RegistrationStatus
        all_scheduled = self.regs.list_by_status(RegistrationStatus.SCHEDULED)
        all_scores = self.scores.list_all()
        
        unscored = []
        for reg in all_scheduled:
            already_scored = any(s.registration_id == reg.id and s.judge_id == judge_id for s in all_scores)
            if not already_scored:
                participant = self.users.get(reg.participant_id)
                name = participant.profile.full_name if hasattr(participant, 'profile') else participant.username
                unscored.append({
                    "reg_id": reg.id,
                    "name": name,
                    "song": reg.song_title
                })
        return unscored

    def ranking(self):
        all_scores = self.scores.list_all()
        by_reg = {}
        for s in all_scores:
            by_reg.setdefault(s.registration_id, []).append(s.total(DEFAULT_WEIGHTS))
        
        result = []
        for reg_id, totals in by_reg.items():
            avg = sum(totals) / len(totals)
            reg = self.regs.get(reg_id)
            participant = self.users.get(reg.participant_id)
            name = participant.profile.full_name if hasattr(participant, 'profile') else participant.username
            result.append((reg_id, name, avg, len(totals)))
            
        result.sort(key=lambda x: x[2], reverse=True) 
        return result