# -*- coding: utf-8 -*-
"""
WeeChat Markdown to IRC converter plugin.
Converts markdown formatting to IRC color/formatting codes.
Can be used standalone or as a WeeChat plugin.
"""

import re

# Try to import weechat (only available when running inside WeeChat)
try:
    import weechat
    HAS_WEECHAT = True
except ImportError:
    HAS_WEECHAT = False
    weechat = None

# Plugin info
SCRIPT_NAME = "markdown_irc"
SCRIPT_AUTHOR = "Chevette <chevette@irc>"
SCRIPT_VERSION = "0.2"
SCRIPT_LICENSE = "MIT"
SCRIPT_DESC = "Convert markdown formatting to IRC codes on message send"

# IRC format codes (using Ctrl-C format: \x03 + code)
IRC_BOLD = "\x03b"
IRC_UNDERLINE = "\x03u"
IRC_ITALIC = "\x0375"
IRC_RESET = "\x03o"

# IRC color codes for markdown headings (levels 1-6)
HEADING_COLORS = ["c34", "c33", "c32", "c31", "c30", "c29"]

# Additional color codes
IRC_BULLET_COLOR = "\x0313"  # Magenta for bullets and numbers
IRC_FENCE_COLOR = "\x0314"   # Gray for code blocks
IRC_CODE_COLOR = "\x0314"    # Gray for inline code

# Alternative format codes (single control chars)
ALT_BOLD = "\x02"
ALT_UNDERLINE = "\x1F"
ALT_RESET = "\x0F"

# Try to import markdown-it-py
try:
    from markdown_it import MarkdownIt
    from markdown_it.tree import SyntaxTreeNode
    HAS_MARKDOWN = True
except ImportError:
    HAS_MARKDOWN = False

# Global counter for ordered lists
_list_counters = {}


def get_config(option, default=""):
    """Get config value, works with or without WeeChat."""
    if HAS_WEECHAT and weechat:
        return weechat.config_get_plugin(option)
    return default


def md_to_irc_converter(node, options=None, env=None, list_id=None):
    """
    Custom renderer for markdown-it that outputs IRC formatting codes.
    Uses SyntaxTreeNode which collapses paired tokens into single nodes.
    """
    global _list_counters
    result = []

    if node.type == "root":
        if hasattr(node, 'children') and node.children:
            for child in node.children:
                result.append(md_to_irc_converter(child, options, env, list_id=list_id))
    elif node.type == "paragraph":
        if hasattr(node, 'children') and node.children:
            for child in node.children:
                result.append(md_to_irc_converter(child, options, env, list_id=list_id))
        result.append("\n")
    elif node.type == "text":
        result.append(node.content if hasattr(node, 'content') else '')
    elif node.type == "heading":
        level = node.tag if hasattr(node, 'tag') else "h1"
        level_num = int(level[1]) - 1
        hashes = '#' * (level_num + 1)
        result.append(IRC_BOLD + hashes + IRC_RESET + " ")
        if 0 <= level_num < len(HEADING_COLORS):
            result.append("\x03" + HEADING_COLORS[level_num])
        if hasattr(node, 'children') and node.children:
            for child in node.children:
                result.append(md_to_irc_converter(child, options, env, list_id=list_id))
        result.append(IRC_RESET + "\n\n")
    elif node.type == "strong":
        use_alt = get_config("use_alt_format", "off") == "on"
        result.append(ALT_BOLD if use_alt else IRC_BOLD)
        if hasattr(node, 'children') and node.children:
            for child in node.children:
                result.append(md_to_irc_converter(child, options, env, list_id=list_id))
        result.append(ALT_RESET if use_alt else IRC_RESET)
    elif node.type == "em":
        use_alt = get_config("use_alt_format", "off") == "on"
        result.append(ALT_BOLD if use_alt else IRC_ITALIC)
        if hasattr(node, 'children') and node.children:
            for child in node.children:
                result.append(md_to_irc_converter(child, options, env, list_id=list_id))
        result.append(ALT_RESET if use_alt else IRC_RESET)
    elif node.type == "inline":
        if hasattr(node, 'children') and node.children:
            for child in node.children:
                result.append(md_to_irc_converter(child, options, env, list_id=list_id))
    elif node.type == "softbreak":
        result.append("\n")
    elif node.type == "hardbreak":
        result.append("\n")
    elif node.type == "bullet_list":
        if hasattr(node, 'children') and node.children:
            for child in node.children:
                result.append(md_to_irc_converter(child, options, env, list_id=list_id))
        result.append("\n")
    elif node.type == "ordered_list":
        current_list_id = id(node)
        _list_counters[current_list_id] = 0
        if hasattr(node, 'children') and node.children:
            for child in node.children:
                result.append(md_to_irc_converter(child, options, env, list_id=current_list_id))
        result.append("\n")
    elif node.type == "list_item":
        if hasattr(node, 'children') and node.children:
            parent = node.parent if hasattr(node, 'parent') else None
            if parent and parent.type == "ordered_list" and list_id is not None:
                _list_counters[list_id] = _list_counters.get(list_id, 0) + 1
                num = _list_counters[list_id]
                result.append(IRC_BULLET_COLOR + f"{num}. " + IRC_RESET)
            else:
                result.append(IRC_BULLET_COLOR + "* " + IRC_RESET)
            for child in node.children:
                result.append(md_to_irc_converter(child, options, env, list_id=list_id))
    elif node.type == "fence":
        result.append(IRC_FENCE_COLOR + "```\n")
        if hasattr(node, 'content') and node.content:
            result.append(node.content)
        if not (hasattr(node, 'content') and node.content.endswith('\n')):
            result.append("\n")
        result.append(IRC_FENCE_COLOR + "```" + IRC_RESET + "\n")
    elif node.type == "code_block":
        result.append(IRC_FENCE_COLOR)
        if hasattr(node, 'content') and node.content:
            result.append(node.content)
        result.append(IRC_RESET + "\n")
    elif node.type == "code_inline":
        result.append(IRC_CODE_COLOR)
        if hasattr(node, 'content'):
            result.append(node.content)
        result.append(IRC_RESET)

    return "".join(result)


