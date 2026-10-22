import unittest

from netframe.protocol import (
    MAX_BODY_SIZE,
    FrameDecoder,
    ProtocolError,
    encode_frame,
)


class FrameDecoderTests(unittest.TestCase):
    def test_header_and_body_can_arrive_in_pieces(self):
        decoder = FrameDecoder()
        frame = encode_frame(b"PING")
        self.assertEqual(decoder.feed(frame[:2]), [])
        self.assertTrue(decoder.has_incomplete_frame)
        self.assertEqual(decoder.feed(frame[2:5]), [])
        self.assertEqual(decoder.feed(frame[5:]), [b"PING"])
        self.assertFalse(decoder.has_incomplete_frame)

    def test_two_frames_can_arrive_in_one_chunk(self):
        decoder = FrameDecoder()
        self.assertEqual(
            decoder.feed(encode_frame(b"PING") + encode_frame(b"UPPER hi")),
            [b"PING", b"UPPER hi"],
        )

    def test_oversized_length_rejected_before_body_arrives(self):
        decoder = FrameDecoder()
        header = (MAX_BODY_SIZE + 1).to_bytes(4, "big")
        with self.assertRaisesRegex(ProtocolError, "length"):
            decoder.feed(header)

    def test_zero_length_rejected(self):
        with self.assertRaises(ProtocolError):
            FrameDecoder().feed(b"\x00\x00\x00\x00")

    def test_unknown_version_rejected(self):
        with self.assertRaisesRegex(ProtocolError, "version"):
            FrameDecoder().feed(encode_frame(b"PING", version=2))

    def test_max_body_and_one_byte_over(self):
        payload = b"x" * (MAX_BODY_SIZE - 1)
        self.assertEqual(FrameDecoder().feed(encode_frame(payload)), [payload])
        with self.assertRaisesRegex(ValueError, "limit"):
            encode_frame(payload + b"x")


if __name__ == "__main__":
    unittest.main()
