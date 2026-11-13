"""Shared helper for the mutation runners: captured subprocess output as text.

subprocess.TimeoutExpired carries what the child wrote before it was killed
as bytes, even under text=True, or None when it wrote nothing. Both runners
report that output, so both need the same conversion.
"""


def as_text(stream: bytes | str | None) -> str:
    if stream is None:
        return ""
    return stream.decode(errors="replace") if isinstance(stream, bytes) else stream
