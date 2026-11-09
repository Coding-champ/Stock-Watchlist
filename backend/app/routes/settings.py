from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app import schemas
from backend.app.database import get_db
from backend.app.models import ApplicationSetting

router = APIRouter(prefix="/settings", tags=["settings"])

DEFAULTS = {
    "display_mode": "compact",
    "default_page": "overview",
    "theme": "default",
}

THEMES = [
    schemas.ThemePalette(
        id="default",
        name="Standard",
        variables={
            "--brand-primary": "#7c3aed",
            "--brand-primary-dark": "#5b21b6",
            "--brand-primary-light": "#c084fc",
            "--brand-secondary": "#6366f1",
            "--brand-primary-rgb": "124, 58, 237",
            "--brand-primary-dark-rgb": "91, 33, 182",
            "--brand-secondary-rgb": "99, 102, 241",
            "--brand-border": "rgba(124, 58, 237, 0.18)",
            "--brand-border-strong": "rgba(91, 33, 182, 0.38)",
            "--brand-surface-muted": "#f6f3ff",
            "--brand-surface-table": "#f1e9ff",
            "--brand-filter-surface": "rgba(243, 232, 255, 0.9)",
            "--brand-filter-hover": "rgba(221, 214, 254, 0.85)",
            "--brand-filter-label": "#5b21b6",
            "--brand-tab-border": "#e9ecef",
            "--brand-tab-text": "#6c757d",
            "--brand-tab-hover": "rgba(124, 58, 237, 0.05)",
            "--brand-tab-hover-border": "rgba(124, 58, 237, 0.3)",
            "--brand-tab-active": "#7c3aed",
            "--brand-tab-active-bg": "rgba(124, 58, 237, 0.08)",
        },
    ),
    schemas.ThemePalette(
        id="orange",
        name="Orange",
        variables={
            "--brand-primary": "#ea580c",
            "--brand-primary-dark": "#9a3412",
            "--brand-primary-light": "#fb923c",
            "--brand-secondary": "#f97316",
            "--brand-primary-rgb": "234, 88, 12",
            "--brand-primary-dark-rgb": "154, 52, 18",
            "--brand-secondary-rgb": "249, 115, 22",
            "--brand-surface-table": "#fff1e8",
            "--brand-filter-surface": "rgba(255, 237, 224, 0.92)",
            "--brand-filter-hover": "rgba(255, 224, 204, 0.9)",
            "--brand-filter-label": "#9a3412",
            "--brand-tab-border": "#f1d8c8",
            "--brand-tab-text": "#7c6256",
            "--brand-tab-hover": "rgba(234, 88, 12, 0.05)",
            "--brand-tab-hover-border": "rgba(234, 88, 12, 0.3)",
            "--brand-tab-active": "#ea580c",
            "--brand-tab-active-bg": "rgba(234, 88, 12, 0.08)",
            "--brand-border": "rgba(234, 88, 12, 0.18)",
            "--brand-border-strong": "rgba(154, 52, 18, 0.38)",
            "--brand-surface-muted": "#fff7ed",
        },
    ),
]


def _read_settings(db: Session):
    rows = {item.key: item.value for item in db.query(ApplicationSetting).all()}
    return {key: rows.get(key, value) for key, value in DEFAULTS.items()}


@router.get("", response_model=schemas.ApplicationSettings)
def get_settings(db: Session = Depends(get_db)):
    return _read_settings(db)


@router.put("", response_model=schemas.ApplicationSettings)
def update_settings(payload: schemas.ApplicationSettingsUpdate, db: Session = Depends(get_db)):
    values = payload.model_dump(exclude_none=True)
    for key, value in values.items():
        setting = db.get(ApplicationSetting, key)
        if setting:
            setting.value = value
        else:
            db.add(ApplicationSetting(key=key, value=value))
    db.commit()
    return _read_settings(db)


@router.get("/themes", response_model=list[schemas.ThemePalette])
def get_themes():
    return THEMES
