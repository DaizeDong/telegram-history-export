# telegram-history-export

用 Telegram 官方的 takeout 接口,把你自己的 Telegram 聊天记录连同上下文导出成结构化 JSON。和 discord、qq 的历史工具是姊妹项目,结构一致,以后再导出就是两条命令,不用从零调研。

聊天记录是私有数据,绝不进这个仓库。telethon 的 session 就是完整账号凭据,放在私有配置目录里,绝不入 git。仓里只有合成 fixture,数据边界闸门强制这一点。

## 两步

先自己在真实终端里登录一次。Telegram 会往你 App 发验证码,所以这步没法无人值守:

```
python tools/telegram_login.py
```

它会把 session 写进私有配置目录,session 坏了就硬失败。先把 api_id 和 api_hash(在 https://my.telegram.org 拿)放进该目录的 `telegram_api.json`。

然后导出,这步可以无人值守:

```
python tools/telegram_export.py --out ~/tg-out/telegram.jsonl
```

它经 takeout 接口拉取你的会话,每条消息写一条 JSON、把对方的话作为上下文保留,并跳过任何标题含 scrape 的文件夹,免得你只读不发的群把你真正说过的话淹了。用 `--exclude-folder` 改或关掉这个排除。

## 为什么这么做

Telegram 的 takeout 接口就是桌面端那个导出按钮背后的东西,ToS 干净、服务端限速友好。唯一的真坑是 session:从桌面端 tdata 转出来的 session 能连、也报已授权,但 `get_me()` 返回 None,于是每条消息的 out 标志都是 False、整份导出被标成"不是我发的"。两个工具都对这个硬失败,而且判定谁发的用的是 **out 标志或 sender id 等于自己 id 的并集**,不是只看 out 标志。详见 `docs/NOTES.md`。

## 配置目录

设 `$TELEGRAM_HISTORY_EXPORT_CONFIG`,否则用默认的 `~/.telegram-history-export-config`。里面放 `telegram_api.json`(api 凭据)和登录后生成的 `tg_session`。两者都是私有的,绝不能提交。

## 依赖

Python 加 `telethon`,没别的。登录那步要真实交互终端,导出那步不用。

## 输出记录

```
{"text", "is_me", "ctx": "dm"|"group", "ts", "sender", "conv", "is_forward"}
```

`sender` 是数字 id,绝不放名字。`conv` 标识会话。记录按 takeout 返回的顺序追加。

## 数据边界

session、凭据、导出的 jsonl 全是真实运行产物,在 `.dataclass.json` 里声明、绝不提交。测试跑在合成记录上,不需要任何真实账号就能验证代码。
