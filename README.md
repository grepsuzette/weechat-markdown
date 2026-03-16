Weechat plugin to convert markdown formatting to IRC codes when receiving messages.

## Features

- **bold** or __bold__ → IRC bold
- *italic* or _italic_ → IRC italic
- # Heading → Bold # with color (c34-c29 for levels 1-6)
- Preserves newlines

## Installation

```bash
# Install markdown parser
pip3 install markdown-it-py

# Copy plugin to WeeChat
cp markdown_irc.py ~/.weechat/python/autoload/

# Load in WeeChat (or restart)
/python load ~/.weechat/python/autoload/markdown_irc.py
```

## Usage

Just type markdown in your messages:

```
**bold** *italic* text
# Title
## Subtitle
```

## Configuration

```
/set plugins.var.python.markdown_irc.enabled on
/set plugins.var.python.markdown_irc.use_alt_format off
```

## Testing

```bash
# Visual test (outside WeeChat)
./test_visual.sh

# Unit tests
python3 test_markdown_irc.py
```
