"""golden-mini fixture component: a 3-state event-driven machine."""


class RejectedError(Exception):
    """The component rejected the event."""


class Mini:
    """Three-state machine used by the StateRadar golden fixture."""

    def __init__(self) -> None:
        self.state = "Idle"
        self.dup_count = 0

    def deliver(self, event: str) -> str:
        """Deliver one event through the declared seam."""
        if event == "M1":
            if self.state == "Idle":
                self.state = "Open"
                return "transition"
            if self.state == "Open":
                return "ignored"
            raise RejectedError("M1 rejected in Closed")
        if event == "M2":
            if self.state == "Open":
                self.state = "Closed"
                return "transition"
            return "ignored"
        if event == "UV-M1-dup":
            self.dup_count += 1
            if self.dup_count >= 2:  # F-14 duplication: repeat is not idempotent
                self.state = "Closed"
            return "handled"
        if event == "UV-M2-stale":
            return "ignored"
        if event == "UV-M1-lost":
            return "ignored"
        if event == "UV-M2-conflict":
            return "ignored"
        if event == "UV-M1-spurious":
            raise RejectedError("UV-M1-spurious rejected")
        raise ValueError(event)
