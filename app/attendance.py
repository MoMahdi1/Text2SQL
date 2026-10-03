from datetime import time


DEFAULT_SHIFT_START = time(9, 0)
DEFAULT_SHIFT_END = time(17, 0)
DEFAULT_GRACE_PERIOD_MINUTES = 15


def calculate_late_minutes(
    check_in_time: time,
    shift_start_time: time = DEFAULT_SHIFT_START,
    grace_period_minutes: int = DEFAULT_GRACE_PERIOD_MINUTES,
) -> int:
    """Return minutes beyond the grace deadline; zero means not late."""

    if grace_period_minutes < 0:
        raise ValueError("grace_period_minutes cannot be negative")

    check_in_seconds = (
        check_in_time.hour * 3600 + check_in_time.minute * 60 + check_in_time.second
    )
    shift_start_seconds = (
        shift_start_time.hour * 3600
        + shift_start_time.minute * 60
        + shift_start_time.second
    )
    seconds_after_deadline = (
        check_in_seconds - shift_start_seconds - grace_period_minutes * 60
    )
    if seconds_after_deadline <= 0:
        return 0
    return (seconds_after_deadline + 59) // 60


def attendance_policy_prompt() -> str:
    """Describe the persisted attendance policy for the SQL generator."""

    return (
        "Attendance defaults: shift starts at 09:00, ends at 17:00, and has a "
        "15-minute grace period. The attendance_records table stores the policy "
        "used for each day. Use its generated is_late and late_minutes columns "
        "instead of recreating the lateness calculation. A NULL check_out_time "
        "means the employee has checked in but has not checked out."
    )
