#!/bin/bash
#
# Visual test script for markdown_irc plugin
# Simulates WeeChat output in terminal using ANSI codes
#

set -e

# ANSI color codes
ANSI_RESET="\033[0m"
ANSI_BOLD="\033[1m"
ANSI_ITALIC="\033[3m"

# Map IRC heading colors to ANSI colors
# c34 -> blue, c33 -> yellow, c32 -> green, c31 -> red, c30 -> black, c29 -> magenta

echo "=========================================="
echo "Markdown IRC Plugin - Visual Test"
echo "=========================================="
echo ""

# Function to convert IRC codes to ANSI
irc_to_ansi() {
    local input="$1"

    # Replace IRC codes with ANSI equivalents using perl for better escaping
    # Bold: \x03b -> \033[1m
    # Italic: \x0375 -> \033[3m
    # Reset: \x03o -> \033[0m
    # Heading colors: \x03c34, \x03c33, etc. -> \033[34m, \033[33m, etc.
    # List color (cyan)
    # Fence color (magenta)
    # Code color (bright black/gray)
    echo "$input" | perl -pe '
        s/\x03c34/\033[34m/g;
        s/\x03c33/\033[33m/g;
        s/\x03c32/\033[32m/g;
        s/\x03c31/\033[31m/g;
        s/\x03c30/\033[30m/g;
        s/\x03c29/\033[35m/g;
        s/\x03b/\033[1m/g;
        s/\x0375/\033[3m/g;
        s/\x03o/\033[0m/g;
        # Magenta for bullets/numbers
        s/\x0313/\033[35m/g;
        # Gray for code/fences
        s/\x0314/\033[90m/g;
    '
}

# Function to run a test case
run_test() {
    local description="$1"
    local input="$2"

    echo "----------------------------------------"
    echo "Test: $description"
    echo "----------------------------------------"
    echo "Input (Markdown):"
    echo "$input"
    echo ""

    # Convert using Python helper - uses markdown_irc.py's actual functions
    local output=$(python3 "$(dirname "$0")/test_visual_runner.py" "$input")

    # Show raw output with visible control chars
    echo "Raw IRC output (control chars visible):"
    echo "$output" | od -c
    echo ""

    # Show ANSI-formatted output
    echo "ANSI-formatted (should display with colors in terminal):"
    irc_to_ansi "$output"
    echo ""
    echo ""
}

# Run test suite
echo "Running test suite..."
echo ""

# Test 1: Bold
run_test "Bold text" "**bold text**"

# Test 2: Italic
run_test "Italic text" "*italic text*"

# Test 3: Heading Level 1
run_test "Heading Level 1" "# Main Title"

# Test 4: Heading Level 2
run_test "Heading Level 2" "## Subtitle"

# Test 5: Heading Level 3
run_test "Heading Level 3" "### Level 3"

# Test 6: Mixed formatting
run_test "Mixed formatting" "This is **bold** and *italic* text"

# Test 7: Document with structure
run_test "Document with headings" "# Title
Some text with **bold** words.
## Subtitle
More *italic* text."

# Test 8: Multiple heading levels
run_test "Multiple heading levels" "# Level 1
## Level 2
### Level 3
#### Level 4
##### Level 5
###### Level 6"

# Test 9: No markdown
run_test "Plain text (no markdown)" "Just some plain text without formatting"

# Test 10: Newline preservation
run_test "Newline preservation" "Line 1
Line 2
Line 3"

# Test 11: Bullet list (using *)
run_test "Bullet list" "* Item one
* Item two
* Item three"

# Test 12: Ordered list
run_test "Ordered list" "1. First item
2. Second item
3. Third item"

# Test 13: Inline code
run_test "Inline code" "Use the \`print()\` function to output text."

# Test 14: Fenced code block with content
run_test "Fenced code block" '```text
blabla
blabla
```'

# Test 15: Complex document
run_test "Complex document" "# Project Title

This is a **description** with *emphasis*.

## Features

* Feature one
* Feature two
* Feature three

## Code Example

Run this command: \`npm install\`

\`\`\`bash
echo "Hello"
\`\`\`"

# Test 16: EXAMPLE.md
run_test "EXAMPLE.md" "$(cat "$(dirname "$0")/EXAMPLE.md")"

echo "=========================================="
echo "Test complete!"
echo "=========================================="
echo ""
echo "If ANSI colors are not showing, ensure:"
echo "  - Your terminal supports ANSI colors"
echo "  - You're not piping through another command"
echo ""
echo "Raw IRC codes shown with od -c:"
echo "  \\003 represents Ctrl-C"
echo "  b = bold, o = reset, 75 = italic, c34-c29 = heading colors"
echo "  13 = magenta (bullets/numbers), 14 = gray (code/fences)"
echo ""
