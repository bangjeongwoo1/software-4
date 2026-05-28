from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from ..database import get_client
from ..schemas.scholarship import ScholarshipSummary, ScholarshipDetail, ScholarshipListResponse

router = APIRouter()

_JOIN_SELECT = (
    "scholarship_id,source_type,title,detail_url,status,"
    "customized_detail_1(title,scholarship_type,benefit_type,summary),"
    "customized_detail_2(campus_text,grade_min,grade_max,gpa_prev_semester_value,"
    "amount_text,eligibility_text,application_method_text,related_document_url),"
    "notice_detail_1(campus_text,author,registered_at,view_count),"
    "notice_detail_2(title,campus_text,contact_phone,raw_text,attachment_file_url,image_file_url),"
    "notice_llm(notice_title,summary,amount_text,department_text,grade_text,"
    "grade_min,grade_max,gpa_min,application_start_date,application_close_date)"
)


def _normalize(row: dict) -> ScholarshipSummary:
    c1 = (row.get("customized_detail_1") or [{}])
    c1 = c1[0] if isinstance(c1, list) else c1

    c2 = (row.get("customized_detail_2") or [{}])
    c2 = c2[0] if isinstance(c2, list) else c2

    n1 = (row.get("notice_detail_1") or [{}])
    n1 = n1[0] if isinstance(n1, list) else n1

    n2 = (row.get("notice_detail_2") or [{}])
    n2 = n2[0] if isinstance(n2, list) else n2

    llm = (row.get("notice_llm") or [{}])
    llm = llm[0] if isinstance(llm, list) else llm

    title = c1.get("title") or n2.get("title") or llm.get("notice_title") or row.get("title")
    amount = c2.get("amount_text") or llm.get("amount_text")
    deadline = c2.get("selection_period_text") or llm.get("application_close_date")
    organization = n1.get("author")
    category = c1.get("scholarship_type") or c1.get("benefit_type")
    campus_text = c2.get("campus_text") or n1.get("campus_text") or n2.get("campus_text")

    grades: list[int] = []
    grade_min = c2.get("grade_min") or llm.get("grade_min")
    grade_max = c2.get("grade_max") or llm.get("grade_max")
    if grade_min and grade_max:
        grades = list(range(int(grade_min), int(grade_max) + 1))
    elif grade_min:
        grades = [int(grade_min)]

    return ScholarshipSummary(
        id=row["scholarship_id"],
        title=title,
        organization=organization,
        category=category,
        amount=amount,
        deadline=deadline,
        status=row.get("status"),
        source_type=row.get("source_type"),
        target_grades=grades,
        detail_url=row.get("detail_url"),
    )


def _normalize_detail(row: dict) -> ScholarshipDetail:
    summary = _normalize(row)

    c2 = (row.get("customized_detail_2") or [{}])
    c2 = c2[0] if isinstance(c2, list) else c2

    n2 = (row.get("notice_detail_2") or [{}])
    n2 = n2[0] if isinstance(n2, list) else n2

    llm = (row.get("notice_llm") or [{}])
    llm = llm[0] if isinstance(llm, list) else llm

    return ScholarshipDetail(
        **summary.model_dump(),
        summary=c2.get("summary") or llm.get("summary"),
        eligibility=c2.get("eligibility_text"),
        application_method=c2.get("application_method_text"),
        application_url=c2.get("related_document_url"),
        application_start=llm.get("application_start_date"),
        application_end=llm.get("application_close_date"),
        contact=n2.get("contact_phone"),
        campus_text=summary.detail_url and c2.get("campus_text"),
        department_text=llm.get("department_text"),
        grade_text=llm.get("grade_text"),
        gpa_min=llm.get("gpa_min"),
        raw=row,
    )


@router.get("", response_model=ScholarshipListResponse)
def list_scholarships(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    keyword: str | None = None,
    grade: int | None = Query(None, ge=1, le=4),
    sort: str = Query("deadline_asc", enum=["deadline_asc", "deadline_desc", "latest"]),
):
    db = get_client()
    query = db.table("scholarship").select(_JOIN_SELECT)

    if keyword:
        query = query.ilike("title", f"%{keyword}%")

    resp = query.execute()
    rows = resp.data or []

    if grade is not None:
        def grade_match(row: dict) -> bool:
            c2 = row.get("customized_detail_2")
            c2 = c2[0] if isinstance(c2, list) and c2 else (c2 or {})
            llm = row.get("notice_llm")
            llm = llm[0] if isinstance(llm, list) and llm else (llm or {})
            g_min = c2.get("grade_min") if c2.get("grade_min") is not None else llm.get("grade_min")
            g_max = c2.get("grade_max") if c2.get("grade_max") is not None else llm.get("grade_max")
            if g_min is None and g_max is None:
                return True
            g_min = int(g_min) if g_min is not None else 1
            g_max = int(g_max) if g_max is not None else 4
            return g_min <= grade <= g_max
        rows = [r for r in rows if grade_match(r)]

    items = [_normalize(r) for r in rows]

    def sort_key(s: ScholarshipSummary):
        return s.deadline or ""

    if sort == "deadline_asc":
        items.sort(key=sort_key)
    elif sort == "deadline_desc":
        items.sort(key=sort_key, reverse=True)

    total = len(items)
    start = (page - 1) * size
    paged = items[start: start + size]

    return ScholarshipListResponse(total=total, page=page, size=size, items=paged)


@router.get("/{scholarship_id}", response_model=ScholarshipDetail)
def get_scholarship(scholarship_id: int):
    db = get_client()
    resp = db.table("scholarship").select(_JOIN_SELECT).eq("scholarship_id", scholarship_id).execute()

    if not resp.data:
        raise HTTPException(status_code=404, detail="해당 장학금을 찾을 수 없습니다.")

    return _normalize_detail(resp.data[0])
