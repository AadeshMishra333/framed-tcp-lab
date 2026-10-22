"""Incremental decoder for the lab's length-prefixed wire format.

Wire format: 4-byte unsigned big-endian body length, 1-byte version, then
ASCII payload. The length includes the version byte. TCP is a byte stream,
so callers may feed arbitrarily split or combined chunks.
"""

from __future__ import annotations

MAX_BODY_SIZE = 65_536
VERSION = 1


class ProtocolError(ValueError):
    """The peer sent a frame this implementation cannot accept."""


def encode_frame(payload: bytes, version: int = VERSION) -> bytes:
    if not isinstance(payload, bytes):
        raise TypeError("payload must be bytes")
    if not 0 <= version <= 255:
        raise ValueError("version must fit in one byte")
    body = bytes((version,)) + payload
    if len(body) > MAX_BODY_SIZE:
        raise ValueError("frame body exceeds limit")
    return len(body).to_bytes(4, "big") + body


class FrameDecoder:
    """Collect bytes until complete frames are available.

    At most one incomplete frame is retained between calls. A caller should
    feed bounded chunks (the server uses 4096 bytes) and close a connection
    after ProtocolError.
    """

    def __init__(self) -> None:
        self._buffer = bytearray()
        self._expected_body: int | None = None

    @property
    def has_incomplete_frame(self) -> bool:
        return bool(self._buffer) or self._expected_body is not None

    def feed(self, chunk: bytes) -> list[bytes]:
        if not isinstance(chunk, bytes):
            raise TypeError("chunk must be bytes")
        self._buffer.extend(chunk)
        frames: list[bytes] = []

        while True:
            if self._expected_body is None:
                if len(self._buffer) < 4:
                    break
                self._expected_body = int.from_bytes(self._buffer[:4], "big")
                del self._buffer[:4]
                if not 1 <= self._expected_body <= MAX_BODY_SIZE:
                    raise ProtocolError("invalid frame length")

            if len(self._buffer) < self._expected_body:
                break

            body = bytes(self._buffer[: self._expected_body])
            del self._buffer[: self._expected_body]
            self._expected_body = None
            if body[0] != VERSION:
                raise ProtocolError("unsupported protocol version")
            frames.append(body[1:])

        return frames
