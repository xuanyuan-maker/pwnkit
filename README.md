# pwnkit

自己编写的 pwn 小工具集合，用于漏洞利用、ELF 与 libc 分析，以及 CTF 题目中的常用工作流。

## 开始使用

```bash
uv sync
uv run pwnkit -v chlibc /path/to/elf
```

`chlibc` 会探查 ELF 导入符号；相关文件路径和导入列表仅在 `-v/--verbose` 下输出。工具代码位于 `packages/pwnkit/src/pwnkit/`，独立的 Rust/C/C++ 工具放在 `tools/`。

## 许可证

[MIT](LICENSE)
