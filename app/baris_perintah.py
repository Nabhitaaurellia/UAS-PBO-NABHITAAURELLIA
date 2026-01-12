from datetime import date
from core.kesalahan import AppError
from domain.enumerasi import Role, RegistrationStatus, PaymentMethod
from infrastruktur.penyimpanan_json import JsonStore
from infrastruktur.repositori import UserRepo, CompetitionRepo, RegistrationRepo, ScheduleRepo, ScoreRepo
from services.auth_service import AuthService
from services.registration_service import RegistrationService
from services.schedule_service import ScheduleService
from services.scoring_service import ScoringService
from app.data_awal import seed_all

def _input_int(prompt: str) -> int:
    try:
        return int(input(prompt).strip())
    except ValueError:
        print("Input harus berupa angka.")
        return 0

def _pause():
    input("\nTekan Enter untuk lanjut...")

def run_app():
    store = JsonStore()
    seed_all(store)

    users = UserRepo(store)
    comp_repo = CompetitionRepo(store)
    regs = RegistrationRepo(store)
    slots = ScheduleRepo(store)
    scores = ScoreRepo(store)

    auth_service = AuthService(users)
    reg_service = RegistrationService(users, comp_repo, regs)
    sched_service = ScheduleService(regs, slots)
    score_service = ScoringService(regs, scores, users)

    print("=== SELAMAT DATANG DI SISTEM LOMBA NYANYI ===")
    
    current_user = None
    today = date(2025, 12, 29) 

    while True:
        try:
            if not current_user:
                print("\n1. Login\n2. Register Peserta\n0. Keluar")
                pilih = input("Pilih: ")
                if pilih == "1":
                    uname = input("Username: "); pwd = input("Password: ")
                    current_user = auth_service.login(uname, pwd)
                    
                    if current_user.role == Role.PARTICIPANT:
                        comp = comp_repo.get_competition()
                        print(f"\nLogin berhasil! Selamat datang, {current_user.profile.full_name}")
                        
                        detected_cat = "Tidak ditemukan kategori yang sesuai"
                        for cat in comp.categories.values():
                            if cat.min_age <= current_user.profile.age <= cat.max_age:
                                detected_cat = cat.name
                                break
                        print(f"Berdasarkan umur Anda ({current_user.profile.age} thn), Anda masuk kategori: {detected_cat}")
                    else:
                        print(f"\nLogin berhasil! Selamat datang, {current_user.username}")

                elif pilih == "2":
                    uname = input("Username baru: "); pwd = input("Password baru: ")
                    name = input("Nama Lengkap: "); age = _input_int("Umur: ")
                    phone = input("No Telp: ")
                    auth_service.register_participant(uname, pwd, name, age, phone)
                    print("\nRegistrasi berhasil! Silakan login.")
                elif pilih == "0": break
            else:
                print(f"\n--- MENU {current_user.role.value.upper()} ---")
                
                if current_user.role == Role.PARTICIPANT:
                    print("1. Daftar Lomba\n2. Lihat Status Pendaftaran\n3. Bayar Pendaftaran\n4. Lihat Jadwal\n0. Logout")
                    pilih = input("Pilih: ")
                    
                    if pilih == "1":
                        raw_cat_id = input("Pilih Kategori (anak/remaja/dewasa): ").strip().lower()
                        cat_id = f"cat_{raw_cat_id}" if not raw_cat_id.startswith("cat_") else raw_cat_id
                        judul = input("Judul Lagu: "); pencipta = input("Pencipta: "); link = input("Link Lagu/Video: ")
                        reg_service.create_registration(current_user.id, cat_id, judul, pencipta, link, today)
                        print("\n[Sukses] Pendaftaran berhasil dibuat!")
                    elif pilih == "2":
                        my_regs = reg_service.list_my_regs(current_user.id)
                        if not my_regs: print("Anda belum memiliki pendaftaran.")
                        for r in my_regs:
                            print(f"ID: {r.id} | Lagu: {r.song_title} | Status: {r.status.value}")
                    elif pilih == "3":
                        reg_id = input("Masukkan ID Pendaftaran: ")
                        metode_input = input("Pilih Metode (transfer_bank, ewallet): ").strip().lower()
                        metode = PaymentMethod(metode_input)
                        bukti = input("Masukkan Link Bukti Bayar: ")
                        reg_service.submit(reg_id, current_user.id)
                        reg_service.pay(reg_id, current_user.id, metode, bukti)
                        print("\n[Sukses] Pembayaran dikirim!")
                    elif pilih == "4":
                        reg_id = input("Masukkan ID Pendaftaran: ")
                        slot = sched_service.get_slot_for_registration(reg_id)
                        if slot:
                            print(f"No Urut: {slot.order_no} | Jadwal: {slot.date_time} di {slot.stage}")
                        else:
                            print("Belum dijadwalkan.")
                    elif pilih == "0": current_user = None

                elif current_user.role == Role.ORGANIZER:
                    print("1. Verifikasi Pembayaran\n2. Atur Jadwal Manual\n3. Lihat Semua Pendaftaran\n0. Logout")
                    pilih = input("Pilih: ")
                    if pilih == "1":
                        all_paid = reg_service.list_by_status(RegistrationStatus.PAID)
                        if not all_paid:
                            print("Tidak ada pendaftaran yang perlu diverifikasi.")
                        else:
                            for r in all_paid:
                                p = users.get(r.participant_id)
                                print(f"ID: {r.id} | Nama: {p.profile.full_name} | Bukti: {r.payment.proof}")
                            rid = input("ID untuk diverifikasi: ")
                            reg_service.organizer_verify(rid)
                            print("\n[Sukses] Terverifikasi.")
                    elif pilih == "2":
                        verified = reg_service.list_by_status(RegistrationStatus.VERIFIED)
                        if not verified: print("Tidak ada peserta VERIFIED.")
                        else:
                            for r in verified:
                                p = users.get(r.participant_id)
                                print(f"ID: {r.id} | Nama: {p.profile.full_name} | Lagu: {r.song_title}")
                            rid = input("\nPilih ID Pendaftaran: ")
                            time = input("Waktu (YYYY-MM-DD HH:MM): ")
                            stg = input("Stage (Default: Main Stage): ") or "Main Stage"
                            ord_no = _input_int("Nomor Tampil: ")
                            sched_service.assign_manual_slot(rid, time, stg, ord_no)
                            print("\n[Sukses] Jadwal manual disimpan.")
                    elif pilih == "3":
                        for status in RegistrationStatus:
                            print(f"\n[STATUS: {status.value.upper()}]")
                            found = reg_service.list_by_status(status)
                            if not found: print("  (Kosong)")
                            for r in found:
                                p = users.get(r.participant_id)
                                print(f"  ID: {r.id} | Nama: {p.profile.full_name} | Lagu: {r.song_title}")
                    elif pilih == "0": current_user = None

                elif current_user.role == Role.JUDGE:
                    print("1. Beri Nilai\n2. Lihat Ranking\n0. Logout")
                    pilih = input("Pilih: ")
                    if pilih == "1":
                        candidates = score_service.get_unscored_scheduled(current_user.id)
                        if not candidates: print("\n[!] Tidak ada peserta untuk dinilai.")
                        else:
                            for c in candidates: print(f"ID: {c['reg_id']} | Nama: {c['name']} | Lagu: {c['song']}")
                            rid = input("\nMasukkan ID Pendaftaran: ")
                            v = _input_int("Vokal: "); i = _input_int("Intonasi: "); s = _input_int("Stage: ")
                            score_service.submit_score(rid, current_user.id, v, i, s)
                            print("\n[Sukses] Nilai disimpan.")
                    elif pilih == "2":
                        ranks = score_service.ranking()
                        print("\n--- RANKING SEMENTARA ---")
                        for idx, (r_id, name, avg, count) in enumerate(ranks, start=1):
                            print(f"{idx}. {name} (ID: {r_id}) | Skor: {avg:.2f} | Juri: {count}")
                    elif pilih == "0": current_user = None
                
        except AppError as e:
            print(f"\n[!] Error: {e}")
        except Exception as e:
            print(f"\n[!] Kesalahan Sistem: {e}")
        _pause()

if __name__ == "__main__":
    run_app()