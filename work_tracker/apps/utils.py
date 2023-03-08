from datetime import datetime
from decimal import Decimal

from work_tracker.apps.tracker.models import Entry


def calculate_billables(entry: Entry, start_time: datetime, end_time: datetime) -> Entry:
    """
    Calculate and update total_time, hours, bill of current Entry instance based off of specified
    start_time and end_time.

    Returns:
        Entry: Updated Entry instance.
    """
    user = entry.task.user
    total_time = (end_time - start_time).total_seconds()
    hours = round(Decimal(total_time / 3600), 6)
    bill = round(hours * user.rate, 2)

    # Update instance fields with calculated values.
    entry.total_time += total_time
    entry.hours += hours
    entry.bill += bill
    return entry
