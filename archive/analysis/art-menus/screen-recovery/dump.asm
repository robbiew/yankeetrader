bits 16
org 100h
int 60h
mov [frames],cx
mov [ptr],bx
mov [segm],es
mov dx,filename
xor cx,cx
mov ah,3ch
int 21h
jc fail
mov bx,ax
mov ax,[frames]
mov cx,4016
mul cx
mov cx,ax
mov dx,[ptr]
mov ds,[segm]
mov ah,40h
int 21h
mov ah,3eh
int 21h
mov ax,4c00h
int 21h
fail:
mov ax,4c01h
int 21h
frames dw 0
ptr dw 0
segm dw 0
filename db 'SCREENS.BIN',0
