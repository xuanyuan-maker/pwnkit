#!/bin/python
# _*_ coding: utf-8 _*_

from pwn import *

context(arch='[ARCH]', os='linux')
context.terminal = ['konsole', '-e']
context.log_level = 'debug'
context.binary = '[ELF_PATH]'
e = ELF('[ELF_PATH]')
libc = e.libc
# libc = ELF('')
host = "127.0.0.1"
port = 9999
if args['RE']:
    io = remote(host, port)
else:
    io = process('[ELF_PATH]')


def debug():
    gdb.attach(io)
    pause()


sa = lambda s, d: io.sendafter(s, d)
sla = lambda s, d: io.sendlineafter(s, d)
sl = lambda d: io.sendline(d)
sd = lambda d: io.send(d)
ru = lambda s: io.recvuntil(s)
rc = lambda n: io.recv(n)
rl = lambda: io.recvline()
ti = lambda: io.interactive()
lg = lambda s, v: log.info('\033[1;32m %s --> 0x%x \033[0m' % (s, v))


def main():
    pass


if __name__ == '__main__':
    main()
    ti()
