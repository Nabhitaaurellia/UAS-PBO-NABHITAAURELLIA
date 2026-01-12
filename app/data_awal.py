from domain.model import Competition, Category
from infrastruktur.repositori import CompetitionRepo, UserRepo
from infrastruktur.penyimpanan_json import JsonStore
from domain.enumerasi import Role
from core.keamanan import hash_password

def seed_all(store: JsonStore):
    db = store.read()
    if db.get("competition") is None:
        comp_repo = CompetitionRepo(store)
        comp = Competition(
            id="comp_0001",
            name="Lomba Nyanyi Nasional",
            location="Jakarta",
            date="2026-02-01",
            deadline="2026-01-20",
            categories={
                "cat_anak": Category(id="cat_anak", name="Anak (7-12)", min_age=7, max_age=12, fee=50000, quota=50),
                "cat_remaja": Category(id="cat_remaja", name="Remaja (13-17)", min_age=13, max_age=17, fee=75000, quota=50),
                "cat_dewasa": Category(id="cat_dewasa", name="Dewasa (18-35)", min_age=18, max_age=35, fee=100000, quota=50),
            }
        )
        comp_repo.set_competition(comp)

    users_repo = UserRepo(store)
    def add_user(username: str, password: str, role: Role):
        if users_repo.find_by_username(username):
            return
        ph = hash_password(password)
        uid = users_repo.next_id()
        current_db = store.read()
        current_db["users"].append({
            "id": uid, "username": username, "password_salt_hex": ph.salt_hex, 
            "password_hash_hex": ph.hash_hex, "role": role.value
        })
        store.write(current_db)

    add_user("organizer", "organizer123", Role.ORGANIZER)
    add_user("judge", "judge123", Role.JUDGE)