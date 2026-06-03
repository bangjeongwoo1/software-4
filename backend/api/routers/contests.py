from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from ..database import get_client
from ..schemas.contest import ContestSummary, ContestDetail, ContestListResponse

router = APIRouter()

_JOIN_SELECT = (
    "contest_id,title,detail_url,status,"
    "contest_detail_1(title,host,target_text,reception_start,reception_end,"
    "review_start,review_end,announcement_date,d_day),"
    "contest_detail_2(host_organization,main_field,target_text,reception_period_text,"
    "review_period_text,contest_region,award_text,homepage_url,application_method,"
    "application_url,participation_fee,detail_text)"
)


def _normalize(row: dict) -> ContestSummary:
    d1 = (row.get("contest_detail_1") or [{}])
    d1 = d1[0] if isinstance(d1, list) else d1

    d2 = (row.get("contest_detail_2") or [{}])
    d2 = d2[0] if isinstance(d2, list) else d2

    title = d1.get("title") or row.get("title")
    host = d1.get("host") or d2.get("host_organization")

    return ContestSummary(
        id=row["contest_id"],
        title=title,
        host=host,
        field=d2.get("main_field"),
        prize=d2.get("award_text"),
        deadline=d1.get("reception_end"),
        d_day=d1.get("d_day"),
        status=row.get("status"),
        detail_url=row.get("detail_url"),
    )


def _normalize_detail(row: dict) -> ContestDetail:
    summary = _normalize(row)

    d1 = (row.get("contest_detail_1") or [{}])
    d1 = d1[0] if isinstance(d1, list) else d1

    d2 = (row.get("contest_detail_2") or [{}])
    d2 = d2[0] if isinstance(d2, list) else d2

    return ContestDetail(
        **summary.model_dump(),
        description=d2.get("detail_text"),
        eligibility=d2.get("target_text"),
        target_text=d1.get("target_text"),
        reception_period_text=d2.get("reception_period_text"),
        review_period_text=d2.get("review_period_text"),
        contest_region=d2.get("contest_region"),
        application_method=d2.get("application_method"),
        application_url=d2.get("application_url") or d2.get("homepage_url"),
        participation_fee=d2.get("participation_fee"),
        reception_start=d1.get("reception_start"),
        reception_end=d1.get("reception_end"),
        announcement_date=d1.get("announcement_date"),
        raw=row,
    )


@router.get("", response_model=ContestListResponse)
def list_contests(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    keyword: str | None = None,
    field: str | None = None,
    sort: str = Query("deadline_asc", enum=["deadline_asc", "deadline_desc", "latest"]),
):
    db = get_client()
    query = db.table("contest").select(_JOIN_SELECT)

    if keyword:
        query = query.ilike("title", f"%{keyword}%")

    resp = query.execute()
    rows = resp.data or []

    if field:
        def field_match(row: dict) -> bool:
            d2 = (row.get("contest_detail_2") or [{}])
            d2 = d2[0] if isinstance(d2, list) else d2
            return (d2.get("main_field") or "") == field
        rows = [r for r in rows if field_match(r)]

    items = [_normalize(r) for r in rows]

    def sort_key(c: ContestSummary):
        return c.deadline or ""

    if sort == "deadline_asc":
        items.sort(key=sort_key)
    elif sort == "deadline_desc":
        items.sort(key=sort_key, reverse=True)

    total = len(items)
    start = (page - 1) * size
    paged = items[start: start + size]

    return ContestListResponse(total=total, page=page, size=size, items=paged)


@router.get("/{contest_id}", response_model=ContestDetail)
def get_contest(contest_id: int):
    db = get_client()
    resp = db.table("contest").select(_JOIN_SELECT).eq("contest_id", contest_id).execute()

    if not resp.data:
        raise HTTPException(status_code=404, detail="해당 공모전을 찾을 수 없습니다.")

    return _normalize_detail(resp.data[0])
