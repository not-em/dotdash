#!/usr/bin/env python3
"""
main.py — CLI for the Morse code tool

Usage:
  python main.py encode "Hello World"
  python main.py encode "Hello World" --save output.mp3
  python main.py encode "Hello World" --wpm 15 --save output.mp3
  python main.py decode ".... . .-.. .-.. ---"
"""

import argparse
import sys
from morse import encode, decode, generate_audio


def cmd_encode(args):
    text = args.text
    morse = encode(text)
    print(f"\n  Text:  {text}")
    print(f"  Morse: {morse}\n")

    if args.save:
        print(f"  Generating audio at {args.wpm} WPM...")
        mp3_bytes = generate_audio(text, wpm=args.wpm)
        with open(args.save, "wb") as f:
            f.write(mp3_bytes)
        print(f"  Saved → {args.save}\n")


def cmd_decode(args):
    text = decode(args.morse)
    print(f"\n  Morse: {args.morse}")
    print(f"  Text:  {text}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Morse Code Encoder/Decoder",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py encode "SOS"
  python main.py encode "Hello World" --save hello.mp3
  python main.py encode "Hello World" --wpm 15 --save hello.mp3
  python main.py decode "... --- ..."
        """,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # encode
    enc = sub.add_parser("encode", help="Encode text to morse code")
    enc.add_argument("text", help="Text to encode")
    enc.add_argument("--save", metavar="FILE", help="Save audio as MP3")
    enc.add_argument(
        "--wpm",
        type=int,
        default=20,
        metavar="N",
        help="Words per minute for audio (default: 20)",
    )

    # decode
    dec = sub.add_parser("decode", help="Decode morse code to text")
    dec.add_argument(
        "morse", help="Morse code to decode (use dots and dashes, / for word gaps)"
    )

    args = parser.parse_args()

    if args.command == "encode":
        cmd_encode(args)
    elif args.command == "decode":
        cmd_decode(args)


if __name__ == "__main__":
    main()
