"""
Veri modelleri - TS EN 13515 & Agrega standartlarına uygun
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any
from datetime import date


ALLOWED_CEMENT_TYPES = {
    "CEM I 42,5 R",
    "CEM I 52,5 R",
    "CEM II/A-M 42,5 R",
    "CEM I 52,5 R Süper Beyaz",
    "CEM II/B-LL 32,5 R",
    "CEM II/A-M (V-LL) 52,5 N",
    "CEM I 42,5 R Superpower",
    "CEM I 52,5 N",
    "CEM II/A-M (P-L) 42,5 R",
}

ALLOWED_CONSISTENCY_CLASSES = {
    "S1", "S2", "S3", "S4", "S5",
    "F1", "F2", "F3", "F4", "F5", "F6",
}

ALLOWED_EXPOSURE_CLASSES = {
    "X0",
    "XC1", "XC2", "XC3", "XC4",
    "XD1", "XD2", "XD3",
    "XS1", "XS2", "XS3",
    "XF1", "XF2", "XF3", "XF4",
    "XA1", "XA2", "XA3",
    "XM1", "XM2", "XM3",
}


class SieveAnalysisCreate(BaseModel):
    test_date: str = Field(..., description="Test tarihi (YYYY-MM-DD)")
    aggregate_type: str = Field(..., description="Agrega sınıfı (0-2, 0-5, 5-12, 12-22)")
    sample_weight: Optional[float] = Field(None, description="Numune ağırlığı (g)")
    operator: Optional[str] = Field(None, description="Deney yapan")
    source: Optional[str] = Field(None, description="Agrega kaynağı/ocak")
    notes: Optional[str] = None
    sieve_results: Dict[str, float] = Field(..., description="Elek göz açıklığı(mm): elekten geçen(%)")

    class Config:
        schema_extra = {
            "example": {
                "test_date": "2024-03-22",
                "aggregate_type": "0-5",
                "sample_weight": 1000.0,
                "operator": "Mehmet MUTLU",
                "source": "Taş Ocağı A",
                "sieve_results": {
                    "0.063": 2.1,
                    "0.125": 5.3,
                    "0.25": 14.2,
                    "0.5": 28.7,
                    "1": 47.8,
                    "2": 72.3,
                    "4": 91.5,
                    "5.6": 98.2
                }
            }
        }


class SieveAnalysis(SieveAnalysisCreate):
    id: int
    evaluation: Optional[Dict[str, Any]] = None
    status: str = "UYGUN"
    week_number: Optional[int] = None
    year: Optional[int] = None
    created_at: Optional[str] = None


class PollutionTestCreate(BaseModel):
    test_date: str = Field(..., description="Test tarihi (YYYY-MM-DD)")
    aggregate_type: str = Field(..., description="Agrega sınıfı")
    operator: Optional[str] = None
    source: Optional[str] = None
    bypass_open: bool = Field(False, description="Baypas açık mı?")
    washing_water_dirty: bool = Field(False, description="Yıkama suyu kirli mi?")
    washing_water_insufficient: bool = Field(False, description="Yıkama suyu yetersiz mi?")
    mb_value: Optional[float] = Field(None, description="Metilen mavisi değeri (g/kg)")
    sand_equivalent: Optional[float] = Field(None, description="Kum eşdeğeri (%)")
    clay_lumps: Optional[float] = Field(None, description="Kil topağı içeriği (%)")
    fine_content: Optional[float] = Field(None, description="İnce madde içeriği (%)")
    notes: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "test_date": "2024-03-22",
                "aggregate_type": "0-5",
                "operator": "Mehmet MUTLU",
                "source": "Taş Ocağı A",
                "bypass_open": False,
                "washing_water_dirty": False,
                "washing_water_insufficient": False,
                "mb_value": 0.8,
                "sand_equivalent": 72,
                "clay_lumps": 0.2,
                "fine_content": 3.1
            }
        }


class PollutionTest(PollutionTestCreate):
    id: int
    evaluation: Optional[Dict[str, Any]] = None
    status: str = "UYGUN"
    week_number: Optional[int] = None
    year: Optional[int] = None
    created_at: Optional[str] = None


class ConcreteRecipeCreate(BaseModel):
    recipe_code: str = Field(..., description="Reçete kodu (örn: C25/30-S3)")
    concrete_class: str = Field(..., description="Beton sınıfı (C20/25, C25/30...)")
    cement_type: Optional[str] = Field(None, description="Çimento tipi (CEM I 42.5R...)")
    cement_content: Optional[float] = Field(None, description="Çimento miktarı (kg/m³)")
    water_cement_ratio: Optional[float] = Field(None, description="Su/Çimento oranı")
    aggregate_0_2: float = Field(0, description="0-2mm agrega (kg/m³)")
    aggregate_0_5: float = Field(0, description="0-5mm agrega (kg/m³)")
    aggregate_5_12: float = Field(0, description="5-12mm agrega (kg/m³)")
    aggregate_12_22: float = Field(0, description="12-22mm agrega (kg/m³)")
    aggregate_0_315: float = Field(0, description="0-31.5mm agrega (kg/m³)")
    admixture_type: Optional[str] = Field(None, description="Katkı maddesi tipi")
    admixture_content: float = Field(0, description="Katkı maddesi miktarı (kg/m³)")
    target_slump: Optional[float] = Field(None, description="Hedef çökme (mm)")
    target_strength: Optional[float] = Field(None, description="Hedef dayanım (MPa)")
    consistency_class: Optional[str] = Field(None, description="Kıvam sınıfı (S1-S5)")
    exposure_class: Optional[str] = Field(None, description="Maruziyet sınıfı (XC1...)")
    notes: Optional[str] = None

    @field_validator("cement_type", mode="before")
    @classmethod
    def validate_cement_type(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return None
        if v not in ALLOWED_CEMENT_TYPES:
            raise ValueError("Geçersiz çimento tipi")
        return v

    @field_validator("consistency_class", mode="before")
    @classmethod
    def validate_consistency_class(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            v = v.strip().upper()
            if not v:
                return None
        if v not in ALLOWED_CONSISTENCY_CLASSES:
            raise ValueError("Geçersiz kıvam sınıfı")
        return v

    @field_validator("exposure_class", mode="before")
    @classmethod
    def validate_exposure_class(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            v = v.strip().upper()
            if not v:
                return None
        if v not in ALLOWED_EXPOSURE_CLASSES:
            raise ValueError("Geçersiz maruziyet sınıfı")
        return v

    class Config:
        schema_extra = {
            "example": {
                "recipe_code": "C25/30-S3-001",
                "concrete_class": "C25/30",
                "cement_type": "CEM I 42.5R",
                "cement_content": 340,
                "water_cement_ratio": 0.48,
                "aggregate_0_2": 0,
                "aggregate_0_5": 680,
                "aggregate_5_12": 420,
                "aggregate_12_22": 580,
                "aggregate_0_315": 0,
                "admixture_type": "Süperakışkanlaştırıcı",
                "admixture_content": 3.4,
                "target_slump": 160,
                "target_strength": 30,
                "consistency_class": "S3",
                "exposure_class": "XC2"
            }
        }


class ConcreteRecipe(ConcreteRecipeCreate):
    id: int
    actual_strength: Optional[float] = None
    is_active: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class WeeklyReport(BaseModel):
    week_start: str
    week_end: str
    week_number: int
    year: int
    sieve_summary: Dict[str, Any]
    pollution_summary: Dict[str, Any]
    non_conformities: list
    recommendations: list
    overall_status: str
    generated_at: str
