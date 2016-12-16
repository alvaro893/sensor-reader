def int_to_bytes(n):
    s = '%x' % n
    if len(s) & 1:
        s = '0' + s
    return s.decode('hex')


def from_bytes_to_int(s):
    if type(s) != 'str':
        s = str(s)
    return int(s.encode('hex'), 16)


def descale(val, pmin, pmax):
    """
    :return: tuple with a value and the next
    """
    raw_val = val * (pmax - pmin) / 254 + pmin
    return raw_val >> 8, (raw_val & 0xff)+1


def scale(val, other, pmin, pmax):  # for consulting purposes
    raw = val << 8 | other
    return ((raw - pmin) * 254) / (pmax - pmin)
