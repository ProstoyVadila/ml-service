from enum import Enum

from prometheus_client import Counter


class Counters(Enum):
    timeouts = Counter("timeouts", "Number of timeouts")
    exceptions = Counter("exceptions", "Number of exceptions")
