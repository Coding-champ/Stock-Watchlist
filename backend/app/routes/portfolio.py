from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from backend.app import schemas
from backend.app.database import get_db
from backend.app.services.portfolio_service import PortfolioService


router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.get("", response_model=schemas.PortfolioResponse)
@router.get("/", response_model=schemas.PortfolioResponse, include_in_schema=False)
def get_portfolio(db: Session = Depends(get_db)):
    return PortfolioService(db).get_portfolio()


@router.post(
    "/holdings",
    response_model=schemas.PortfolioHoldingResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_holding(
    payload: schemas.PortfolioHoldingCreate,
    db: Session = Depends(get_db),
):
    try:
        service = PortfolioService(db)
        holding = service.add_holding(
            payload.identifier,
            payload.quantity,
            payload.purchase_price,
            payload.purchase_date,
        )
        return next(item for item in service.get_portfolio()["holdings"] if item["id"] == holding.id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post(
    "/holdings/{holding_id}/buy",
    response_model=schemas.PortfolioHoldingResponse,
)
def buy_holding(
    holding_id: int,
    payload: schemas.PortfolioHoldingBuy,
    db: Session = Depends(get_db),
):
    service = PortfolioService(db)
    try:
        service.buy_holding(
            holding_id,
            payload.quantity,
            payload.purchase_price,
            payload.purchase_date,
        )
        return next(
            item for item in service.get_portfolio()["holdings"] if item["id"] == holding_id
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.delete("/holdings/{holding_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_holding(holding_id: int, db: Session = Depends(get_db)):
    try:
        PortfolioService(db).delete_holding(holding_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
