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
            return "handled"
        if event == "UV-M2-stale":
            return "ignored"
        if event == "UV-M1-lost":
            return "ignored"
        if event == "UV-M2-conflict":
            return "ignored"
        if event == "UV-M1-spurious":
            raise RejectedError("UV-M1-spurious rejected")
        if event == "svc-ack":
            if self.state == "Idle":
                # Structurally unreachable: the service only acknowledges a
                # delivered M1, so no ack can exist here. Rejecting makes a
                # breach of that upstream guarantee loud instead of silent.
                raise RejectedError("svc-ack without a delivered M1")
            if self.state == "Open":
                self.dup_count += 1
                return "handled"
            return "ignored"
        raise ValueError(event)
