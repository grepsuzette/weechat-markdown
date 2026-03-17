# crayfish-weechat-markdown

WeeChat plugin that colorizes markdown from OpenClaw agents in IRC.

OpenClaw agents output markdown by default. This plugin makes it readable
in your WeeChat IRC client.

## Install

```bash
pip3 install markdown-it-py
cp markdown_irc.py ~/.weechat/python/autoload/
```

Then `/script load markdown_irc.py` in WeeChat (or restart).

## Supported

- **bold**, *italic*
- # Headings (color-coded by level)
- Bullet and numbered lists
- `inline code` and fenced code blocks

## Test

```bash
./test_visual.sh
```
