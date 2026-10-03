from datetime import time

import pytest

from app.attendance import attendance_policy_prompt, calculate_late_minutes


@pytest.mark.parametrize(
    ("check_in", "expected_minutes"),
    [
        (time(8, 55), 0),
        (time(9, 0), 0),
        (time(9, 15), 0),
        (time(9, 15, 1), 1),
        (time(9, 16), 1),
        (time(9, 35), 20),
    ],
)
def test_calculate_late_minutes(check_in: time, expected_minutes: int) -> None:
    assert calculate_late_minutes(check_in) == expected_minutes


def test_calculate_late_minutes_supports_row_specific_policy() -> None:
    assert calculate_late_minutes(time(10, 11), time(10, 0), 10) == 1


def test_calculate_late_minutes_rejects_negative_grace_period() -> None:
    with pytest.raises(ValueError):
        calculate_late_minutes(time(9, 0), grace_period_minutes=-1)


def test_attendance_policy_prompt_explains_persisted_business_rules() -> None:
    prompt = attendance_policy_prompt()

    assert "09:00" in prompt
    assert "17:00" in prompt
    assert "15-minute" in prompt
    assert "is_late" in prompt
    assert "NULL check_out_time" in prompt
