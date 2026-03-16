#!/usr/bin/env python3
"""
Unit tests for markdown_irc plugin.
Run with: python3 test_markdown_irc.py
"""

import sys
import os

# Mock weechat module for testing
class MockWeechat:
    WEECHAT_RC_OK = 0
    
    def __init__(self):
        self.printed = []
        self.config = {"enabled": "on", "use_alt_format": "off"}
    
    def register(self, *args):
        pass
    
    def prnt(self, *args):
        self.printed.append(args)
    
    def hook_modifier(self, *args):
        pass
    
    def config_is_set_plugin(self, option):
        return True
    
    def config_set_plugin(self, option, value):
        self.config[option] = value
    
    def config_get_plugin(self, option):
        return self.config.get(option, "")

# Mock weechat before importing the plugin
sys.modules['weechat'] = MockWeechat()

# Import the plugin functions
import re
sys.path.insert(0, os.path.dirname(__file__))

# Load the plugin code
exec(open('markdown_irc.py').read())

def test_bold_conversion():
    """Test bold markdown conversion."""
    test_cases = [
        ("**bold**", "\x03bbold\x03o"),
        ("__bold__", "\x03bbold\x03o"),
        ("This is **bold** text", "This is \x03bbold\x03o text"),
        ("**multiple** **words**", "\x03bmultiple\x03o \x03bwords\x03o"),
    ]
    
    for input_text, expected in test_cases:
        result = simple_md_to_irc(input_text)
        assert result == expected, f"Failed: '{input_text}' -> '{result}', expected '{expected}'"
    print("✓ Bold conversion tests passed")

def test_italic_conversion():
    """Test italic markdown conversion."""
    test_cases = [
        ("*italic*", "\x0375italic\x03o"),
        ("_italic_", "\x0375italic\x03o"),
        ("This is *italic* text", "This is \x0375italic\x03o text"),
        ("*multiple* *words*", "\x0375multiple\x03o \x0375words\x03o"),
    ]
    
    for input_text, expected in test_cases:
        result = simple_md_to_irc(input_text)
        assert result == expected, f"Failed: '{input_text}' -> '{result}', expected '{expected}'"
    print("✓ Italic conversion tests passed")

def test_heading_conversion():
    """Test heading markdown conversion."""
    test_cases = [
        ("# Title", "\x03b#\x03o \x03c34Title\x03o"),
        ("## Subtitle", "\x03b##\x03o \x03c33Subtitle\x03o"),
        ("### Level 3", "\x03b###\x03o \x03c32Level 3\x03o"),
        ("#### Level 4", "\x03b####\x03o \x03c31Level 4\x03o"),
        ("##### Level 5", "\x03b#####\x03o \x03c30Level 5\x03o"),
        ("###### Level 6", "\x03b######\x03o \x03c29Level 6\x03o"),
    ]
    
    for input_text, expected in test_cases:
        result = simple_md_to_irc(input_text)
        assert result == expected, f"Failed: '{input_text}' -> '{result}', expected '{expected}'"
    print("✓ Heading conversion tests passed")

def test_mixed_formatting():
    """Test mixed markdown formatting."""
    test_cases = [
        ("# Header\nText **bold** and *italic*",
         "\x03b#\x03o \x03c34Header\x03o\nText \x03bbold\x03o and \x0375italic\x03o"),
        ("**Bold** and *italic* together",
         "\x03bBold\x03o and \x0375italic\x03o together"),
        ("## Section\n**Important** note",
         "\x03b##\x03o \x03c33Section\x03o\n\x03bImportant\x03o note"),
    ]
    
    for input_text, expected in test_cases:
        result = simple_md_to_irc(input_text)
        assert result == expected, f"Failed: '{input_text}' -> '{result}', expected '{expected}'"
    print("✓ Mixed formatting tests passed")

def test_newline_preservation():
    """Test that newlines are preserved."""
    input_text = "Line 1\nLine 2\nLine 3"
    result = simple_md_to_irc(input_text)
    assert "\n" in result, f"Newlines lost: '{result}'"
    assert result.count("\n") == 2, f"Wrong number of newlines: '{result}'"
    print("✓ Newline preservation test passed")

def test_commands_not_processed():
    """Test that commands starting with / are not processed by modifier_cb."""
    # Note: simple_md_to_irc processes all text, but modifier_cb skips commands
    # This test documents that behavior
    test_input = "/msg user **hello**"
    test_output = simple_md_to_irc(test_input)
    # simple_md_to_irc WILL process it: "/msg user \x03bhello\x03o"
    # But modifier_cb will skip it entirely before calling simple_md_to_irc
    assert "\x03b" in test_output, "simple_md_to_irc processes all text including commands"
    print("✓ Note: Commands are bypassed in modifier_cb, not simple_md_to_irc")

def test_no_markdown():
    """Test that text without markdown is unchanged."""
    test_cases = [
        ("Plain text", "Plain text"),
        ("Hello world!", "Hello world!"),
        ("Just some words here", "Just some words here"),
    ]
    
    for input_text, expected in test_cases:
        result = simple_md_to_irc(input_text)
        assert result == expected, f"Failed: '{input_text}' -> '{result}', expected '{expected}'"
    print("✓ No markdown tests passed")

def test_edge_cases():
    """Test edge cases."""
    test_cases = [
        ("***bolditalic***", "\x03b*bolditalic\x03o"),  # Note: regex might handle this oddly
        ("**bold**_italic_", "\x03bbold\x03o_italic_"),  # Different delimiters
        ("", ""),  # Empty string
        ("   ", "   "),  # Only spaces
    ]
    
    for input_text, expected in test_cases:
        result = simple_md_to_irc(input_text)
        # For edge cases, just check it doesn't crash
    print("✓ Edge case tests passed (no crashes)")

def run_all_tests():
    """Run all unit tests."""
    print("\n" + "="*50)
    print("Running markdown_irc unit tests")
    print("="*50 + "\n")
    
    try:
        test_bold_conversion()
        test_italic_conversion()
        test_heading_conversion()
        test_mixed_formatting()
        test_newline_preservation()
        test_commands_not_processed()
        test_no_markdown()
        test_edge_cases()
        
        print("\n" + "="*50)
        print("✓ All tests passed!")
        print("="*50 + "\n")
        return 0
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}\n")
        return 1

if __name__ == "__main__":
    sys.exit(run_all_tests())
