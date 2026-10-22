"""A small, dependency-free framed TCP protocol lab."""

from .protocol import FrameDecoder, ProtocolError, encode_frame

__all__ = ["FrameDecoder", "ProtocolError", "encode_frame"]
