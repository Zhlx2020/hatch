"""Process wide session handle set by __main__."""
_session = None


def install(session):
    global _session
    _session = session


def session():
    return _session
