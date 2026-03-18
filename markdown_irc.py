# -*- coding: utf-8 -*-
"""
WeeChat plugin for draft/multiline support and optional markdown colorization.

- Combines BATCH'd draft/multiline messages into single display lines
- Optionally colorizes markdown formatting
"""

import re

try:
    import weechat
    HAS_WEECHAT = True
except ImportError:
    HAS_WEECHAT = False
    weechat = None

SCRIPT_NAME = "markdown_irc"
SCRIPT_AUTHOR = "Chevette <chevette@irc>"
SCRIPT_VERSION = "0.3"
SCRIPT_LICENSE = "MIT"
SCRIPT_DESC = "Combine draft/multiline messages and optionally colorize markdown"

# Batch state: {batch_id: {"target": str, "lines": [str], "nick": str, "closed": bool}}
_active_batches = {}


def get_config(option, default=""):
    if HAS_WEECHAT and weechat:
        return weechat.config_get_plugin(option)
    return default


def parse_irc_prefix(prefix):
    """Parse IRC prefix into nick!user@host."""
    nick = prefix
    if "!" in prefix:
        nick = prefix.split("!")[0]
    return nick


def strip_ircv3_tags(message):
    """Strip IRCv3 tags from message. Returns (tags_dict, message_without_tags)."""
    tags = {}
    if message.startswith("@"):
        # Tags end at first space
        space_idx = message.find(" ")
        if space_idx == -1:
            return tags, message
        tags_str = message[1:space_idx]
        message = message[space_idx + 1:]
        # Parse tags: tag1=val1;tag2=val2
        for tag in tags_str.split(";"):
            if "=" in tag:
                key, val = tag.split("=", 1)
                tags[key] = val
            else:
                tags[tag] = ""
    return tags, message


def batch_in_cb(data, signal, signal_data):
    """Handle incoming BATCH messages."""
    # Strip IRCv3 tags if present
    _, signal_data = strip_ircv3_tags(signal_data)

    # Format: :server BATCH +id draft/multiline #channel
    # or:     :server BATCH -id
    parts = signal_data.split()
    if len(parts) < 3:
        return weechat.WEECHAT_RC_OK

    # parts: [":server", "BATCH", "+id", "draft/multiline", ":#channel"]
    # or:    [":server", "BATCH", ":-id"]
    if parts[1] != "BATCH":
        return weechat.WEECHAT_RC_OK

    batch_cmd = parts[2].lstrip(":")  # +id or -id (strip : if trailing param)

    if batch_cmd.startswith("+"):
        # Batch start
        batch_id = batch_cmd[1:]
        if "draft/multiline" in signal_data:
            target = parts[4].lstrip(":") if len(parts) > 4 else ""
            _active_batches[batch_id] = {"target": target, "lines": [], "nick": None, "closed": False}
    elif batch_cmd.startswith("-"):
        # Batch end - schedule processing after a short delay to let PRIVMSG arrive
        batch_id = batch_cmd[1:]
        if batch_id in _active_batches:
            # Mark batch as closed - will be processed by timer
            _active_batches[batch_id]["closed"] = True
            # Schedule processing after 100ms
            weechat.hook_timer(100, 0, 1, "process_closed_batch_cb", batch_id)

    return weechat.WEECHAT_RC_OK


def process_closed_batch_cb(data, remaining_calls):
    """Process a closed batch after delay."""
    batch_id = data
    if batch_id not in _active_batches:
        return weechat.WEECHAT_RC_OK

    batch = _active_batches.get(batch_id)
    if not batch or not batch.get("closed"):
        return weechat.WEECHAT_RC_OK

    # Pop and process
    _active_batches.pop(batch_id, None)

    if batch["lines"] and batch["nick"]:
        combined = "\n".join(batch["lines"])
        target = batch["target"]
        nick = batch["nick"]

        # Find the buffer for this target
        buf = weechat.buffer_search("irc", f"sidero.{target}") or \
              weechat.buffer_search("irc", target) or \
              weechat.current_buffer()

        # Colorize if enabled
        colorize = get_config("colorize_markdown", "off")
        if colorize == "on":
            combined = simple_md_to_irc(combined)

        # Print combined message
        weechat.prnt(buf, f"{weechat.color('chat_nick')}{nick}\t{combined}")

    return weechat.WEECHAT_RC_OK


