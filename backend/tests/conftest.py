"""Shared pytest configuration.

이 conftest는 두 가지 일을 한다.
1. backend/ 디렉터리를 sys.path에 추가해서 scholarship.parser, contest.contest_parser 모듈을
   바로 import 할 수 있게 한다. 이 tests/ 폴더를 backend/tests/ 안에 두고 실행하면 된다.
2. 오늘 날짜에 의존하는 함수 (build_status, calc_d_day 등) 테스트를 위해
   각 모듈의 ``date`` 심볼을 ``FakeDate`` 로 패치하는 ``frozen_today`` fixture 제공.
"""

from __future__ import annotations

import datetime
import sys
from pathlib import Path

import pytest

# backend/ 를 sys.path에 추가
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


FROZEN_TODAY = datetime.date(2026, 6, 5)


def _make_fake_date(today_value: datetime.date):
    class FakeDate(datetime.date):
        @classmethod
        def today(cls):
            return today_value

    return FakeDate


@pytest.fixture
def frozen_today(monkeypatch):
    """Freeze date.today() in scholarship.parser and contest.contest_parser."""

    fake = _make_fake_date(FROZEN_TODAY)
    import scholarship.parser as sp
    import contest.contest_parser as cp

    monkeypatch.setattr(sp, "date", fake)
    monkeypatch.setattr(cp, "date", fake)
    return FROZEN_TODAY
