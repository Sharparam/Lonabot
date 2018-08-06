import re
from datetime import datetime, timedelta


_UNITS_RE = re.compile(
    r'(y(?:ears?)?'
    r'|w(?:eeks?)?'
    r'|d(?:ays?)?'
    r'|h(?:ours?)?'
    r'|m(?:in(?:ute)?s?)?'
    r'|s(?:ecs?)?'
    r')((?:\b|\d).*)',
    re.IGNORECASE
)

_UNITS = {
    'y': 31536000.0,
    'w': 604800.0,
    'd': 86400.0,
    'h': 3600.0,
    'm': 60.0,
    's': 1.0
}


def parse_delay(when):
    m = re.match(r'(\d+):(\d+)(?::(\d+))?', when)
    if m:
        text = when[m.end():]
        hour = int(m.group(1))
        mins = int(m.group(2))
        secs = int(m.group(3) or 0)
        delay = (hour * 60 + mins) * 60 + secs
    else:
        # Try matching integers + possible units
        when = when.split() + ['']
        delay = 0.0
        i = 0
        while i < len(when):
            m = re.match(r'(\d+(?:\.\d+)?)(.+)?', when[i])
            if not m:
                break
            value = float(m.group(1))
            unit = m.group(2)
            if not unit:
                i += 1
                unit = when[i]

            n = _UNITS_RE.match(unit)
            if n:
                unit = n.group(1)[0].lower()
                if unit in _UNITS:
                    delay += value * _UNITS[unit]
                    if n.group(2):
                        # {unit}{number + stuff} <- may be another value
                        when[i] = n.group(2)
                        i -= 1
                else:
                    delay += value * 60.0
                    when[i] = n.group(0)
                    break  # {invalid unit} <- assume user's text
            else:
                if int(delay):
                    # The value should belong to the user's text unless
                    # we already have something that's not gibberish.
                    when[i] = m.group(0)
                else:
                    delay += value * 60.0
                    if m.group(2):
                        # Assume the thing after the value is user's text
                        when[i] = m.group(2)
                break

            i += 1
        text = ' '.join(when[i:-1])

    due = int(datetime.utcnow().timestamp() + delay) if int(delay) else None
    return due, text


def parse_due(due, delta):
    m = re.match(r'(\d+)(?::(\d+))?(?::(\d+))?', due)
    if not m:
        return None, due

    hour = int(m.group(1))
    mins = int(m.group(2) or 0)
    secs = int(m.group(3) or 0)
    text = due[m.end():]
    now = datetime.utcnow() + timedelta(seconds=delta)  # Work in local time
    due = datetime(
        now.year, now.month, now.day, hour, mins, secs, 0, now.tzinfo)

    if due < now:
        due += timedelta(days=1)

    # But return UTC time
    return int(due.timestamp() - delta), text


def spell_digit(n):
    return ['zero', 'one', 'two', 'three', 'four',
            'five', 'six', 'seven', 'eight', 'nine'][n]


def spell_ten(n):
    return ['ten', 'twenty', 'thirty', 'forty', 'fifty',
            'sixty', 'seventy', 'eighty', 'ninety'][n - 1]


def spell_number(n, allow_and=True):
    # In the range of [0..1_000_000), for now
    if n < 0:
        spelt = 'minus'
        n = -n
    else:
        spelt = ''

    add_and = False
    if n >= 1000:
        add_and = allow_and
        high, n = divmod(n, 1000)
        spelt += f' {spell_number(high, allow_and=False)} thousand'
    if n >= 100:
        add_and = allow_and
        high, n = divmod(n, 100)
        spelt += f' {spell_digit(high)} hundred'
    if n >= 20:
        if add_and:
            spelt += ' and'
            add_and = False
        high, n = divmod(n, 10)
        spelt += f' {spell_ten(high)}'
    elif n >= 10:
        if add_and:
            spelt += ' and'
            add_and = False
        spelt += ' ' + [
            'ten', 'eleven', 'twelve', 'thirteen', 'fourteen',
            'fifteen', 'sixteen', 'seventeen', 'eighteen', 'nineteen'
        ][n - 10]
        n = 0

    if n or not spelt:
        if add_and:
            spelt += ' and'
        spelt += ' ' + spell_digit(n)

    return spelt.lstrip()


def spell_due(due, utc_delta=None, prefix=True):
    if prefix and utc_delta is not None:
        # Looks like doing .utcfromtimestamp "subtracts" the +N local time…?
        due = datetime.fromtimestamp(due + utc_delta)
        return f'due to {due}'

    spelt = 'due in' if prefix else ''
    remaining = int(due - datetime.utcnow().timestamp())
    if remaining < 60:
        spelt += f' {remaining} second'
        if remaining > 1:
            spelt += 's'
        return spelt.lstrip()
    if remaining >= 86400:
        days, remaining = divmod(remaining, 86400)
        spelt += f' {days} day'
        if days > 1:
            spelt += 's'
    if remaining >= 3600:
        hours, remaining = divmod(remaining, 3600)
        spelt += f' {hours} hour'
        if hours > 1:
            spelt += 's'
    mins, remaining = divmod(remaining, 60)
    spelt += f' {mins} minute'
    if mins > 1:
        spelt += 's'
    return spelt.lstrip()


def large_round(number, precision):
    # e.g. large_round(11, 5) -> 10
    return round(number / precision) * precision