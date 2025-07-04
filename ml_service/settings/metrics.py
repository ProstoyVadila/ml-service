from enum import Enum

from prometheus_client import Counter


class Counters(Enum):
    REJECTED_REQUESTS = Counter(
        "rejected_requests", "Number of rejected requests due to throttling"
    )
    SUCCESSFUL_REQUESTS = Counter(
        "successful_requests", "Number of successfully processed requests"
    )
    TIMEOUTS = Counter("timeouts", "Number of timeouts")
    EXCEPTIONS = Counter("exceptions", "Number of exceptions")
