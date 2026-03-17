#!/usr/bin/env python3
"""
Standalone test runner for markdown-to-IRC converter.
Imports from markdown_irc.py which handles weechat import conditionally.
"""

import sys
from markdown_irc import convert_markdown, HAS_MARKDOWN

def irc_to_ansi(text):
    """Convert IRC format codes to ANSI for terminal display."""
    # Map IRC colors to ANSI
    color_map = {
        "c34": "\033[34m",  # blue
        "c33": "\033[33m",  # yellow
        "c32": "\033[32m",  # green
        "c31": "\033[31m",  # red
        "c30": "\033[90m",  # bright black
        "c29": "\033[35m",  # magenta
    }
    
    # IRC color codes \x03NN
    text = text.replace("\x0313", "\033[35m")  # magenta (bullets)
    text = text.replace("\x0314", "\033[90m")  # gray (code)
    
    # Heading colors
    for irc_code, ansi in color_map.items():
        text = text.replace(f"\x03{irc_code}", ansi)
    
    # Format codes
    text = text.replace("\x03b", "\033[1m")    # bold
    text = text.replace("\x0375", "\033[3m")   # italic
    text = text.replace("\x03o", "\033[0m")    # reset
    text = text.replace("\x02", "\033[1m")     # alt bold
    text = text.replace("\x0F", "\033[0m")     # alt reset
    
    return text


def main():
    if len(sys.argv) > 1:
        text = sys.argv[1]
    else:
        text = sys.stdin.read()
    
    result = convert_markdown(text)
    print(irc_to_ansi(result), end="")


if __name__ == "__main__":
    main()
