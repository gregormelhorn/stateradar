"""
Synthetic device connection manager for StateRadar demonstration.

A stateful component that manages the lifecycle of a single device
connection: connection attempts, timeouts, retry backoff, cancellation,
and terminal failure after exhausting retries.

This is NOT production code. It exists to demonstrate the complete
StateRadar analysis workflow on a bounded, understandable component.
"""

import asyncio
import random
from dataclasses import dataclass
from enum import Enum, auto


class State(Enum):
    DISCONNECTED = auto()
    CONNECTING = auto()
    CONNECTED = auto()
    RECONNECTING = auto()
    FAILED = auto()


@dataclass
class DeviceInfo:
    device_id: str
    address: str


class ConnectionError(Exception):
    """Raised when a connection attempt fails."""


class ConnectionTimeout(Exception):
    """Raised when a connection attempt times out."""


class DeviceConnection:
    """Manages the lifecycle of a single device connection.

    Behaviour:
    - connect() initiates a connection attempt. If already connected,
      it is a no-op.
    - disconnect() gracefully closes the connection and stops retries.
    - If the connection attempt fails, it retries up to max_retries
      with exponential backoff.
    - If max_retries is exhausted, the component enters FAILED state
      and no further connections are attempted.
    - disconnect() during CONNECTING cancels the attempt and returns
      to DISCONNECTED.
    - A connection that stays up for at least min_uptime is considered
      stable; retry_count resets to 0.
    """

    def __init__(
        self,
        device: DeviceInfo,
        max_retries: int = 3,
        connect_timeout: float = 5.0,
        min_uptime: float = 2.0,
        base_backoff: float = 1.0,
    ):
        self.device = device
        self.max_retries = max_retries
        self.connect_timeout = connect_timeout
        self.min_uptime = min_uptime
        self.base_backoff = base_backoff

        self.state: State = State.DISCONNECTED
        self.retry_count: int = 0
        self._connect_task: asyncio.Task | None = None
        self._should_stop: bool = False
        self._uptime_task: asyncio.Task | None = None

    async def connect(self) -> None:
        """Initiate a connection to the device."""
        if self.state in (State.CONNECTED, State.CONNECTING):
            return  # idempotent
        if self.state == State.FAILED:
            raise ConnectionError("device is in FAILED state")

        self._should_stop = False
        self.state = State.CONNECTING
        self._connect_task = asyncio.create_task(self._connect_loop())

    async def disconnect(self) -> None:
        """Gracefully disconnect and stop retries."""
        self._should_stop = True
        if self._connect_task is not None:
            self._connect_task.cancel()
            self._connect_task = None
        if self._uptime_task is not None:
            self._uptime_task.cancel()
            self._uptime_task = None
        self.state = State.DISCONNECTED

    async def _connect_loop(self) -> None:
        """Internal loop: connect, retry on failure, track uptime."""
        while self.retry_count < self.max_retries and not self._should_stop:
            try:
                await self._attempt_connection()
                self.state = State.CONNECTED
                self.retry_count = 0
                self._start_uptime_timer()
                return
            except (ConnectionError, ConnectionTimeout):
                self.retry_count += 1
                if self.retry_count >= self.max_retries:
                    self.state = State.FAILED
                    return
                self.state = State.RECONNECTING
                backoff = self.base_backoff * (2 ** (self.retry_count - 1))
                jitter = random.uniform(0, backoff * 0.5)
                await asyncio.sleep(backoff + jitter)

    async def _attempt_connection(self) -> None:
        """Simulate a connection attempt with timeout."""
        try:
            await asyncio.wait_for(
                self._simulate_connect(), timeout=self.connect_timeout
            )
        except asyncio.TimeoutError:
            raise ConnectionTimeout(
                f"connection to {self.device.address} timed out"
            )

    async def _simulate_connect(self) -> None:
        """Simulate network behavior: 70% success, random latency."""
        delay = random.uniform(0.1, 1.0)
        await asyncio.sleep(delay)
        if random.random() > 0.7:
            raise ConnectionError(
                f"connection to {self.device.address} refused"
            )

    def _start_uptime_timer(self) -> None:
        """Start the min_uptime timer. After min_uptime, retry_count
        is reset (already done in _connect_loop on successful connect).
        This timer detects early disconnection."""
        async def _uptime():
            await asyncio.sleep(self.min_uptime)
            # Connection survived min_uptime — already handled by
            # retry_count=0 set in _connect_loop.

        self._uptime_task = asyncio.create_task(_uptime())
