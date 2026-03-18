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

# IRC format codes
IRC_BOLD = "\x02"
IRC_RESET = "\x0F"
IRC_COLOR = "\x03"

# Batch state: {batch_id: {"target": str, "lines": [str], "nick": str}}
_active_batches = {}

# Nick tracking for batches (batch id -> nick)
_batch_nick = {}


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


def batch_in_cb(data, signal, signal_data):
    """Handle incoming BATCH messages."""
    # Format: :server BATCH +id draft/multiline #channel
    # or:     :server BATCH -id
    parts = signal_data.split()
    if len(parts) < 3:
        return weechat.WEECHAT_RC_OK
    
    batch_cmd = parts[1]  # +id or -id
    
    if batch_cmd.startswith("+"):
        # Batch start
        batch_id = batch_cmd[1:]
        if len(parts) >= 5 and "draft/multiline" in signal_data:
            target = parts[4] if len(parts) > 4 else ""
            _active_batches[batch_id] = {"target": target, "lines": [], "nick": None}
    elif batch_cmd.startswith("-"):
        # Batch end - combine and print
        batch_id = batch_cmd[1:]
        if batch_id in _active_batches:
            batch = _active_batches.pop(batch_id)
            if batch["lines"] and batch["nick"]:
                combined = "\n".join(batch["lines"])
                target = batch["target"]
                nick = batch["nick"]
                
                # Find the buffer for this target
                buf = weechat.buffer_search("irc", f"server.{target}") or \
                      weechat.buffer_search("irc", f"#{target}") or \
                      weechat.current_buffer()
                
                # Colorize if enabled
                if get_config("colorize_markdown", "off") == "on":
                    combined = simple_md_to_irc(combined)
                
                # Print combined message
                weechat.prnt(buf, f"{weechat.color('chat_nick')}{nick}\t{combined}")
    
    return weechat.WEECHAT_RC_OK


def privmsg_in_cb(data, signal, signal_data):
    """Handle incoming PRIVMSG - buffer if part of active batch."""
    # Format: :nick!user@host PRIVMSG #target :message
    # Check if there's an active batch for this
    
    # Parse the message
    if not signal_data.startswith(":"):
        return weechat.WEECHAT_RC_OK
    
    space_idx = signal_data.find(" ")
    if space_idx == -1:
        return weechat.WEECHAT_RC_OK
    
    prefix = signal_data[1:space_idx]
    rest = signal_data[space_idx+1:]
    
    nick = parse_irc_prefix(prefix)
    
    # Check for batch tag in message tags (IRCv3)
    # Tags come before the command, but weechat might strip them
    # For now, check if we have ANY active batch for this nick's target
    
    # Parse target and message
    parts = rest.split(" :", 1)
    if len(parts) < 2:
        return weechat.WEECHAT_RC_OK
    
    target = parts[0].split()[0] if " " in parts[0] else parts[0]
    message = parts[1]
    
    # Check if this PRIVMSG is part of an active batch
    # We match by target and that we have a batch waiting for a nick
    for batch_id, batch in list(_active_batches.items()):
        if batch["target"] == target:
            # This PRIVMSG belongs to this batch
            if batch["nick"] is None:
                batch["nick"] = nick
            batch["lines"].append(message)
            # Don't let weechat display this message
            return weechat.WEECHAT_RC_OK_EAT
    
    return weechat.WEECHAT_RC_OK


def simple_md_to_irc(text):
    """Simple markdown to IRC colorization."""
    # Bold
    text = re.sub(r'\*\*(.*?)\*\*', IRC_BOLD + r'\1' + IRC_RESET, text)
    text = re.sub(r'__(.*?)__', IRC_BOLD + r'\1' + IRC_RESET, text)
    
    # Italic (using underline as approximation)
    text = re.sub(r'\*(.*?)\*', IRC_COLOR + "37" + r'\1' + IRC_RESET, text)
    text = re.sub(r'_(.*?)_', IRC_COLOR + "37" + r'\1' + IRC_RESET, text)
    
    # Code
    text = re.sub(r'`(.*?)`', IRC_COLOR + "14" + r'\1' + IRC_RESET, text)
    
    # Headers
    for level in range(6, 0, -1):
        hashes = '#' * level
        color = str(36 - level)  # Different colors for different levels
        text = re.sub(
            f'^{re.escape(hashes)}\\s+(.*)$',
            IRC_BOLD + hashes + IRC_RESET + ' ' + IRC_COLOR + color + r'\1' + IRC_RESET,
            text,
            flags=re.MULTILINE
        )
    
    # Bullets
    text = re.sub(r'^\* (.*)$', IRC_COLOR + "13* " + IRC_RESET + r'\1', text, flags=re.MULTILINE)
    text = re.sub(r'^(\d+)\. (.*)$', IRC_COLOR + "13" + r'\1. ' + IRC_RESET + r'\2', text, flags=re.MULTILINE)
    
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
    
    # Hook BATCH and PRIVMSG for draft/multiline support
    weechat.hook_signal("irc_in_batch", "batch_in_cb", "")
    weechat.hook_signal("irc_in_privmsg", "privmsg_in_cb", "")
    
    weechat.prnt("", f"{SCRIPT_NAME}: Loaded - draft/multiline support enabled")
    if get_config("colorize_markdown", "off") == "on":
        weechat.prnt("", f"{SCRIPT_NAME}: Markdown colorization enabled")


# Standalone test
if __name__ == "__main__" and not HAS_WEECHAT:
    print("This plugin must be loaded inside WeeChat")
    print("Install: cp markdown_irc.py ~/.weechat/python/autoload/")
    print("Load: /script load markdown_irc.py")
