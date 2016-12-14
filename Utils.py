def int_to_bytes(n):
    s = '%x' % n
    if len(s) & 1:
        s = '0' + s
    return s.decode('hex')


def from_bytes_to_int(s):
    if type(s) != 'str':
        s = str(s)
    return int(s.encode('hex'), 16)