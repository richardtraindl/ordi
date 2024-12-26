

from datetime import datetime, date, timedelta
from ..values import ANREDE, GESCHLECHT, IMPFUNG, ARTIKEL
from .helper import reverse_lookup, gibFeiertag


def mapanrede(anredecode):
    anrede = reverse_lookup(ANREDE, anredecode)
    if(anrede == None):
        anrede = ""
    return anrede


def mapgeschlecht(geschlechtscode):
    geschlecht = reverse_lookup(GESCHLECHT, geschlechtscode)
    if(geschlecht == None):
        geschlecht = ""
    return geschlecht


def mapimpfung(impfungscode):
    impfung = reverse_lookup(IMPFUNG, impfungscode)
    if(impfung == None):
        impfung = ""
    return impfung


def mapartikel(artikelcode):
    artikel = reverse_lookup(ARTIKEL, artikelcode)
    if(artikel == None):
        artikel = ""
    return artikel


def conv_curr(amount): 
  import locale 
  locale.setlocale(locale.LC_ALL, 'de_AT.UTF-8')
  return locale.currency(amount, symbol=False, grouping=False, international=False)


def filter_supress_none(val):
    if not val is None:
        return val
    else:
        return ""


def filter_format_date(val):
    if not val is None:
        if(val.year==1900 and val.month==1 and val.day==1):
            return ""
        else:
            try:
                return val.strftime("%d.%m.%Y")
            except:
                return ""
    else:
        return ""


def filter_mformat_date(val):
    if not val is None:
        if(val.year==1900 and val.month==1 and val.day==1):
            return ""
        else:
            try:
                return val.strftime("%d.%m. %Y")
            except:
                return ""
    else:
        return ""


def filter_format_datetime(val):
    if not val is None:
        return val.strftime("%d.%m.%Y, %H:%M")
    else:
        return ""


def calc_kw(now):
    dt = date(now.year, now.month, now.day)

    # Determine its Day of Week, D
    # Use that to move to the nearest Thursday (-3..+3 days)
    add = 4 - dt.weekday()
    dt += timedelta(days=add)

    # Note the year of that date, Y
    # Obtain January 1 of that year
    firstofyear = date(dt.year, 1, 1)

    # Get the Ordinal Date of that Thursday, DDD of YYYY-DDD
    ydays = (dt - firstofyear).days + 1

    # Then W is 1 + (DDD-1) div 7
    return int(1 + (ydays / 7))


def add_days(dt, days):
    return dt + timedelta(days=days)


def add_hours(dt, hours):
    return dt + timedelta(hours=hours)


def add_mins(dt, mins):
    return dt + timedelta(minutes=mins)


def gib_feiertag(now):
    return gibFeiertag(now)
