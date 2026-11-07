/* crt.s —— 用户程序的入口。0.11 从虚拟地址 0 开始执行，所以 start 必须排第一。 */
	.text
	.globl start
start:
	movb $0x53, %al               /* 'S'：串口标记已进用户态，调 sh 时很好用 */
	movw $0x3f8, %dx
	out %al, %dx
	movl (%esp), %eax              /* argc */
	leal 4(%esp), %ebx             /* argv */
	pushl %ebx
	pushl %eax
	call main
	pushl %eax
	movl $1, %eax                  /* _exit */
	int $0x80

	.globl memcpy
memcpy:
	pushl %esi
	pushl %edi
	movl 12(%esp), %edi
	movl 16(%esp), %esi
	movl 20(%esp), %ecx
	movl %edi, %eax
	cld
	rep movsb
	popl %edi
	popl %esi
	ret

	.globl memset
memset:
	pushl %edi
	movl 8(%esp), %edi
	movl 12(%esp), %eax
	movl 16(%esp), %ecx
	movl %edi, %edx
	cld
	rep stosb
	movl %edx, %eax
	popl %edi
	ret
