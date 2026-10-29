"""Validated boundaries; graph state itself holds only JSON-compatible values."""
from datetime import date
from decimal import Decimal
from hashlib import sha256
import json
import unicodedata
from pydantic import BaseModel, Field, field_validator


class Criterion(BaseModel):
    criterion_id: int
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    weight: Decimal = Field(ge=0, allow_inf_nan=False)
    max_score: Decimal = Field(gt=0, allow_inf_nan=False)
    is_active: bool = True


class SupplierInput(BaseModel):
    supplier_id: str
    supplier_name: str = Field(min_length=1, max_length=120)
    submission_date: date
    experience_rating: Decimal = Field(ge=0, le=10, allow_inf_nan=False)
    file_sha256: str
    artifact_ref: str
    filename: str

    @field_validator('supplier_name')
    @classmethod
    def clean_name(cls, value):
        value = unicodedata.normalize('NFKC', value).strip()
        if not value:
            raise ValueError('Supplier name is required')
        return value


def canonical(value):
    return unicodedata.normalize('NFKC', value).strip().casefold()


def digest(value):
    return sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def validate_criteria(rows):
    items = [Criterion.model_validate(c) for c in rows if c.get('is_active', True)]
    if not items or len({c.criterion_id for c in items}) != len(items):
        raise ValueError('At least one active criterion and unique IDs are required.')
    if sum(c.weight for c in items) != Decimal(100):
        raise ValueError('Active criteria weights must total exactly 100%. Update criteria before evaluating.')
    return [c.model_dump(mode='json') for c in sorted(items, key=lambda c: c.criterion_id)]
