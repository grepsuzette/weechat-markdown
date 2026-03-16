# -*- coding: utf-8 -*-
"""
WeeChat Markdown to IRC converter plugin.
Converts markdown formatting to IRC color/formatting codes on message send.
"""

import weechat
import re

# Plugin info
SCRIPT_NAME = "markdown_irc"
SCRIPT_AUTHOR = "Chevette <chevette@irc>"
SCRIPT_VERSION = "0.1"
SCRIPT_LICENSE = "MIT"
SCRIPT_DESC = "Convert markdown formatting to IRC codes on message send"

# IRC format codes (using Ctrl-C format: \x03 + code)
# Note: WeeChat uses \x02 for bold, \x1F for underline, \x0F for reset
# But we can also use the \x03 prefix format: \x03b for bold, \x03o for reset
IRC_BOLD = "\x03b"
IRC_UNDERLINE = "\x03u"
IRC_ITALIC = "\x0375"
IRC_RESET = "\x03o"

# IRC color codes for markdown headings
# Maps heading level 1-6 to color codes c34-c29
HEADING_COLORS = ["c34", "c33", "c32", "c31", "c30", "c29"]

# Alternative format codes (single control chars)
ALT_BOLD = "\x02"
ALT_UNDERLINE = "\x1F"
ALT_RESET = "\x0F"

# Configuration
settings = {
    "enabled": "on",  # on/off
    "use_alt_format": "off",  # Use single-char format codes instead of \x03 prefix
}

# Try to import markdown-it-py
try:
    from markdown_it import MarkdownIt
    from markdown_it.tree import SyntaxTreeNode
    HAS_MARKDOWN = True
except ImportError:
    HAS_MARKDOWN = False


def md_to_irc_converter(node, options=None, env=None):
    """
    Custom renderer for markdown-it that outputs IRC formatting codes.
    """
    result = []
    
    if node.type == "root":
        for child in node.children:
            result.append(md_to_irc_converter(child, options, env))
    elif node.type == "paragraph":
        for child in node.children:
            result.append(md_to_irc_converter(child, options, env))
    elif node.type == "text":
        result.append(node.content)
    elif node.type == "heading_open":
        # Preserve the # characters in bold, then apply heading color
        level = node.tag  # This is "h1", "h2", etc.
        level_num = int(level[1]) - 1  # Convert "h1" to 0, "h2" to 1, etc.
        hashes = '#' * (level_num + 1)
        # Output bold # characters, space, then heading color for the text
        result.append(IRC_BOLD + hashes + IRC_RESET + " ")
        if 0 <= level_num < len(HEADING_COLORS):
            result.append("\x03" + HEADING_COLORS[level_num])
    elif node.type == "heading_close":
        result.append(IRC_RESET)
    elif node.type == "strong_open":
        result.append(IRC_BOLD if weechat.config_get_plugin("use_alt_format") != "on" else ALT_BOLD)
    elif node.type == "strong_close":
        result.append(IRC_RESET if weechat.config_get_plugin("use_alt_format") != "on" else ALT_RESET)
    elif node.type == "emph_open":
        result.append(IRC_ITALIC if weechat.config_get_plugin("use_alt_format") != "on" else ALT_BOLD)  # No single italic char
    elif node.type == "emph_close":
        result.append(IRC_RESET if weechat.config_get_plugin("use_alt_format") != "on" else ALT_RESET)
    elif node.type == "inline":
        for child in node.children:
            result.append(md_to_irc_converter(child, options, env))
    elif node.type == "softbreak":
        result.append("\n")  # Preserve newlines
    elif node.type == "hardbreak":
        result.append("\n")  # Preserve newlines (could use "\n\n" for hard breaks)
    
    return "".join(result)


def simple_md_to_irc(text):
    """
    Simple regex-based markdown to IRC converter (fallback if markdown-it not available).
    """
    # Convert headings (must be at start of line)
    # Keep # characters in bold, apply color to the rest
    # Process from h6 down to h1 to avoid partial matches
    for level in range(6, 0, -1):
        hashes = '#' * level
        color_code = HEADING_COLORS[level - 1]
        # Match heading at start of line, keep hashes in bold, apply color to text
        text = re.sub(
            r'^(' + hashes + r')\s+(.*)$',
            lambda m: IRC_BOLD + m.group(1) + IRC_RESET + ' ' + '\x03' + color_code + m.group(2) + IRC_RESET,
            text,
            flags=re.MULTILINE
        )
    
    # Convert bold **text** or __text__ (remove the delimiters)
    text = re.sub(r'\*\*(.*?)\*\*', IRC_BOLD + r'\1' + IRC_RESET, text)
    text = re.sub(r'__(.*?)__', IRC_BOLD + r'\1' + IRC_RESET, text)
    
    # Convert italic *text* or _text_ (remove the delimiters)
    text = re.sub(r'\*(.*?)\*', IRC_ITALIC + r'\1' + IRC_RESET, text)
    text = re.sub(r'_(.*?)_', IRC_ITALIC + r'\1' + IRC_RESET, text)
    
    # Convert code `text`
    # Could map to a specific color, but for now just keep as is
    # text = re.sub(r'`(.*?)`', IRC_CODE + r'\1' + IRC_RESET, text)
    
    return text


def modifier_cb(data, modifier, modifier_data, string):
    """
    Modifier callback to convert markdown in outgoing messages.
    Called before message is sent.
    """
    # Check if plugin is enabled
    if weechat.config_get_plugin("enabled") != "on":
        return string
    
    # Only process text messages (not commands starting with /)
    if string.startswith("/"):
        return string
    
    # Check if message contains markdown formatting
    md_patterns = [r'\*\*', r'__', r'\*', r'_']
    has_md = any(re.search(pattern, string) for pattern in md_patterns)
    
    if not has_md:
        return string
    
    # Convert markdown to IRC codes
    if HAS_MARKDOWN:
        md = MarkdownIt()
        tree = md.parse(string)
        converted = md_to_irc_converter(tree)
    else:
        converted = simple_md_to_irc(text=string)
    
    weechat.prnt("", f"DEBUG: markdown_irc converted '{string}' to '{converted}'")
    
    return converted


def config_cb(data, option, value):
    """Configuration callback."""
    weechat.config_set_plugin(option, value)
    return weechat.WEECHAT_RC_OK


def init_config():
    """Initialize plugin configuration."""
    for option, default_value in settings.items():
        if not weechat.config_is_set_plugin(option):
            weechat.config_set_plugin(option, default_value)


if __name__ == "__main__":
    weechat.register(SCRIPT_NAME, SCRIPT_AUTHOR, SCRIPT_VERSION, SCRIPT_LICENSE, SCRIPT_DESC, "", "")
    
    # Initialize configuration
    init_config()
    
    # Hook for modifier on input text (before send)
    weechat.hook_modifier("input_text_for_buffer", "modifier_cb", "")
    
    # Print info
    if HAS_MARKDOWN:
        weechat.prnt("", f"{SCRIPT_NAME}: Loaded with markdown-it-py support")
    else:
        weechat.prnt("", f"{SCRIPT_NAME}: Loaded with simple regex fallback (install python3-markdown-it for better parsing)")
