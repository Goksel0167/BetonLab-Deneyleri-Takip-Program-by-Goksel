"""
TS EN 13515 ve Agrega Standartlarına göre analiz motoru
Elek analizi değerlendirmesi ve kirlilik testi yorumlama
"""
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional


# ─── TS EN 13515 STANDART SINIR DEĞERLERİ ───────────────────────────────────
# Elekten geçen % - Alt ve üst sınırlar (elek göz açıklığı mm: [alt%, üst%])

SIEVE_LIMITS = {
    "0-2": {  # 0-2mm Doğal Kum (GrAding curve limits)
        "0.063": [0, 10],
        "0.125": [0, 20],
        "0.25": [5, 45],
        "0.5": [25, 70],
        "1": [50, 85],
        "2": [85, 99],
        "4": [95, 100],
    },
    "0-5": {  # 0-5mm Kırma Kum
        "0.063": [0, 16],
        "0.125": [0, 25],
        "0.25": [5, 40],
        "0.5": [20, 55],
        "1": [35, 65],
        "2": [55, 80],
        "4": [80, 99],
        "5.6": [95, 100],
    },
    "5-12": {  # 5-12mm Çakıl/Kırmataş
        "1": [0, 5],
        "2": [0, 10],
        "4": [0, 20],
        "5.6": [5, 40],
        "8": [30, 70],
        "11.2": [65, 99],
        "16": [95, 100],
    },
    "12-22": {  # 12-22mm İri Agrega
        "8": [0, 5],
        "11.2": [0, 15],
        "16": [20, 55],
        "22.4": [80, 99],
        "31.5": [95, 100],
    },
    "0-31.5": {  # 0-31.5mm Mıcır
        "0.063": [0, 8],
        "0.5": [5, 30],
        "2": [20, 50],
        "8": [45, 70],
        "16": [65, 90],
        "22.4": [80, 99],
        "31.5": [95, 100],
    }
}

# Kirlilik sınır değerleri (TS EN 12620)
POLLUTION_LIMITS = {
    "mb_value": {  # Metilen mavisi (g/kg)
        "0-2":   {"limit": 1.0, "warning": 0.8},
        "0-5":   {"limit": 1.0, "warning": 0.8},
        "5-12":  {"limit": None, "warning": None},
        "12-22": {"limit": None, "warning": None},
    },
    "sand_equivalent": {  # Kum eşdeğeri (%) - min değer
        "0-2":   {"min_limit": 65, "min_warning": 70},
        "0-5":   {"min_limit": 60, "min_warning": 65},
        "5-12":  {"min_limit": None, "min_warning": None},
        "12-22": {"min_limit": None, "min_warning": None},
    },
    "fine_content": {  # İnce madde içeriği (%) - max değer
        "0-2":   {"limit": 5.0, "warning": 4.0},
        "0-5":   {"limit": 16.0, "warning": 12.0},
        "5-12":  {"limit": 1.5, "warning": 1.0},
        "12-22": {"limit": 1.5, "warning": 1.0},
    },
    "clay_lumps": {  # Kil topağı içeriği (%) - max değer
        "0-2":   {"limit": 0.5, "warning": 0.3},
        "0-5":   {"limit": 0.5, "warning": 0.3},
        "5-12":  {"limit": 0.25, "warning": 0.15},
        "12-22": {"limit": 0.25, "warning": 0.15},
    }
}


class GradeAnalyzer:
    """Tane büyüklüğü dağılımı analizi - TS EN 13515"""

    def get_all_limits(self) -> dict:
        return {
            "sieve_limits": SIEVE_LIMITS,
            "pollution_limits": POLLUTION_LIMITS,
            "standard": "TS EN 13515 / TS EN 12620",
            "version": "2024"
        }

    def evaluate(self, aggregate_type: str, sieve_results: Dict[str, float]) -> dict:
        """Elek analizi sonuçlarını standart sınırlarla karşılaştır"""
        limits = SIEVE_LIMITS.get(aggregate_type)
        if not limits:
            return {
                "status": "BİLİNMEYEN",
                "message": f"'{aggregate_type}' için standart sınır tanımlı değil",
                "details": []
            }

        details = []
        non_conform = []
        warnings = []
        checked = 0

        for sieve_size, (lower, upper) in limits.items():
            if sieve_size not in sieve_results:
                continue
            checked += 1
            value = sieve_results[sieve_size]
            sieve_status = "UYGUN"
            comment = ""

            if value < lower:
                sieve_status = "UYGUNSUZ"
                diff = lower - value
                comment = f"Alt sınırın {diff:.1f}% altında (ince malzeme eksik - KABA geldi)"
                non_conform.append(f"{sieve_size}mm: {value:.1f}% < {lower}% (alt sınır)")
            elif value > upper:
                sieve_status = "UYGUNSUZ"
                diff = value - upper
                comment = f"Üst sınırın {diff:.1f}% üzerinde (ince malzeme fazla - İNCE geldi)"
                non_conform.append(f"{sieve_size}mm: {value:.1f}% > {upper}% (üst sınır)")
            else:
                # Sınır yakınlık kontrolü (%5 tolerans)
                tolerance = (upper - lower) * 0.1
                if value < lower + tolerance:
                    sieve_status = "UYARI"
                    comment = f"Alt sınıra yakın ({lower}%) - Kaba tarafa kayma riski"
                    warnings.append(f"{sieve_size}mm: Alt sınıra yakın")
                elif value > upper - tolerance:
                    sieve_status = "UYARI"
                    comment = f"Üst sınıra yakın ({upper}%) - İnce tarafa kayma riski"
                    warnings.append(f"{sieve_size}mm: Üst sınıra yakın")

            details.append({
                "sieve_mm": sieve_size,
                "value": value,
                "lower_limit": lower,
                "upper_limit": upper,
                "status": sieve_status,
                "comment": comment
            })

        # Genel durum belirleme
        if non_conform:
            status = "UYGUNSUZ"
            message = f"{len(non_conform)} elek boyutunda standart dışı değer tespit edildi"
            recommendation = self._get_recommendation(aggregate_type, details)
        elif warnings:
            status = "UYARI"
            message = f"Değerler sınırlar içinde ancak {len(warnings)} elek boyutunda sınır yakınlığı var"
            recommendation = "Haftalık takip sıklığını artırın ve kaynak değişimi değerlendirin"
        else:
            status = "UYGUN"
            message = f"Tüm elek boyutları TS EN 13515 sınırları içinde"
            recommendation = "Rutin haftalık takibe devam edin"

        return {
            "status": status,
            "message": message,
            "non_conformities": non_conform,
            "warnings": warnings,
            "recommendation": recommendation,
            "checked_sieves": checked,
            "details": details,
            "evaluated_at": datetime.now().isoformat()
        }

    def _get_recommendation(self, aggregate_type: str, details: list) -> str:
        """Uygunsuzluk için öneri oluştur"""
        coarse_issues = [d for d in details if d["status"] == "UYGUNSUZ" and d["value"] < d["lower_limit"]]
        fine_issues = [d for d in details if d["status"] == "UYGUNSUZ" and d["value"] > d["upper_limit"]]

        recommendations = []
        if coarse_issues:
            recommendations.append(
                f"Agrega KABA tarafa kaydı ({len(coarse_issues)} elek). "
                "Tasarımda ince agrega miktarını artırın veya fraksiyon değiştirin."
            )
        if fine_issues:
            recommendations.append(
                f"Agrega İNCE tarafa kaydı ({len(fine_issues)} elek). "
                "Tasarımda iri agrega miktarını artırın veya fraksiyon değiştirin. "
                "Beton su ihtiyacı artabilir, dayanım düşebilir - reçete gözden geçirilmeli."
            )
        return " | ".join(recommendations) if recommendations else "Kaynak değişikliği incelensin"


