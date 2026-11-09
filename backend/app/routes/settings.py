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
            "--brand-border": "rgba(124, 58, 237, 0.18)",
            "--brand-border-strong": "rgba(91, 33, 182, 0.38)",
            "--brand-surface-muted": "#f6f3ff",
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
