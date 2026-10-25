import socket
import threading
import unittest

from netframe.client import request
from netframe.protocol import MAX_BODY_SIZE, FrameDecoder, encode_frame
from netframe.server import LabServer, RequestHandler


class ServerIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = LabServer(("127.0.0.1", 0), RequestHandler)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    def test_echo_round_trip(self):
        self.assertEqual(
            request("127.0.0.1", self.port, b"ECHO hello"),
            b"hello",
        )

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def test_ping_and_upper(self):
        self.assertEqual(request("127.0.0.1", self.port, b"PING"), b"PONG")
        self.assertEqual(
            request("127.0.0.1", self.port, b"UPPER hello"), b"HELLO"
        )

    def test_fragmented_request_and_two_requests_on_one_connection(self):
        with socket.create_connection(("127.0.0.1", self.port), timeout=2) as peer:
            peer.settimeout(2)
            first = encode_frame(b"PING")
            peer.sendall(first[:2])
            peer.sendall(first[2:] + encode_frame(b"UPPER network"))
            decoder = FrameDecoder()
            responses = []
            while len(responses) < 2:
                responses.extend(decoder.feed(peer.recv(4096)))
            self.assertEqual(responses, [b"PONG", b"NETWORK"])

    def test_oversized_header_closes_connection(self):
        with socket.create_connection(("127.0.0.1", self.port), timeout=2) as peer:
            peer.settimeout(2)
            peer.sendall((MAX_BODY_SIZE + 1).to_bytes(4, "big"))
            self.assertEqual(peer.recv(1), b"")

    def test_disconnect_halfway_through_frame_does_not_stop_server(self):
        with socket.create_connection(("127.0.0.1", self.port), timeout=2) as peer:
            peer.sendall(encode_frame(b"PING")[:3])
        self.assertEqual(request("127.0.0.1", self.port, b"PING"), b"PONG")

    def test_unknown_command_is_explicit(self):
        self.assertEqual(
            request("127.0.0.1", self.port, b"DELETE everything"),
            b"ERR unknown-command",
        )


if __name__ == "__main__":
    unittest.main()
