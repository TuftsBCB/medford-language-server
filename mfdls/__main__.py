#!/usr/bin/env python3
"""__main__.py

By: Liam Strand
On: June 2022

The driver for the MEDFORD Language Server.

Usage:

pythom -m mfdls [--ws | --tcp [--port <port number>] [--host <host ip>]]

"""
import argparse
import logging
import sys
import os

# Gotta get the medford parser in the path before we can import the server
sys.path.append(os.path.join(os.getcwd(), "..", "medford-parser", "src"))
from mfdls.server import medford_server

logging.basicConfig(filename="pygls.log", level=logging.DEBUG, filemode="w")


def add_arguments(parser: argparse.ArgumentParser) -> None:
    """Configures the argument parser
    Parameters: The argument parser to configure
       Returns: None
       Effects: Adds arguments to the argument parser
    """
    parser.description = "MEDFORD Language Server"

    parser.add_argument("--tcp", action="store_true", help="Use TCP server")
    parser.add_argument("--ws", action="store_true", help="Use WebSocket server")
    parser.add_argument("--host", default="127.0.0.1", help="Bind to this address")
    parser.add_argument("--port", type=int, default=2087, help="Bind to this port")


def main() -> None:
    """The Driver"""
    parser = argparse.ArgumentParser()
    add_arguments(parser)
    args = parser.parse_args()


    if args.tcp:
        medford_server.start_tcp(args.host, args.port)
    elif args.ws:
        medford_server.start_ws(args.host, args.port)
    else:
        medford_server.start_io()


if __name__ == "__main__":
    main()
