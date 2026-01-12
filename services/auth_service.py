from core.kesalahan import AuthError, ConflictError, ValidationError
from core.keamanan import hash_password, verify_password, PasswordHash
from domain.enumerasi import Role
from domain.model import Participant, ParticipantProfile, User
from infrastruktur.repositori import UserRepo

class AuthService:
    def __init__(self, users: UserRepo):
        self.users = users

    def register_participant(self, username: str, password: str, full_name: str, age: int, phone: str) -> Participant:
        if not username or not password:
            raise ValidationError("username/password wajib diisi")
        if self.users.find_by_username(username):
            raise ConflictError("username sudah dipakai")

        ph = hash_password(password)
        user_id = self.users.next_id()
        participant = Participant(
            id=user_id,
            username=username,
            password_salt_hex=ph.salt_hex,
            password_hash_hex=ph.hash_hex,
            role=Role.PARTICIPANT,
            profile=ParticipantProfile(full_name=full_name, age=int(age), phone=phone),
        )
        self.users.add(participant)
        return participant

    def login(self, username: str, password: str) -> User:
        u = self.users.find_by_username(username)
        if not u:
            raise AuthError("username/password salah")
        ph = PasswordHash(salt_hex=u.password_salt_hex, hash_hex=u.password_hash_hex)
        if not verify_password(password, ph):
            raise AuthError("username/password salah")
        return u