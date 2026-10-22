"""Minimal client for manual demos and integration checks."""

from __future__ import annotations

import argparse
import socket

from .protocol import FrameDecoder, encode_frame


def request(host: str, port: int, message: bytes, timeout: float = 3.0) -> bytes:
    decoder = FrameDecoder()
    with socket.create_connection((host, port), timeout=timeout) as connection:
        connection.settimeout(timeout)
        connection.sendall(encode_frame(message))
        while True:
            chunk = connection.recv(4096)
            if not chunk:
                raise ConnectionError("server closed before a full response")
            frames = decoder.feed(chunk)
            if frames:
                return frames[0]


def main() -> None:
    parser = argparse.ArgumentParser(description="Send one framed lab request")
    parser.add_argument("message", help="PING or UPPER <ascii text>")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9000)
    args = parser.parse_args()
    print(request(args.host, args.port, args.message.encode("ascii")).decode("ascii"))


if __name__ == "__main__":
    main()
