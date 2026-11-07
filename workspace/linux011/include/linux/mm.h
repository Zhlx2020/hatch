#ifndef _MM_H
#define _MM_H

#define PAGE_SIZE 4096

extern unsigned long get_free_page(void);
extern unsigned long put_page(unsigned long page,unsigned long address);
extern void free_page(unsigned long addr);
extern void hatch_copy_shared_page(unsigned long addr);	/* HATCH: fork 时立刻私有化子进程栈页 */

#endif
