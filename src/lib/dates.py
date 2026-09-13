from datetime import datetime, timedelta, timezone


def get_current_date():
    tz = timezone(timedelta(hours=-4))
    return datetime.now(tz=tz).replace(tzinfo=None)
