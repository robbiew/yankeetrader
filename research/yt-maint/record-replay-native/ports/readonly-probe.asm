; Diagnostic only: same-size46-byte copied YTMAINT patch at main0044.
; Requires a386-capable research emulator. No production binary is modified.
; TARGET is the four-byte MBF port-index bit pattern, interpreted little-endian.
; Defaultffffffff never equals an admitted port index;606 is8a178000.
bits 16
org 0x44
%ifndef TARGET
 %define TARGET 0xffffffff
%endif
push cs
pop ds
mov dx,0                 ; unchanged main module header as body-end witness
jmp write
hook:
pushf
cmp dword [0x7ad6],strict dword TARGET
jne resume
mov dx,0x1a              ; raw FAC after TIMER/60, before storing into port
write:
mov bx,1
mov cx,4
mov ah,0x40
int 0x21
mov ax,0x4c00
int 0x21
resume:
popf
db 0xcd,0x3f,0x7d,0x90,0x90
jmp 0x939
