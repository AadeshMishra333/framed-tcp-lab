# Framed TCP Lab

![Checks](https://github.com/AadeshMishra333/framed-tcp-lab/actions/workflows/ci.yml/badge.svg)

A small, runnable TCP service that makes a common network programming problem visible: one application message may arrive in several socket reads, while several messages may arrive in one read. The server accepts a bounded binary frame, runs a simple command, and replies in the same format. It uses only Python's standard library.

This is an educational network service with a reproducible container build and automated checks. It is not a Marvell product, a secure public API, or a cryptographic protocol.

## Run locally

Use Python 3.12 or newer. Open two terminals from the repository root:

```text
python -m netframe.server --host 127.0.0.1 --port 9000
```

```text
python -m netframe.client PING
python -m netframe.client "UPPER hello network"
python -m netframe.client "ECHO hello network"
```

Expected replies are `PONG`, `HELLO NETWORK`, and `hello network`. Port `9000` is configurable. The default address is loopback, so the service is not exposed to the local network.

Run all checks, including real loopback socket interactions:

```text
python -m unittest discover -s tests -v
```

## Wire format

| Bytes | Meaning |
|---|---|
| 0–3 | Unsigned big-endian length of the following body, including the version byte |
| 4 | Version (`1`) |
| 5 onward | ASCII command payload |

The body length must be from 1 through 65,536 bytes. `PING` returns `PONG`; `UPPER text` returns uppercase ASCII text; `ECHO text` returns the text unchanged; unknown commands return `ERR unknown-command`. A malformed length or unsupported version causes the server to close the connection. This explicit close is the lab's protocol-error policy, not a general network standard.

### Why the decoder keeps state

TCP delivers a stream of bytes, not message boundaries. If the four-byte length header arrives as two bytes and then two bytes, the first call to `FrameDecoder.feed()` saves the first two bytes and emits no frame. It reads the length only once all four header bytes exist. It then waits until that many body bytes have arrived. It can also extract two frames from one chunk. The server reads up to 4096 bytes at a time and checks the declared length before waiting for a body, so an oversized length is rejected early.

```mermaid
flowchart LR
  C[Client bytes] --> H[4-byte length check]
  H --> B[Wait for complete body]
  B --> V[Check version]
  V --> A[Run command]
  A --> R[Encode response]
```

## Container demo

With Docker available:

```text
docker build -t framed-tcp-lab .
docker run --rm -p 127.0.0.1:9000:9000 framed-tcp-lab
python -m netframe.client PING
```

The image runs as a non-root user. The repository's GitHub Actions workflow runs the unit/integration suite, builds the image, starts a container, and sends a `PING` smoke request on pushes and pull requests. Check the [workflow runs](https://github.com/AadeshMishra333/framed-tcp-lab/actions/workflows/ci.yml) for the latest result. This local workstation does not have Docker; the documented `docker run` demo remains for Aadesh to verify on his own machine if available.

## Tests and failure behavior

- Header and body split across reads.
- Two requests on one connection, including coalesced bytes.
- Zero or oversized declared length; maximum allowed length.
- Unknown protocol version.
- Client disconnect halfway through a frame; server remains available.
- Unknown command returns an explicit error.
- `ECHO` round trip through a real loopback socket.

The server applies a three-second socket timeout, closes malformed connections, and logs the reason without logging request bodies. It does not authenticate clients, negotiate TLS, rate-limit peers, or impose a global connection/thread cap. Keep it on loopback or a controlled test network. Do not expose it directly to the public Internet.
