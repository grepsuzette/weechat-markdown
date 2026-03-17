#!/usr/bin/env python3
"""
Test runner - standalone markdown to IRC converter.
Uses markdown-it-py when available, regex fallback otherwise.
"""

import sys
import re

# Import markdown-it-py directly
try:
    from markdown_it import MarkdownIt
    from markdown_it.tree import SyntaxTreeNode
    HAS_MARKDOWN = True
except ImportError:
    HAS_MARKDOWN = False

# IRC format codes (from markdown_irc.py)
IRC_BOLD = "\x03b"
IRC_ITALIC = "\x0375"
IRC_RESET = "\x03o"
HEADING_COLORS = ["c34", "c33", "c32", "c31", "c30", "c29"]

# Additional color codes
IRC_BULLET_COLOR = "\x0313"  # Magenta for bullets and numbers
IRC_FENCE_COLOR = "\x0314"   # Gray for code blocks
IRC_CODE_COLOR = "\x0314"    # Gray for inline code

# Global counter for ordered lists
_list_counters = {}

def md_to_irc(node, list_id=None):
    """Convert markdown tree to IRC formatting codes."""
    global _list_counters
    result = []

    if node.type == "root":
        if hasattr(node, 'children') and node.children:
            for child in node.children:
                result.append(md_to_irc(child, list_id=list_id))
    elif node.type == "paragraph":
        if hasattr(node, 'children') and node.children:
            for child in node.children:
                result.append(md_to_irc(child, list_id=list_id))
        result.append("\n")
    elif node.type == "text":
        result.append(node.content if hasattr(node, 'content') else '')
    elif node.type == "heading":
        # SyntaxTreeNode collapses heading_open/close into single 'heading' node
        level = node.tag if hasattr(node, 'tag') else "h1"
        level_num = int(level[1]) - 1
        hashes = '#' * (level_num + 1)
        result.append(IRC_BOLD + hashes + IRC_RESET + " ")
        if 0 <= level_num < len(HEADING_COLORS):
            result.append("\x03" + HEADING_COLORS[level_num])
        if hasattr(node, 'children') and node.children:
            for child in node.children:
                result.append(md_to_irc(child, list_id=list_id))
        result.append(IRC_RESET + "\n\n")
    elif node.type == "strong":
        # SyntaxTreeNode collapses strong_open/close into single 'strong' node
        result.append(IRC_BOLD)
        if hasattr(node, 'children') and node.children:
            for child in node.children:
                result.append(md_to_irc(child, list_id=list_id))
        result.append(IRC_RESET)
    elif node.type == "em":
        # SyntaxTreeNode collapses emph_open/close into single 'em' node
        result.append(IRC_ITALIC)
        if hasattr(node, 'children') and node.children:
            for child in node.children:
                result.append(md_to_irc(child, list_id=list_id))
        result.append(IRC_RESET)
    elif node.type == "inline":
        if hasattr(node, 'children') and node.children:
            for child in node.children:
                result.append(md_to_irc(child, list_id=list_id))
    elif node.type == "softbreak":
        result.append("\n")
    elif node.type == "hardbreak":
        result.append("\n")
    # Bullet list support
    elif node.type == "bullet_list":
        if hasattr(node, 'children') and node.children:
            for child in node.children:
                result.append(md_to_irc(child, list_id=list_id))
        result.append("\n")
    # Ordered list support
    elif node.type == "ordered_list":
        # Reset counter for this list
        current_list_id = id(node)
        _list_counters[current_list_id] = 0
        if hasattr(node, 'children') and node.children:
            for child in node.children:
                result.append(md_to_irc(child, list_id=current_list_id))
        result.append("\n")
    elif node.type == "list_item":
        if hasattr(node, 'children') and node.children:
            # Check if parent is ordered_list or bullet_list
            parent = node.parent if hasattr(node, 'parent') else None
            if parent and parent.type == "ordered_list" and list_id is not None:
                # Ordered list item - use numbered format
                _list_counters[list_id] = _list_counters.get(list_id, 0) + 1
                num = _list_counters[list_id]
                result.append(IRC_BULLET_COLOR + f"{num}. " + IRC_RESET)
            else:
                # Bullet list item - use * format
                result.append(IRC_BULLET_COLOR + "* " + IRC_RESET)
            for child in node.children:
                result.append(md_to_irc(child, list_id=list_id))
    # Code block support (fence with ```)
    elif node.type == "fence":
        result.append(IRC_FENCE_COLOR + "```\n")
        # Fence content is in node.content, not children
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
    """Simple regex-based markdown to IRC converter (fallback)."""
    # Convert headings (must be at start of line)
    for level in range(6, 0, -1):
        hashes = '#' * level
        color_code = HEADING_COLORS[level - 1]
        text = re.sub(
            r'^(#{' + str(level) + r'})\s+(.*)$',
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

    # Convert inline code `text`
    text = re.sub(r'`(.*?)`', IRC_CODE_COLOR + r'\1' + IRC_RESET, text)

    # Convert bullet list items (using *)
    text = re.sub(r'^\*\s+(.*)$',
                  lambda m: IRC_BULLET_COLOR + "* " + IRC_RESET + m.group(1),
                  text, flags=re.MULTILINE)

    # Convert ordered list items
    text = re.sub(r'^(\d+)\.\s+(.*)$',
                  lambda m: IRC_BULLET_COLOR + m.group(1) + ". " + IRC_RESET + m.group(2),
                  text, flags=re.MULTILINE)

    return text

def main():
    if len(sys.argv) > 1:
        input_text = sys.argv[1]
    else:
        input_text = sys.stdin.read()

    if HAS_MARKDOWN:
        md = MarkdownIt()
        tokens = md.parse(input_text)
        tree = SyntaxTreeNode(tokens)
        output = md_to_irc(tree)
    else:
        # Fallback to regex when markdown-it-py is not installed
        output = simple_md_to_irc(input_text)

    sys.stdout.write(output)

if __name__ == '__main__':
    main()
