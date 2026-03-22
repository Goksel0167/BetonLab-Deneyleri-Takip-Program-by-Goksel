"""
Demo veri yükleyici - 500+ kayıt ile sistemi test etmek için
python seed_data.py komutuyla çalıştırın
"""
import sys
import os
import random
import json
from datetime import datetime, date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from database import DatabaseManager
from analysis import GradeAnalyzer, PollutionAnalyzer, SIEVE_LIMITS


class MockSieveData:
    def __init__(self):
        self.test_date = ""
        self.aggregate_type = ""
        self.sample_weight = 0
        self.operator = ""
        self.source = ""
        self.notes = ""
        self.sieve_results = {}


class MockPollutionData:
    def __init__(self):
        self.test_date = ""
        self.aggregate_type = ""
        self.operator = ""
        self.source = ""
        self.bypass_open = False
        self.washing_water_dirty = False
        self.washing_water_insufficient = False
        self.mb_value = None
        self.sand_equivalent = None
        self.clay_lumps = None
        self.fine_content = None
        self.notes = ""


class MockRecipeData:
    def __init__(self):
        self.recipe_code = ""
        self.concrete_class = ""
        self.cement_type = ""
        self.cement_content = 0
        self.water_cement_ratio = 0
        self.aggregate_0_2 = 0
        self.aggregate_0_5 = 0
        self.aggregate_5_12 = 0
        self.aggregate_12_22 = 0
        self.aggregate_0_315 = 0
        self.admixture_type = ""
        self.admixture_content = 0
        self.target_slump = 0
        self.target_strength = 0
        self.consistency_class = ""
        self.exposure_class = ""
        self.notes = ""


def generate_sieve_results(aggregate_type: str, conformity: float = 0.85) -> dict:
    """Gerçekçi elek analizi verileri üret (conformity: 0-1 arası uyum oranı)"""
    limits = SIEVE_LIMITS.get(aggregate_type, {})
    results = {}
    for sieve_mm, (lower, upper) in limits.items():
        if random.random() < conformity:
            # Uygun değer - sınırlar içinde
            mid = (lower + upper) / 2
            spread = (upper - lower) * 0.35
            value = mid + random.gauss(0, spread / 2)
            value = max(lower + 0.5, min(upper - 0.5, value))
        else:
            # Uygunsuz değer
            if random.random() < 0.5:
                value = lower - random.uniform(2, 8)
            else:
                value = upper + random.uniform(2, 8)
            value = max(0, min(100, value))
        results[sieve_mm] = round(value, 1)
    return results


def seed_database(num_records: int = 520):
    db = DatabaseManager()
    grade_analyzer = GradeAnalyzer()
    pollution_analyzer = PollutionAnalyzer()

    operators = ["Mehmet MUTLU", "Ahmet DEMİR", "Fatma YILMAZ", "Ali KAYA"]
    sources = ["Taş Ocağı A - Kocaeli", "Taş Ocağı B - Adapazarı", "Doğal Kum - Sakarya",
               "Kırmataş C - İzmit", "Kalker D - Gebze"]
    agg_types = ["0-2", "0-5", "5-12", "12-22"]
    concrete_classes = ["C16/20", "C20/25", "C25/30", "C30/37", "C35/45", "C40/50"]

    start_date = date.today() - timedelta(days=365)

    print(f"BetonLab - Demo verisi yükleniyor ({num_records} kayıt)...")
    print("─" * 60)

    # ─── ELEK ANALİZİ ────────────────────────────────────────────
    sieve_count = num_records // 2
    print(f"Elek analizleri oluşturuluyor... ({sieve_count} kayıt)")
    for i in range(sieve_count):
        data = MockSieveData()
        day_offset = random.randint(0, 365)
        test_date = start_date + timedelta(days=day_offset)
        data.test_date = test_date.isoformat()
        data.aggregate_type = random.choice(agg_types)
        data.sample_weight = round(random.uniform(800, 1200), 0)
        data.operator = random.choice(operators)
        data.source = random.choice(sources)
        data.notes = ""

        # %90 uyumlu, %10 uygunsuz veri
        conformity = 0.95 if random.random() < 0.9 else 0.4
        data.sieve_results = generate_sieve_results(data.aggregate_type, conformity)

        evaluation = grade_analyzer.evaluate(data.aggregate_type, data.sieve_results)
        db.save_sieve_analysis(data, evaluation)

        if (i + 1) % 50 == 0:
            print(f"  {i+1}/{sieve_count} elek analizi kaydedildi")

    # ─── KİRLİLİK TESTİ ──────────────────────────────────────────
    pollution_count = num_records // 3
    print(f"\nKirlilik testleri oluşturuluyor... ({pollution_count} kayıt)")
    for i in range(pollution_count):
        data = MockPollutionData()
        day_offset = random.randint(0, 365)
        test_date = start_date + timedelta(days=day_offset)
        data.test_date = test_date.isoformat()
        data.aggregate_type = random.choice(["0-2", "0-5", "5-12", "12-22"])
        data.operator = random.choice(operators)
        data.source = random.choice(sources)

        # Baypas - %3 ihtimalle açık
        data.bypass_open = random.random() < 0.03
        data.washing_water_dirty = random.random() < 0.05
        data.washing_water_insufficient = random.random() < 0.04

        # Ölçüm değerleri
        if data.aggregate_type in ["0-2", "0-5"]:
            data.mb_value = round(random.uniform(0.3, 1.3), 2)
            data.sand_equivalent = round(random.uniform(55, 85), 1)
            data.fine_content = round(random.uniform(1.5, 18.0), 1)
            data.clay_lumps = round(random.uniform(0.0, 0.6), 2)
        else:
            data.mb_value = None
            data.sand_equivalent = None
            data.fine_content = round(random.uniform(0.3, 2.5), 1)
            data.clay_lumps = round(random.uniform(0.0, 0.35), 2)

        evaluation = pollution_analyzer.evaluate(data)
        db.save_pollution_test(data, evaluation)

        if (i + 1) % 50 == 0:
            print(f"  {i+1}/{pollution_count} kirlilik testi kaydedildi")

    # ─── BETON REÇETELERİ ─────────────────────────────────────────
    print(f"\nBeton reçeteleri oluşturuluyor...")
    recipes = [
        ("C20/25-S2-001", "C20/25", "CEM I 42.5R", 300, 0.55, 0, 750, 380, 540, 0, "Plastisite", 2.5, 120, 25, "S2", "XC1"),
        ("C25/30-S3-001", "C25/30", "CEM I 42.5R", 340, 0.48, 0, 680, 420, 580, 0, "Süperakışkan", 3.4, 160, 30, "S3", "XC2"),
        ("C25/30-S3-002", "C25/30", "CEM II/A-L 42.5R", 350, 0.47, 0, 660, 430, 570, 0, "Süperakışkan", 3.5, 160, 30, "S3", "XC2"),
        ("C30/37-S4-001", "C30/37", "CEM I 52.5R", 380, 0.43, 0, 640, 440, 600, 0, "Süperakışkan", 4.2, 190, 37, "S4", "XC3"),
        ("C35/45-S4-001", "C35/45", "CEM I 52.5R", 420, 0.38, 0, 610, 450, 620, 0, "Süperakışkan", 5.0, 200, 45, "S4", "XC4"),
        ("C16/20-S1-001", "C16/20", "CEM II/B-M 32.5R", 270, 0.60, 650, 0, 380, 510, 0, "Plastisite", 2.0, 90, 20, "S1", "XC0"),
        ("C40/50-S4-001", "C40/50", "CEM I 52.5R", 460, 0.34, 0, 580, 460, 640, 0, "Süperakışkan", 5.8, 210, 50, "S4", "XS1"),
    ]
    for r in recipes:
        data = MockRecipeData()
        (data.recipe_code, data.concrete_class, data.cement_type, data.cement_content,
         data.water_cement_ratio, data.aggregate_0_2, data.aggregate_0_5, data.aggregate_5_12,
         data.aggregate_12_22, data.aggregate_0_315, data.admixture_type, data.admixture_content,
         data.target_slump, data.target_strength, data.consistency_class, data.exposure_class) = r
        data.notes = "Demo verisi"
        db.save_concrete_recipe(data)

    counts = db.get_record_counts()
    print("\n" + "─" * 60)
    print("✅ Demo verisi başarıyla yüklendi!")
    print(f"   Elek Analizleri : {counts['sieve_analyses']} kayıt")
    print(f"   Kirlilik Testleri: {counts['pollution_tests']} kayıt")
    print(f"   Beton Reçeteleri : {counts['concrete_recipes']} kayıt")
    print(f"   TOPLAM           : {sum(counts.values())} kayıt")
    print("─" * 60)
    print("Sistemi başlatmak için: python backend/main.py")
    print("API dokümantasyonu  : http://localhost:8000/docs")
    print("Web arayüzü         : http://localhost:8000")


if __name__ == "__main__":
    seed_database(520)
