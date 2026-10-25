"""Runnable TCP server for the framed protocol lab."""

from __future__ import annotations

import argparse
import logging
import socket
import socketserver

from .protocol import FrameDecoder, ProtocolError, encode_frame

LOG = logging.getLogger(__name__)
READ_SIZE = 4096
CLIENT_TIMEOUT_SECONDS = 3.0


def respond(payload: bytes) -> bytes:
    """Handle two intentionally small commands without side effects."""
    if payload == b"PING":
        return b"PONG"
    if payload.startswith(b"UPPER "):
        try:
            return payload[6:].decode("ascii").upper().encode("ascii")
        except UnicodeDecodeError:
            return b"ERR ascii-only"
    if payload.startswith(b"ECHO "):
        return payload[len(b"ECHO "):]
    return b"ERR unknown-command"


class RequestHandler(socketserver.BaseRequestHandler):
    def handle(self) -> None:
        connection: socket.socket = self.request
        connection.settimeout(CLIENT_TIMEOUT_SECONDS)
        decoder = FrameDecoder()
        while True:
            try:
                chunk = connection.recv(READ_SIZE)
                if not chunk:
                    if decoder.has_incomplete_frame:
                        LOG.info("client disconnected during a frame")
                    return
                for payload in decoder.feed(chunk):
                    connection.sendall(encode_frame(respond(payload)))
            except (ProtocolError, socket.timeout) as exc:
                LOG.info("closing client connection: %s", exc)
                return
            except (BrokenPipeError, ConnectionResetError):
                return


class LabServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True
    block_on_close = False


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the framed TCP lab server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9000)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    with LabServer((args.host, args.port), RequestHandler) as server:
        LOG.info("listening on %s:%s", *server.server_address)
        try:
            server.serve_forever(poll_interval=0.1)
        except KeyboardInterrupt:
            LOG.info("stopping")


if __name__ == "__main__":
    main()
