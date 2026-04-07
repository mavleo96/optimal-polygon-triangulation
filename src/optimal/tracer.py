class _Tracer:
    """Optional trace recorder; pass as ``_tracer=`` to ``_dp`` to enable."""

    __slots__ = ("events", "_stack", "splits_cache", "costs_cache")

    def __init__(self) -> None:
        self.events: list[dict] = []
        self._stack: list[tuple[int, int]] = []
        self.splits_cache: list[list[float | None]] = []
        self.costs_cache: list[list[float | None]] = []

    def push(self, start: int, end: int) -> None:
        self._stack.append((start, end))

    def pop(self) -> None:
        self._stack.pop()

    def record(self, event: str, start: int, end: int, **kw) -> None:
        self.events.append(
            {"event": event, "start": start, "end": end, "stack": list(self._stack), **kw}
        )
