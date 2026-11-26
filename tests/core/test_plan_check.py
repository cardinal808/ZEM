"""Plan against reality (B38): day totals of the day-ahead expectations next to what was measured."""

from __future__ import annotations

from datetime import date

import pytest

from zephyr_core import plan_check
from zephyr_core.costs import add_to_day


def _record(**kw: object) -> dict[str, object]:
    base = {
        "complete": True,
        "import_kwh": 0.2,
        "export_kwh": 0.0,
        "house_kwh": 0.5,
        "solar_kwh": 0.3,
        "excluded_kwh": 0.1,
        "cost": 0.05,
        "soc": 40.0,
    }
    base.update(kw)
    return base


def _expected(**kw: float) -> dict[str, object]:
    exp = {"load": 0.35, "excluded": 0.1, "solar": 0.4, "import": 0.1, "export": 0.0, "cost": 0.03, "soc": 42.0}
    exp.update(kw)
    return plan_check.record_fields(exp)


def test_record_fields() -> None:
    assert plan_check.record_fields(None) == {}
    fields = _expected()
    assert fields["ahead_load_kwh"] == 0.35 and fields["ahead_cost"] == 0.03 and fields["ahead_soc"] == 42.0


def test_day_compares_only_quarters_with_a_plan() -> None:
    day: dict[str, float] = {}
    add_to_day(day, _record())  # no day-ahead plan (e.g. the first day)
    add_to_day(day, _record(**_expected()))
    add_to_day(day, _record(soc=38.0, **_expected(load=0.5, soc=41.0)))
    check = plan_check.day_check("2026-11-27", day)
    assert check is not None
    assert check["quarters"] == 2 and check["of"] == 3
    # Measured use = house without the air conditioner: 0.4 per quarter.
    assert check["load"] == {"expected": pytest.approx(0.85), "actual": pytest.approx(0.8), "diff": pytest.approx(-0.05)}
    assert check["load_abs_err"] == pytest.approx(0.15)
    assert check["solar"]["expected"] == pytest.approx(0.8) and check["solar"]["actual"] == pytest.approx(0.6)
    assert check["cost"]["diff"] == pytest.approx(0.04)
    assert check["soc_end"] == {"expected": 41.0, "actual": 38.0}


def test_no_solar_or_price_measured() -> None:
    day: dict[str, float] = {}
    add_to_day(day, _record(solar_kwh=None, house_kwh=None, cost=None, **_expected()))
    check = plan_check.day_check("2026-11-27", day)
    assert check is not None and "solar" not in check and "load" not in check and "cost" not in check
    assert check["import"]["actual"] == pytest.approx(0.2)


def test_checks_and_summary() -> None:
    days: dict[str, dict[str, float]] = {"2026-11-25": {}, "2026-11-26": {}, "2026-11-27": {}}
    add_to_day(days["2026-11-25"], _record())
    add_to_day(days["2026-11-26"], _record(**_expected()))
    add_to_day(days["2026-11-27"], _record(**_expected(load=0.5)))
    items = plan_check.checks(days, date(2026, 11, 25), date(2026, 11, 27))
    assert [i["date"] for i in items] == ["2026-11-26", "2026-11-27"]
    total = plan_check.summary(items)
    assert total["days"] == 2
    assert total["load"]["expected"] == pytest.approx(0.85) and total["load"]["mean_abs_day"] == pytest.approx(0.075)
    assert plan_check.day_check("2026-11-25", days["2026-11-25"]) is None