def simple_md_to_irc(text):
    """Simple regex-based markdown to IRC converter (fallback if markdown-it not available)."""
    for level in range(6, 0, -1):
        hashes = '#' * level
        color_code = HEADING_COLORS[level - 1]
        text = re.sub(
            r'^(' + hashes + r')\s+(.*)$',
            lambda m: IRC_BOLD + m.group(1) + IRC_RESET + ' ' + '\x03' + color_code + m.group(2) + IRC_RESET,
            text,
            flags=re.MULTILINE
        )

    text = re.sub(r'\*\*(.*?)\*\*', IRC_BOLD + r'\1' + IRC_RESET, text)
    text = re.sub(r'__(.*?)__', IRC_BOLD + r'\1' + IRC_RESET, text)
    text = re.sub(r'\*(.*?)\*', IRC_ITALIC + r'\1' + IRC_RESET, text)
    text = re.sub(r'_(.*?)_', IRC_ITALIC + r'\1' + IRC_RESET, text)
    text = re.sub(r'`(.*?)`', IRC_CODE_COLOR + r'\1' + IRC_RESET, text)
    text = re.sub(r'^\*\s+(.*)$',
                  lambda m: IRC_BULLET_COLOR + "* " + IRC_RESET + m.group(1),
                  text, flags=re.MULTILINE)
    text = re.sub(r'^(\d+)\.\s+(.*)$',
                  lambda m: IRC_BULLET_COLOR + m.group(1) + ". " + IRC_RESET + m.group(2),
                  text, flags=re.MULTILINE)

    return text


def convert_markdown(text):
    """
    Convert markdown text to IRC format codes.
    Main entry point for standalone use.
    """
    global _list_counters
    _list_counters = {}

    if HAS_MARKDOWN:
        md = MarkdownIt()
        tokens = md.parse(text)
        tree = SyntaxTreeNode(tokens)
        return md_to_irc_converter(tree)
    else:
        return simple_md_to_irc(text)


# WeeChat-specific callbacks (only used when running inside WeeChat)

def modifier_cb(data, modifier, modifier_data, string):
    """Modifier callback to convert markdown in displayed messages."""
    global _list_counters
    _list_counters = {}

    if get_config("enabled", "on") != "on":
        return string

    parts = modifier_data.split(";", 1)
    tags = parts[1] if len(parts) > 1 else ""

    relevant_tags = ["irc_privmsg", "irc_notice", "notify_message", "notify_private"]
    if not any(tag in tags for tag in relevant_tags):
        return string

    md_patterns = [r'\*\*', r'__', r'\*', r'_', r'^\* ', r'^\d+\. ', r'^#', r'^```', r'`[^`]+`']
    has_md = any(re.search(pattern, string, re.MULTILINE) for pattern in md_patterns)

    if not has_md:
        return string

    return convert_markdown(string)


def config_cb(data, option, value):
    """Configuration callback."""
    if HAS_WEECHAT and weechat:
        weechat.config_set_plugin(option, value)
    return 0  # WEECHAT_RC_OK


def init_config():
    """Initialize plugin configuration."""
    if HAS_WEECHAT and weechat:
        settings = {"enabled": "on", "use_alt_format": "off"}
        for option, default_value in settings.items():
            if not weechat.config_is_set_plugin(option):
                weechat.config_set_plugin(option, default_value)


# WeeChat plugin initialization
if HAS_WEECHAT and __name__ == "__main__":
    weechat.register(SCRIPT_NAME, SCRIPT_AUTHOR, SCRIPT_VERSION, SCRIPT_LICENSE, SCRIPT_DESC, "", "")
    init_config()
    weechat.hook_modifier("weechat_print", "modifier_cb", "")

    if HAS_MARKDOWN:
        weechat.prnt("", f"{SCRIPT_NAME}: Loaded - colorizing markdown messages")
    else:
        weechat.prnt("", f"{SCRIPT_NAME}: Loaded (install markdown-it-py for better parsing)")


# CLI entry point for testing
if __name__ == "__main__" and not HAS_WEECHAT:
    import sys
    if len(sys.argv) > 1:
        print(convert_markdown(sys.argv[1]), end="")
    else:
        print(convert_markdown(sys.stdin.read()), end="")
