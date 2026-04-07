# weechat-markdown

[Weechat](https://weechat.org) plugin for `draft/multiline` support and markdown colorization. This works well with OpenClaw, Hermes-agent etc, and a private IRC server 
like [ergo](https://ergo.chat) that supports BATCH and draft/multiline.

(note: Weechat is the IRC client from 2003, not the Chinese app called WeChat.)

## draft/multiline Support

WeeChat natively supports the modern [IRCv3 feature](https://ircv3.net/specs/extensions/multiline) `draft/multiline` when connected to servers that implement it (like [ergo](https://ergo.chat)). When AI agents like OpenClaw or Hermes-agent send multi-line markdown messages via this BATCH extension, this plugin intercepts the BATCH messages, buffers each PRIVMSG within the batch, combines them with newline characters into a single display message, and applies IRC formatting codes to render the markdown syntax (bold, italic, code, headers, lists) properly in Weechat.

## Install

Copy `markdown_irc.py` to `~/.local/share/weechat/python/autoload/` or whereever is your weechat config. Then in WeeChat, run `/script load markdown_irc.py`

See [WeeChat Python Scripts documentation](https://weechat.org/files/doc/stable/weechat_user.en.html#python_scripts) for more details.

## Config

- `colorize_markdown` (default: on) - Apply IRC formatting to markdown (bold, italic, code, headers, lists)
- `interpret_underscores` (default: off) - Interpret underscores `_text_` as italic (disabled by default to avoid false positives in code and regular text)

```
/set plugins.var.python.markdown_irc.colorize_markdown on
/set plugins.var.python.markdown_irc.interpret_underscores off
```

<img width="886" height="1009" alt="570521131-6cf8d023-bc4d-4483-8ef5-0761664d0a06" src="https://github.com/user-attachments/assets/52d8721c-a542-43a4-b433-4308e6337412" />