class PollutionAnalyzer:
    """Kirlilik testi analizi - TS EN 12620"""

    def evaluate(self, data) -> dict:
        """Kirlilik testi sonuçlarını standart sınırlarla karşılaştır"""
        agg_type = data.aggregate_type
        non_conform = []
        warnings = []
        details = []

        # Baypas kontrolü
        if data.bypass_open:
            non_conform.append("Baypas AÇIK durumda tespit edildi - Agrega yıkanmıyor!")
            details.append({"parameter": "Baypas", "value": "AÇIK", "status": "KRİTİK",
                           "comment": "Baypas açıkken agrega kirliliği giderilemez"})

        # Yıkama suyu kontrolü
        if data.washing_water_dirty:
            non_conform.append("Yıkama suyu KİRLİ - Agrega yıkama verimliliği düşük")
            details.append({"parameter": "Yıkama Suyu", "value": "KİRLİ", "status": "UYGUNSUZ",
                           "comment": "Yıkama suyu değiştirilmeli"})
        if data.washing_water_insufficient:
            non_conform.append("Yıkama suyu YETERSİZ - Kapasite artırılmalı")
            details.append({"parameter": "Yıkama Suyu Kapasitesi", "value": "YETERSİZ", "status": "UYGUNSUZ",
                           "comment": "Su debisi artırılmalı veya sistem revize edilmeli"})

        # Metilen mavisi
        if data.mb_value is not None:
            mb_limits = POLLUTION_LIMITS["mb_value"].get(agg_type, {})
            if mb_limits.get("limit"):
                if data.mb_value > mb_limits["limit"]:
                    non_conform.append(f"Metilen Mavisi {data.mb_value} g/kg > Limit {mb_limits['limit']} g/kg")
                    details.append({"parameter": "MB Değeri", "value": data.mb_value,
                                   "limit": mb_limits["limit"], "unit": "g/kg", "status": "UYGUNSUZ",
                                   "comment": "Kil/organik kirlilik yüksek"})
                elif data.mb_value > mb_limits.get("warning", 0):
                    warnings.append(f"MB değeri uyarı sınırına yakın: {data.mb_value} g/kg")
                    details.append({"parameter": "MB Değeri", "value": data.mb_value,
                                   "limit": mb_limits["limit"], "unit": "g/kg", "status": "UYARI",
                                   "comment": "Takip sıklığını artırın"})
                else:
                    details.append({"parameter": "MB Değeri", "value": data.mb_value,
                                   "limit": mb_limits["limit"], "unit": "g/kg", "status": "UYGUN", "comment": ""})

        # Kum eşdeğeri
        if data.sand_equivalent is not None:
            se_limits = POLLUTION_LIMITS["sand_equivalent"].get(agg_type, {})
            if se_limits.get("min_limit"):
                if data.sand_equivalent < se_limits["min_limit"]:
                    non_conform.append(f"Kum Eşdeğeri {data.sand_equivalent}% < Min Limit {se_limits['min_limit']}%")
                    details.append({"parameter": "Kum Eşdeğeri", "value": data.sand_equivalent,
                                   "limit": f"≥{se_limits['min_limit']}", "unit": "%", "status": "UYGUNSUZ",
                                   "comment": "Kil oranı yüksek, agrega temizliği yetersiz"})
                elif data.sand_equivalent < se_limits.get("min_warning", 100):
                    warnings.append(f"Kum eşdeğeri düşük: {data.sand_equivalent}%")
                    details.append({"parameter": "Kum Eşdeğeri", "value": data.sand_equivalent,
                                   "limit": f"≥{se_limits['min_limit']}", "unit": "%", "status": "UYARI",
                                   "comment": "Uyarı sınırına yakın, takip artırılmalı"})
                else:
                    details.append({"parameter": "Kum Eşdeğeri", "value": data.sand_equivalent,
                                   "limit": f"≥{se_limits['min_limit']}", "unit": "%", "status": "UYGUN", "comment": ""})

        # İnce madde içeriği
        if data.fine_content is not None:
            fc_limits = POLLUTION_LIMITS["fine_content"].get(agg_type, {})
            if fc_limits.get("limit"):
                if data.fine_content > fc_limits["limit"]:
                    non_conform.append(f"İnce Madde {data.fine_content}% > Limit {fc_limits['limit']}%")
                    details.append({"parameter": "İnce Madde", "value": data.fine_content,
                                   "limit": fc_limits["limit"], "unit": "%", "status": "UYGUNSUZ",
                                   "comment": "Beton su ihtiyacını artırır, dayanımı olumsuz etkiler"})
                elif data.fine_content > fc_limits.get("warning", float("inf")):
                    warnings.append(f"İnce madde uyarı sınırında: {data.fine_content}%")
                    details.append({"parameter": "İnce Madde", "value": data.fine_content,
                                   "limit": fc_limits["limit"], "unit": "%", "status": "UYARI", "comment": ""})
                else:
                    details.append({"parameter": "İnce Madde", "value": data.fine_content,
                                   "limit": fc_limits["limit"], "unit": "%", "status": "UYGUN", "comment": ""})

        # Kil topağı
        if data.clay_lumps is not None:
            cl_limits = POLLUTION_LIMITS["clay_lumps"].get(agg_type, {})
            if cl_limits.get("limit"):
                if data.clay_lumps > cl_limits["limit"]:
                    non_conform.append(f"Kil Topağı {data.clay_lumps}% > Limit {cl_limits['limit']}%")
                    details.append({"parameter": "Kil Topağı", "value": data.clay_lumps,
                                   "limit": cl_limits["limit"], "unit": "%", "status": "UYGUNSUZ",
                                   "comment": "Yıkama sistemi kontrol edilmeli"})
                else:
                    details.append({"parameter": "Kil Topağı", "value": data.clay_lumps,
                                   "limit": cl_limits["limit"], "unit": "%", "status": "UYGUN", "comment": ""})

        if non_conform:
            status = "UYGUNSUZ"
            message = f"{len(non_conform)} parametre standart dışı"
        elif warnings:
            status = "UYARI"
            message = f"Sınırlar içinde, ancak {len(warnings)} parametre için uyarı mevcut"
        else:
            status = "UYGUN"
            message = "Tüm kirlilik parametreleri standart sınırları içinde"

        return {
            "status": status,
            "message": message,
            "non_conformities": non_conform,
            "warnings": warnings,
            "details": details,
            "standard": "TS EN 12620",
            "evaluated_at": datetime.now().isoformat()
        }


