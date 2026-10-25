bits 16
org 100h
jmp install
old dd 0
counter dw 36
index dw 0
length dw 0
keys times 4096 db 0
handler:
 pushf
 push ax
 push bx
 push dx
 push ds
 push es
 push cs
 pop ds
 dec word [counter]
 jnz done
 mov word [counter],1
 mov bx,[index]
 cmp bx,[length]
 jae done
 mov dl,[keys+bx]
 inc word [index]
 cmp dl,'~'
 jne key
 mov word [counter],36
 jmp done
key:
 mov ax,40h
 mov es,ax
 mov bx,[es:1ch]
 mov ax,bx
 add ax,2
 cmp ax,3eh
 jb nowrap
 mov ax,1eh
nowrap:
 cmp ax,[es:1ah]
 je done
 xor dh,dh
 mov [es:bx],dx
 mov [es:1ch],ax
done:
 pop es
 pop ds
 pop dx
 pop bx
 pop ax
 popf
 jmp far [cs:old]
install:
 mov dx,filename
 mov ax,3d00h
 int 21h
 jc exit
 mov bx,ax
 mov dx,keys
 mov cx,4096
 mov ah,3fh
 int 21h
 mov [length],ax
 mov ah,3eh
 int 21h
 mov ax,351ch
 int 21h
 mov [old],bx
 mov [old+2],es
 mov dx,handler
 mov ax,251ch
 int 21h
 mov dx,(resident_end-$$+100h+15)/16
 mov ax,3100h
 int 21h
exit:
 mov ax,4c01h
 int 21h
filename db 'KEYS.TXT',0
resident_end:
