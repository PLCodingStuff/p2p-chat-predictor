# Peer-To-Peer Chat Application

[![Build Status](https://github.com/PLCodingStuff/PredictorCompression/actions/workflows/python-app.yml/badge.svg)](https://github.com/PLCodingStuff/PredictorCompression/actions/workflows/python-app.yml)
[![License: MIT](https://img.shields.io/github/license/PLCodingStuff/PredictorCompression)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](pyproject.toml)

## Table of Contents

- [Overview](#overview)
- [Demo](#demo)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
  - [Project Structure](#project-structure)
- [Installation](#installation)
- [Usage](#usage)
  - [Configuration Files](#configuration-files)
- [Testing and Benchmarking](#testing-and-benchmarking)
- [License](#license)

## Overview

This project is a Peer-To-Peer (P2P) chat application implemented using Python. It features a client-server architecture with data compression and decompression functionalities. The application uses the observer pattern to manage the state of the connection between the client and server, and supports basic message exchange over a network.

The compression is done using the Predictor algorithm (it can be referred from [here](https://datatracker.ietf.org/doc/rfc1978/) and [here](https://dl.acm.org/doi/10.1145/42005.42031)).

The project is designed for a course named "Software Design and Development" and demonstrates principles of software design, including network communication, data compression, and design patterns.

Python 3.11 was used for the implementation.

## Demo

**Compress / decompress round-trip:**

```console
$ py p2ppred.py compress "The quick brown fox jumps over the lazy dog"
0023546865717569636b62726f776e666f786a756d70736f7665727468656c617a79646f67104110422100

$ py p2ppred.py decompress 0023546865717569636b62726f776e666f786a756d70736f7665727468656c617a79646f67104110422100
The quick brown fox jumps over the lazy dog
```

**Two-node chat**, one `start` process per terminal (server/client configs swapped between them — see [Configuration Files](#configuration-files)):

```console
# Terminal 1 — node 1
$ py p2ppred.py start node1config.json node2config.json
Starting chat...
> Hey, can you see this?
Yep, loud and clear!
> Great, chat away!
What's on your mind?
> quit
Terminating Process
```

```console
# Terminal 2 — node 2
$ py p2ppred.py start node2config.json node1config.json
Starting chat...
Hey, can you see this?
> Yep, loud and clear!
Great, chat away!
> What's on your mind?
Peer has left the chat.
> quit
Terminating Process
```

Each side's typed lines are compressed and sent over the wire, decompressed, and displayed on the other. Node 1 quits first, so node 2 sees `Peer has left the chat.` before quitting itself — node 1 doesn't get that message about its own departure.

## Features

- **Client-Server Communication**: Each running node opens both a server socket (to accept the peer's incoming connection) and a client socket (to connect out to the peer), driven through a small length-prefixed wire protocol with a `HELLO`/`ACK` handshake.
- **Data Compression**: Uses a custom Predictor-based compression scheme to minimize the size of transmitted messages.
- **Observer Pattern**: The server and client sides are both `Observer`s of a shared `Connection`, so either side setting the connection state (e.g. on disconnect) notifies the other.
- **Network Handling**: Dedicated error types for handshake failures, connection loss, and accept/connect timeouts.
- **CLI**: A `p2ppred` command-line tool for validating configs, compressing/decompressing text directly, and starting a chat node.

## Tech Stack

- **Language**: Python 3.11+
- **Networking**: raw TCP sockets (`socket` from the standard library), a custom length-prefixed framing protocol, and a `HELLO`/`ACK` handshake
- **Compression**: a from-scratch implementation of the Predictor algorithm ([RFC 1978](https://datatracker.ietf.org/doc/rfc1978/)), using [`bitarray`](https://github.com/ilanschnell/bitarray) for bit-level packing
- **Tooling**: [`uv`](https://docs.astral.sh/uv/) for dependency management, [`pytest`](https://docs.pytest.org/) for testing, [`ruff`](https://docs.astral.sh/ruff/) for linting
- **CI**: GitHub Actions (`.github/workflows/python-app.yml`)

## Architecture

- **Node** (`src/network/node.py`) orchestrates a chat session: it builds a server + client pair, attaches both as `Observer`s to a shared `Connection`, and runs the server in a background thread while the client runs on the calling thread.
- **Server & Client** (`src/network/server.py`, `src/network/client.py`) each own their socket lifecycle — bind/listen/accept with retries on the server side, connect with retries on the client side — and, once connected, run a handshake before entering their receive/send loop.
- **Wire protocol** (`src/network_components/`): a small length-prefixed framing format (`HELLO`/`ACK`/`MSG`/`QUIT`) sits on top of raw TCP, plus a symmetric `HELLO`/`ACK` handshake run before either side exchanges chat messages.
- **Compression** (`src/business/compression/`): outgoing messages are passed through the custom Predictor algorithm before being framed and sent; incoming messages are decompressed the same way before being displayed.
- **Observer pattern** (`src/interfaces/`): the server and client are both observers of one shared `Connection`. Either side setting the connection state (e.g. a peer disconnecting) notifies the other, so both loops stop together.
- **Config loading** (`src/config/config.py`): loads a node's JSON config (`port` required; `timeout`, `retries`, `address` default if absent) and builds the corresponding `ServerSocketConfig`/`ClientSocketConfig`.

### Project Structure

```
p2ppred.py                                  # CLI entry point
benchmark.py                             # compression benchmark runner
src/
  cli/commands.py                        # p2ppred argparse CLI (validate/compress/decompress/start)
  config/config.py                       # JSON config loading + ServerSocketConfig/ClientSocketConfig construction
  network/
    node.py                              # Node: orchestrates server + client over a shared Connection
    server.py                            # ServerSocketConfig, ServerSocket, PeerClientSocketManager, ServerManager
    client.py                            # ClientSocketConfig, ClientSocket, ClientManager
  network_components/
    connection.py                        # Connection (Observable)
    framing.py                           # wire frame packing/sending/receiving, MessageType
    handshake.py                         # HELLO/ACK handshake
  business/
    compression/compression.py           # Compression (Predictor algorithm)
    compression/decompression.py         # Decompression
    messages/                            # SendMessageProcessor/ReceiveMessageProcessor, CLI I/O adapters
  interfaces/
    observer.py                          # Observer
    observable.py                        # Observable
  errors/                                # client/server/protocol error types
tests/                                   # pytest suite, mirrors src/ one file per module
```

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/PLCodingStuff/PredictorCompression.git
   cd PredictorCompression
   ```

2. **Install dependencies:**
   This project uses [`uv`](https://docs.astral.sh/uv/) for dependency management (see `pyproject.toml`/`uv.lock`). Install `uv`, then:
   ```bash
   uv sync
   ```

## Usage

The CLI entry point is `p2ppred.py`, which dispatches to the `p2ppred` subcommands:

```bash
py p2ppred.py validate <config.json>              # validate a config file
py p2ppred.py compress "some text"                # compress text, prints hex
py p2ppred.py decompress <hex>                     # decompress a hex string back to text
py p2ppred.py start <server_config.json> <client_config.json>   # start a two-way chat node
```

(Prefix with `uv run` instead of `py` if you're not in an activated environment, e.g. `uv run python p2ppred.py validate config.json`.)

### Configuration Files

Each node needs **two** JSON config files: one for its server socket, one for its client socket (which dials the peer). Both share the same shape:

```json
{
    "address": "127.0.0.1",
    "port": 5000,
    "timeout": 5.0,
    "retries": 3
}
```

`address`, `timeout`, and `retries` are optional and default to `127.0.0.1`, `5.0`, and `3` respectively. `port` is required — for the **server** config it's this node's own listening port; for the **client** config it's the *peer's* port (the client config connects out to it). 

To run two local nodes against each other you need four files in total (a server + client config per node) — or just two files used in swapped order, since each side's own config doubles as its peer's dial target. `node1config.json` (port `5000`) and `node2config.json` (port `6000`) at the repo root are a ready-to-run example pair:

```bash
py p2ppred.py start node1config.json node2config.json   # node 1: listens on 5000, dials 6000
py p2ppred.py start node2config.json node1config.json   # node 2: listens on 6000, dials 5000
```

## Testing and Benchmarking

```bash
uv run pytest                                   # run the test suite
py benchmark.py benchmark                       # run compression benchmarks against benchmarks/*.txt
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