def privmsg_in_cb(data, signal, signal_data):
    """Handle incoming PRIVMSG - buffer if part of active batch."""
    # Strip IRCv3 tags and extract batch tag if present
    tags, signal_data = strip_ircv3_tags(signal_data)

    # Format: :nick!user@host PRIVMSG #target :message
    # Parse the message
    if not signal_data.startswith(":"):
        return weechat.WEECHAT_RC_OK

    space_idx = signal_data.find(" ")
    if space_idx == -1:
        return weechat.WEECHAT_RC_OK

    prefix = signal_data[1:space_idx]
    rest = signal_data[space_idx+1:]

    nick = parse_irc_prefix(prefix)

    # Parse target and message
    parts = rest.split(" :", 1)
    if len(parts) < 2:
        return weechat.WEECHAT_RC_OK

    target = parts[0].split()[0] if " " in parts[0] else parts[0]
    message = parts[1]

    # Check if this PRIVMSG is part of an active batch using the batch tag
    batch_id = tags.get("batch")
    if batch_id and batch_id in _active_batches:
        batch = _active_batches[batch_id]
        if batch["nick"] is None:
            batch["nick"] = nick
        batch["lines"].append(message)
        # Don't let weechat display this message
        return weechat.WEECHAT_RC_OK_EAT

    return weechat.WEECHAT_RC_OK


def simple_md_to_irc(text):
    """Simple markdown to WeeChat colorization using weechat.color()."""
    if not weechat:
        return text

    # Bold: **text** or __text__
    bold_start = weechat.color("bold")
    bold_end = weechat.color("-bold")
    text = re.sub(r'\*\*(.*?)\*\*', bold_start + r'\1' + bold_end, text)
    text = re.sub(r'__(.*?)__', bold_start + r'\1' + bold_end, text)

    # Italic: *text* or _text_
    italic_start = weechat.color("italic")
    italic_end = weechat.color("-italic")
    text = re.sub(r'\*(.*?)\*', italic_start + r'\1' + italic_end, text)
    text = re.sub(r'_(.*?)_', italic_start + r'\1' + italic_end, text)

    # Code: `text` (cyan)
    code_start = weechat.color("cyan")
    code_end = weechat.color("reset")
    text = re.sub(r'`(.*?)`', code_start + r'\1' + code_end, text)

    # Headers: # through ######
    # IRC color codes: h1=47, h2=46, h3=45, h4=44, h5=43, h6=42
    header_colors = ["47", "46", "45", "44", "43", "42"]  # level 1-6
    hash_color = weechat.color("49")  # Color for # characters
    reset = weechat.color("reset")
    for level in range(6, 0, -1):
        hashes = '#' * level
        color = header_colors[level - 1]
        header_color = weechat.color(color)
        text = re.sub(
            f'^{re.escape(hashes)}\\s+(.*)$',
            hash_color + hashes + reset + ' ' + header_color + r'\1' + reset,
            text,
            flags=re.MULTILINE
        )

    # Bullets: * or -
    bullet_color = weechat.color("magenta")
    reset = weechat.color("reset")
    text = re.sub(r'^[\*\-] (.*)$', bullet_color + '* ' + reset + r'\1', text, flags=re.MULTILINE)
    text = re.sub(r'^(\d+)\. (.*)$', bullet_color + r'\1. ' + reset + r'\2', text, flags=re.MULTILINE)

    return text


def init_config():
    if HAS_WEECHAT and weechat:
        settings = {
            "colorize_markdown": "off",  # Enable markdown colorization
        }
        for option, default_value in settings.items():
            if not weechat.config_is_set_plugin(option):
                weechat.config_set_plugin(option, default_value)


# WeeChat plugin initialization
if HAS_WEECHAT and __name__ == "__main__":
    weechat.register(SCRIPT_NAME, SCRIPT_AUTHOR, SCRIPT_VERSION, SCRIPT_LICENSE, SCRIPT_DESC, "", "")
    init_config()

    # Hook BATCH and PRIVMSG - signal includes server name like "server,irc_in_PRIVMSG"
    weechat.hook_signal("*,irc_in_batch", "batch_in_cb", "")
    weechat.hook_signal("*,irc_in_privmsg", "privmsg_in_cb", "")

    weechat.prnt("", f"{SCRIPT_NAME}: Loaded - draft/multiline support enabled")
    if get_config("colorize_markdown", "off") == "on":
        weechat.prnt("", f"{SCRIPT_NAME}: Markdown colorization enabled")


# Standalone test
if __name__ == "__main__" and not HAS_WEECHAT:
    print("This plugin must be loaded inside WeeChat")
    print("Install: cp markdown_irc.py ~/.weechat/python/autoload/")
    print("Load: /script load markdown_irc.py")
