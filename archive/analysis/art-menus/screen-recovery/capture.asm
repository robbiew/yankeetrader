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
 push si
 push di
 push cx
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
 cmp dl,'@'
 je snapshot
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
 jmp done
snapshot:
 cld
 cmp word [frames],12
 jae done
 mov ax,4016
 mul word [frames]
 mov di,ax
 add di,buffer
 push ds
 pop es
 mov ax,40h
 mov ds,ax
 mov ax,[49h]
 stosw
 mov ax,[4ah]
 stosw
 mov ax,[4eh]
 stosw
 mov si,ax
 mov ax,[50h]
 stosw
 xor ax,ax
 mov cx,4
 rep stosw
 mov ax,0b800h
 mov ds,ax
 mov cx,2000
 rep movsw
 push cs
 pop ds
 inc word [frames]
 jmp done
done:
 pop es
 pop ds
 pop cx
 pop di
 pop si
 pop dx
 pop bx
 pop ax
 popf
 jmp far [cs:old]
query:
 push cs
 pop es
 mov bx,buffer
 mov cx,[cs:frames]
 iret
frames dw 0
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
 mov dx,query
 mov ax,2560h
 int 21h
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
buffer times 4016*12 db 0
resident_end:
