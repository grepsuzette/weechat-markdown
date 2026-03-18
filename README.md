# crayfish-weechat-markdown

WeeChat plugin for draft/multiline support and optional markdown colorization.

## draft/multiline Support

IRC's `draft/multiline` extension allows sending multi-line messages via BATCH.
This plugin combines BATCH'd messages into single display lines in WeeChat.

## Install

```bash
cd ~/.weechat/python/autoload
git clone git@sidero.lan:crayfish-weechat-markdown.git
ln -s crayfish-weechat-markdown/markdown_irc.py .
```

Then in WeeChat:

```
/script load markdown_irc.py
```

## Config

```
/set plugins.var.python.markdown_irc.colorize_markdown on
```

- `colorize_markdown` (default: off) - Apply IRC formatting to markdown

## How It Works

1. Hooks `irc_in_batch` to detect `BATCH +id draft/multiline #channel`
2. Hooks `irc_in_privmsg` to intercept messages during active batch
3. Buffers all PRIVMSGs until `BATCH -id` arrives
4. Combines lines with `\n` and displays as one message

## Dependencies

- `markdown-it-py` (optional, for markdown colorization)

```
pip3 install markdown-it-py
```
