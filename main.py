#!/usr/bin/env python3
"""Ashen Depths — entry point."""
import curses
import sys
from ashen_depths.engine import GameEngine


def main():
    try:
        curses.wrapper(_run)
    except KeyboardInterrupt:
        pass


def _run(stdscr):
    engine = GameEngine(stdscr)
    engine.run()


if __name__ == '__main__':
    main()
