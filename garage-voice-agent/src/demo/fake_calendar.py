from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from schemas import TimeSlot

PARIS_TZ = ZoneInfo("Europe/Paris")


def _next_business_day(start: date, offset: int) -> date:
    day = start
    remaining = offset
    while remaining:
        day += timedelta(days=1)
        if day.weekday() < 5:
            remaining -= 1
    return day


def generate_mock_slots(
    requested_date: str | None,
    requested_period: str | None,
    service_type: str,
) -> list[TimeSlot]:
    if requested_date:
        try:
            base_date = datetime.fromisoformat(requested_date).date()
        except ValueError:
            base_date = date.today()
    else:
        base_date = date.today()

    period = requested_period or "journee"
    times = {
        "matin": ["09:00", "10:30", "11:30"],
        "apres-midi": ["14:00", "15:30", "17:00"],
        "après-midi": ["14:00", "15:30", "17:00"],
        "journee": ["09:30", "14:00", "16:30"],
        "journée": ["09:30", "14:00", "16:30"],
    }.get(period.lower(), ["09:30", "14:00", "16:30"])

    slots: list[TimeSlot] = []
    for index, time_value in enumerate(times, start=1):
        day = _next_business_day(base_date, index)
        slot_datetime = datetime.combine(day, time.fromisoformat(time_value), PARIS_TZ)
        slots.append(
            TimeSlot(
                slot_id=f"mock-{service_type.lower().replace(' ', '-')}-{index}",
                datetime=slot_datetime.isoformat(),
                period=period,
                service_type=service_type,
            )
        )
    return slots
