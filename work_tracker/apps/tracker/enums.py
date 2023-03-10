from enumfields import Enum


class TaskType(Enum):
    FEATURE = 1
    BUG = 2
    DEV_OPS = 3
    DOCUMENTATION = 4
    REPORTING = 5
    INVESTIGATION = 6
    DATABASE = 7

    class Labels:
        DEV_OPS = "Dev Ops"


class TaskStatus(Enum):
    NEW = 1
    IN_PROGRESS = 2
    COMPLETED = 3
    NEEDS_FEEDBACK = 4
    CLOSED = 5

    class Labels:
        IN_PROGRESS = "In Progress"
        NEEDS_FEEDBACK = "Feedback Needed"


class EntryStatus(Enum):
    ACTIVE = 1
    PAUSED = 2
    COMPLETE = 3


class EntryAction(Enum):
    PAUSE = 1
    RESUME = 2
    COMPLETE = 3
