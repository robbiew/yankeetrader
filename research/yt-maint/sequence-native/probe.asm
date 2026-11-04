; Assemble with NASM -f bin; same-size disposable YTMAINT.EXE diagnostic.
; SITE must be an exact five-byte QB runtime dispatch, copied as OP.
; Defaults are the RND(1) entry7908; CALLER reads SS:BP+2 at a helper seed.
bits 16
org 0x44
%ifndef SITE
 %define SITE 0x7908
%endif
%ifndef THRESHOLD
 %define THRESHOLD 65535
%endif
%ifndef SOURCE
 %define SOURCE 0x234
%endif
%ifndef CALLER
 %define CALLER 0
%endif
push cs
pop ds
mov dx,counter
jmp write
hook:
pushf
dec word [cs:counter]
jnz resume
%if CALLER
 push ss
 pop ds
 lea dx,[bp+2]
%else
 mov dx,SOURCE
%endif
write:
mov bx,1
mov cx,4
mov ah,0x40
int 0x21
mov ax,0x4c00
int 0x21
resume:
popf
%ifdef OP
 db OP
%else
 db 0xcd,0x3d,0x33,0x90,0x90
%endif
jmp SITE+5
counter: dw THRESHOLD
%if !CALLER
 db 'C!'
%endif
; Both variants occupy exactly46 bytes. At main-body return the caller variant
; reads the counter then the unchanged original bytes at72/73 (57cd).
