"""
BetonLab - Beton ve Agrega Laboratuvar Takip Sistemi
TS EN 13515 & Agrega Standartlarına Uygun
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from typing import Optional
import uvicorn
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager
from models import (
    SieveAnalysis, PollutionTest, ConcreteRecipe,
    WeeklyReport, SieveAnalysisCreate, PollutionTestCreate,
    ConcreteRecipeCreate
)
from analysis import GradeAnalyzer, PollutionAnalyzer, ReportGenerator
from datetime import date, datetime

app = FastAPI(
    title="BetonLab API",
    description="Beton ve Agrega Laboratuvar Takip Sistemi - TS EN 13515",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db = DatabaseManager()

# ─── Static files ───────────────────────────────────────────────────────────
frontend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
if os.path.exists(os.path.join(frontend_path, "static")):
    app.mount("/static", StaticFiles(directory=os.path.join(frontend_path, "static")), name="static")

@app.get("/", include_in_schema=False)
async def root():
    index_path = os.path.join(frontend_path, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "BetonLab API çalışıyor", "docs": "/docs"}

# ─── ELEK ANALİZİ ────────────────────────────────────────────────────────────
@app.get("/api/sieve-analyses", tags=["Elek Analizi"])
async def get_sieve_analyses(
    limit: int = Query(100, le=500),
    offset: int = 0,
    aggregate_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Elek analizlerini listele (max 500 kayıt)"""
    records = db.get_sieve_analyses(limit, offset, aggregate_type, start_date, end_date)
    return {"data": records, "total": db.count_sieve_analyses(aggregate_type)}

@app.post("/api/sieve-analyses", tags=["Elek Analizi"])
async def create_sieve_analysis(data: SieveAnalysisCreate):
    """Yeni elek analizi kaydet"""
    analyzer = GradeAnalyzer()
    result = analyzer.evaluate(data.aggregate_type, data.sieve_results)
    record_id = db.save_sieve_analysis(data, result)
    return {"id": record_id, "evaluation": result, "message": "Elek analizi kaydedildi"}

@app.get("/api/sieve-analyses/{record_id}", tags=["Elek Analizi"])
async def get_sieve_analysis(record_id: int):
    record = db.get_sieve_analysis_by_id(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Kayıt bulunamadı")
    return record

@app.delete("/api/sieve-analyses/{record_id}", tags=["Elek Analizi"])
async def delete_sieve_analysis(record_id: int):
    db.delete_sieve_analysis(record_id)
    return {"message": "Kayıt silindi"}

# ─── KİRLİLİK TESTİ ─────────────────────────────────────────────────────────
@app.get("/api/pollution-tests", tags=["Kirlilik Testi"])
async def get_pollution_tests(
    limit: int = Query(100, le=500),
    offset: int = 0,
    aggregate_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    records = db.get_pollution_tests(limit, offset, aggregate_type, start_date, end_date)
    return {"data": records, "total": db.count_pollution_tests(aggregate_type)}

@app.post("/api/pollution-tests", tags=["Kirlilik Testi"])
async def create_pollution_test(data: PollutionTestCreate):
    """Yeni kirlilik testi kaydet"""
    analyzer = PollutionAnalyzer()
    result = analyzer.evaluate(data)
    record_id = db.save_pollution_test(data, result)
    return {"id": record_id, "evaluation": result, "message": "Kirlilik testi kaydedildi"}

@app.get("/api/pollution-tests/{record_id}", tags=["Kirlilik Testi"])
async def get_pollution_test(record_id: int):
    record = db.get_pollution_test_by_id(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Kayıt bulunamadı")
    return record

# ─── BETON REÇETESİ ──────────────────────────────────────────────────────────
@app.get("/api/concrete-recipes", tags=["Beton Reçetesi"])
async def get_concrete_recipes(
    limit: int = Query(100, le=500),
    offset: int = 0,
    concrete_class: Optional[str] = None
):
    records = db.get_concrete_recipes(limit, offset, concrete_class)
    return {"data": records, "total": db.count_concrete_recipes(concrete_class)}

@app.post("/api/concrete-recipes", tags=["Beton Reçetesi"])
async def create_concrete_recipe(data: ConcreteRecipeCreate):
    record_id = db.save_concrete_recipe(data)
    return {"id": record_id, "message": "Beton reçetesi kaydedildi"}

@app.get("/api/concrete-recipes/{record_id}", tags=["Beton Reçetesi"])
async def get_concrete_recipe(record_id: int):
    record = db.get_concrete_recipe_by_id(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Kayıt bulunamadı")
    return record

@app.put("/api/concrete-recipes/{record_id}", tags=["Beton Reçetesi"])
async def update_concrete_recipe(record_id: int, data: ConcreteRecipeCreate):
    db.update_concrete_recipe(record_id, data)
    return {"message": "Beton reçetesi güncellendi"}

# ─── HAFTALIK RAPOR ───────────────────────────────────────────────────────────
@app.get("/api/reports/weekly", tags=["Raporlar"])
async def get_weekly_report(week_start: Optional[str] = None):
    """Haftalık rapor oluştur (TS EN 13515 standartlarına göre)"""
    generator = ReportGenerator(db)
    report = generator.generate_weekly_report(week_start)
    return report

@app.get("/api/reports/weekly/list", tags=["Raporlar"])
async def list_weekly_reports(limit: int = 12):
    reports = db.get_weekly_reports(limit)
    return {"data": reports}

@app.post("/api/reports/weekly/save", tags=["Raporlar"])
async def save_weekly_report(week_start: str):
    generator = ReportGenerator(db)
    report = generator.generate_weekly_report(week_start)
    report_id = db.save_weekly_report(week_start, report)
    return {"id": report_id, "report": report}

# ─── DASHBOARD / İSTATİSTİKLER ───────────────────────────────────────────────
@app.get("/api/dashboard/stats", tags=["Dashboard"])
async def get_dashboard_stats():
    """Ana dashboard istatistikleri"""
    stats = db.get_dashboard_stats()
    return stats

@app.get("/api/dashboard/trend", tags=["Dashboard"])
async def get_trend_data(
    aggregate_type: str,
    days: int = Query(30, le=90)
):
    """Tane büyüklüğü trend verisi"""
    data = db.get_trend_data(aggregate_type, days)
    return {"data": data}

@app.get("/api/dashboard/pollution-trend", tags=["Dashboard"])
async def get_pollution_trend(days: int = Query(30, le=90)):
    data = db.get_pollution_trend(days)
    return {"data": data}

# ─── STANDART SINIRLAR ───────────────────────────────────────────────────────
@app.get("/api/standards/limits", tags=["Standartlar"])
async def get_standard_limits():
    """TS EN 13515 standart sınır değerleri"""
    analyzer = GradeAnalyzer()
    return analyzer.get_all_limits()

@app.get("/api/standards/aggregate-types", tags=["Standartlar"])
async def get_aggregate_types():
    return {
        "types": [
            {"code": "0-2", "name": "0-2 mm Doğal Kum", "category": "DOĞAL"},
            {"code": "0-5", "name": "0-5 mm Kırma Kum", "category": "KIRMA"},
            {"code": "5-12", "name": "5-12 mm Çakıl/Kırmataş", "category": "KIRMA"},
            {"code": "12-22", "name": "12-22 mm İri Agrega", "category": "KIRMA"},
            {"code": "0-31.5", "name": "0-31.5 mm Mıcır", "category": "KIRMA"},
        ]
    }

# ─── SAĞLIK KONTROLÜ ─────────────────────────────────────────────────────────
@app.get("/api/health", tags=["Sistem"])
async def health_check():
    stats = db.get_record_counts()
    return {
        "status": "çalışıyor",
        "timestamp": datetime.now().isoformat(),
        "database": "bağlı",
        "record_counts": stats
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
