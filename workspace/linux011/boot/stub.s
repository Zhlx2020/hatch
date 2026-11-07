/* PE 目标的两处补丁，只为了让 0.11 这份老代码在新工具链上链得起来。
 *
 * 1. __main：PE 的 gcc 会在 main() 的序言里插一句 call __main，替它补一个空的。
 * 2. memcpy：0.11 把 memcpy 写成 string.h 里的 static inline，没包含那份头文件的
 *    翻译单元会留下未定义引用，这里给一份真的。
 */
	.text
	.globl __main
__main:
	ret

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
