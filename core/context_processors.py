"""
Template context processors.
"""
import random
from django.conf import settings


def daily_quote(request):
    """Inject a random motivational quote into all templates."""
    quotes = getattr(settings, 'MOTIVATIONAL_QUOTES', [])
    # Use day-of-year as seed so the same quote shows all day
    import datetime
    day = datetime.date.today().timetuple().tm_yday
    if quotes:
        quote = quotes[day % len(quotes)]
    else:
        quote = ""
    return {'daily_quote': quote}
