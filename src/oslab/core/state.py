"""Machine states and the only allowed transitions."""

IDLE = "idle"
BOOTING = "booting"
RUNNING = "running"
STOPPED = "stopped"
FAULTED = "faulted"

ALLOWED = {
    IDLE: (BOOTING,),
    BOOTING: (RUNNING, STOPPED, FAULTED),
    RUNNING: (STOPPED, FAULTED, IDLE),
    STOPPED: (RUNNING, BOOTING, FAULTED, IDLE),
    FAULTED: (BOOTING, IDLE),
}
