from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app import schemas
from backend.app.database import get_db
from backend.app.services.investment_check_service import InvestmentCheckService


router = APIRouter(prefix="/investment-check", tags=["investment-check"])


@router.post("", response_model=Dict[str, Any])
@router.post("/", response_model=Dict[str, Any], include_in_schema=False)
def run_investment_check(
    payload: schemas.InvestmentCheckRequest,
    db: Session = Depends(get_db),
):
    try:
        return InvestmentCheckService(db).run(payload.identifier, payload.quantity)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Investitions-Check konnte nicht berechnet werden.") from exc
