class SessionStore:
    """Session ID store, persisted to SQLite (the Railway volume).

    Stores Claude Agent SDK session IDs keyed by (channel_id, thread_ts).
    The SDK manages conversation history via sessions, so we only track ids
    for resuming. This used to be in-memory — which meant every deploy
    replaced the process and amnesia'd every open conversation ("I don't
    have a drafted profile visible in our conversation"). Rows live on the
    same volume as the rest of the app state; a small in-process cache
    keeps the hot path off disk.
    """

    def __init__(self, ttl_seconds: int = 86400, max_cache: int = 1000):
        self._ttl_seconds = ttl_seconds
        self._max_cache = max_cache
        self._cache: dict[tuple[str, str], str] = {}

    def get_session(self, channel_id: str, thread_ts: str) -> str | None:
        """Session ID for a thread, or None if absent/expired."""
        key = (channel_id, thread_ts)
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        # Imported lazily: storage.init_db() may not have run at import time.
        from storage import get_agent_session

        session_id = get_agent_session(channel_id, thread_ts, self._ttl_seconds)
        if session_id is not None:
            self._remember(key, session_id)
        return session_id

    def set_session(self, channel_id: str, thread_ts: str, session_id: str) -> None:
        from storage import set_agent_session

        set_agent_session(channel_id, thread_ts, session_id)
        self._remember((channel_id, thread_ts), session_id)

    def _remember(self, key: tuple[str, str], session_id: str) -> None:
        self._cache[key] = session_id
        while len(self._cache) > self._max_cache:
            self._cache.pop(next(iter(self._cache)))