class ReportGenerator:
    """Haftalık rapor oluşturucu - TS EN 13515'e uygun"""

    def __init__(self, db):
        self.db = db

    def generate_weekly_report(self, week_start: Optional[str] = None) -> dict:
        """Haftalık analiz raporu oluştur"""
        if week_start:
            ws = datetime.strptime(week_start, "%Y-%m-%d").date()
        else:
            today = date.today()
            ws = today - timedelta(days=today.weekday())

        we = ws + timedelta(days=6)
        week_num = ws.isocalendar()[1]
        year = ws.year

        sieve_data = self.db.get_sieve_analyses_for_week(ws.isoformat(), we.isoformat())
        pollution_data = self.db.get_pollution_tests_for_week(ws.isoformat(), we.isoformat())

        sieve_summary = self._summarize_sieve(sieve_data)
        pollution_summary = self._summarize_pollution(pollution_data)

        all_non_conformities = []
        for s in sieve_data:
            if s.get("status") == "UYGUNSUZ":
                ev = s.get("evaluation", {})
                all_non_conformities.append({
                    "date": s["test_date"],
                    "type": "Elek Analizi",
                    "aggregate": s["aggregate_type"],
                    "issues": ev.get("non_conformities", [])
                })
        for p in pollution_data:
            if p.get("status") == "UYGUNSUZ":
                ev = p.get("evaluation", {})
                all_non_conformities.append({
                    "date": p["test_date"],
                    "type": "Kirlilik Testi",
                    "aggregate": p["aggregate_type"],
                    "issues": ev.get("non_conformities", [])
                })

        recommendations = self._generate_recommendations(sieve_summary, pollution_summary)
        overall_status = "UYGUNSUZ" if all_non_conformities else (
            "UYARI" if any(s.get("has_warnings") for s in [sieve_summary, pollution_summary]) else "UYGUN"
        )

        return {
            "week_start": ws.isoformat(),
            "week_end": we.isoformat(),
            "week_number": week_num,
            "year": year,
            "sieve_summary": sieve_summary,
            "pollution_summary": pollution_summary,
            "non_conformities": all_non_conformities,
            "recommendations": recommendations,
            "overall_status": overall_status,
            "standard": "TS EN 13515 / TS EN 12620",
            "generated_at": datetime.now().isoformat(),
            "total_tests": len(sieve_data) + len(pollution_data),
        }

    def _summarize_sieve(self, data: list) -> dict:
        if not data:
            return {"count": 0, "conforming": 0, "non_conforming": 0, "by_type": {}}

        by_type = {}
        conforming = sum(1 for d in data if d.get("status") == "UYGUN")
        warning = sum(1 for d in data if d.get("status") == "UYARI")
        non_conforming = sum(1 for d in data if d.get("status") == "UYGUNSUZ")

        for d in data:
            agg = d["aggregate_type"]
            if agg not in by_type:
                by_type[agg] = {"count": 0, "conforming": 0, "non_conforming": 0, "warning": 0}
            by_type[agg]["count"] += 1
            st = d.get("status", "UYGUN")
            if st == "UYGUN":
                by_type[agg]["conforming"] += 1
            elif st == "UYGUNSUZ":
                by_type[agg]["non_conforming"] += 1
            else:
                by_type[agg]["warning"] += 1

        return {
            "count": len(data),
            "conforming": conforming,
            "warning": warning,
            "non_conforming": non_conforming,
            "compliance_rate": round(conforming / len(data) * 100, 1) if data else 0,
            "has_warnings": warning > 0,
            "by_type": by_type
        }

    def _summarize_pollution(self, data: list) -> dict:
        if not data:
            return {"count": 0, "conforming": 0, "non_conforming": 0, "by_type": {}}

        by_type = {}
        conforming = sum(1 for d in data if d.get("status") == "UYGUN")
        warning = sum(1 for d in data if d.get("status") == "UYARI")
        non_conforming = sum(1 for d in data if d.get("status") == "UYGUNSUZ")

        bypass_issues = sum(1 for d in data if d.get("bypass_open"))
        washing_issues = sum(1 for d in data if d.get("washing_water_dirty") or d.get("washing_water_insufficient"))

        for d in data:
            agg = d["aggregate_type"]
            if agg not in by_type:
                by_type[agg] = {"count": 0, "conforming": 0, "non_conforming": 0}
            by_type[agg]["count"] += 1
            if d.get("status") == "UYGUN":
                by_type[agg]["conforming"] += 1
            elif d.get("status") == "UYGUNSUZ":
                by_type[agg]["non_conforming"] += 1

        return {
            "count": len(data),
            "conforming": conforming,
            "warning": warning,
            "non_conforming": non_conforming,
            "compliance_rate": round(conforming / len(data) * 100, 1) if data else 0,
            "bypass_issues": bypass_issues,
            "washing_issues": washing_issues,
            "has_warnings": warning > 0,
            "by_type": by_type
        }

    def _generate_recommendations(self, sieve_sum: dict, pollution_sum: dict) -> list:
        recs = []
        if sieve_sum.get("non_conforming", 0) > 0:
            recs.append({
                "priority": "YÜKSEK",
                "category": "Tane Büyüklüğü",
                "text": f"{sieve_sum['non_conforming']} elek analizi uygunsuz. Taş ocağıyla irtibata geçin, fraksiyon değişikliği değerlendirin."
            })
        if pollution_sum.get("bypass_issues", 0) > 0:
            recs.append({
                "priority": "KRİTİK",
                "category": "Baypas",
                "text": "Baypas açık tespit edildi! Hemen kapatılmalı ve agrega yıkama sistemi kontrol edilmeli."
            })
        if pollution_sum.get("washing_issues", 0) > 0:
            recs.append({
                "priority": "YÜKSEK",
                "category": "Yıkama Sistemi",
                "text": "Yıkama suyu yetersiz/kirli. Su debisi artırılmalı veya sistem revize edilmeli."
            })
        if pollution_sum.get("non_conforming", 0) > 0:
            recs.append({
                "priority": "YÜKSEK",
                "category": "Kirlilik",
                "text": f"{pollution_sum['non_conforming']} kirlilik testi uygunsuz. Beton reçetesi gözden geçirilmeli."
            })
        if sieve_sum.get("count", 0) < 2:
            recs.append({
                "priority": "ORTA",
                "category": "Test Sıklığı",
                "text": "Bu hafta elek analizi sayısı az. Her agrega sınıfı için haftada 1 test yapılmalı."
            })
        if not recs:
            recs.append({
                "priority": "BİLGİ",
                "category": "Genel",
                "text": "Bu hafta tüm testler standart sınırlar içinde. Rutin haftalık takibe devam edin."
            })
        return recs
