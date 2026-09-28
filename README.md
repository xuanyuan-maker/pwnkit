# pwnkit

自己编写的 pwn 小工具集合，用于漏洞利用、ELF 与 libc 分析，以及 CTF 题目中的常用工作流。

## 开始使用

```bash
uv sync
uv run pwnkit -v chlibc /path/to/elf
uv run pwnkit init /path/to/elf
```

`chlibc` 会检查 ELF 架构、递归解析 `DT_NEEDED` 依赖，并优先使用 ELF 所在目录的库；缺少 glibc 时从本地 `configs/pwnkit.toml` 查找候选版本。首次使用可复制 `configs/pwnkit.example.toml`，该本地配置不会提交。也可以用 `PWNKIT_GLIBC_ROOT` 或 `PWNKIT_CONFIG` 指定配置。选择菜单中的 `0` 表示不修改。架构、依赖和候选信息仅在 `-v/--verbose` 下输出，选择、成功和失败信息正常输出。工具代码位于 `packages/pwnkit/src/pwnkit/`，独立的 Rust/C/C++ 工具放在 `tools/`。

## GDB glibc 调试符号

在 GDB 中加载 `gdb/glibc-debug.py`，脚本会读取本地 `configs/pwnkit.toml`，自动设置 glibc 调试符号和 `libthread_db` 搜索路径：

```gdb
source /path/to/pwnkit/gdb/glibc-debug.py
```

也可以用 `PWN_GLIBC_LIBS_DIR` 或 `PWNKIT_GLIBC_ROOT` 临时覆盖库目录，或用 `PWNKIT_CONFIG` 指定配置文件。加载后可执行 `pwn-glibc-debug-reload` 重新扫描。

`init` 会为 ELF 及其同目录依赖添加可执行权限，自动执行 `chlibc`，并在题目目录生成 `exp.py`；使用 `uv run pwnkit init /path/to/elf heap` 生成堆题模板。

生成的 EXP 模板默认使用 kitty 作为 GDB 终端。远程普通 TCP 题目运行 `python exp.py RE`；需要 TLS 的按实例域名容器运行 `python exp.py RE SSL`，模板会使用 `host` 作为 SNI。

## 许可证

[MIT](LICENSE)
