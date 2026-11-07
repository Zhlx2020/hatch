/* sh.c —— 给 0.11 用的最小 shell。
 *
 * 0.11 没有 libc：系统调用就是 int 0x80，参数走寄存器，返回值在 eax。
 * 只有内建命令和 fork+execve，够把 /etc/rc 跑完、给个提示符敲几条命令。
 * 没有登出/作业控制，这本来就是实验机的壳。
 */

#define SYS_exit   1
#define SYS_fork   2
#define SYS_read   3
#define SYS_write  4
#define SYS_open   5
#define SYS_close  6
#define SYS_execve 11
#define SYS_chdir  12
#define SYS_waitpid 7
#define SYS_getpid 20

static inline int sys1(int n, int a)
{
	int r;
	__asm__ volatile ("int $0x80" : "=a" (r) : "a" (n), "b" (a));
	return r;
}

static inline int sys2(int n, int a, int b)
{
	int r;
	__asm__ volatile ("int $0x80" : "=a" (r) : "a" (n), "b" (a), "c" (b));
	return r;
}

static inline int sys3(int n, int a, int b, int c)
{
	int r;
	__asm__ volatile ("int $0x80" : "=a" (r) : "a" (n), "b" (a), "c" (b), "d" (c));
	return r;
}

static int strlen(const char *s) { int n = 0; while (s[n]) n++; return n; }
static void puts(const char *s) { sys3(SYS_write, 1, (int) s, strlen(s)); }
static void putc(char c) { sys3(SYS_write, 1, (int) &c, 1); }

static int strcmp(const char *a, const char *b)
{
	while (*a && *a == *b) { a++; b++; }
	return *a - *b;
}

static int strncmp(const char *a, const char *b, int n)
{
	while (n-- && *a && *a == *b) { a++; b++; }
	return n < 0 ? 0 : *a - *b;
}

static void nl(void) { puts("\n\r"); }

static char buf[1024];
static char *argv[16];
static char *envp[3];

/* 把一行按空格切成 argv，返回个数 */
static int split(char *line)
{
	int n = 0;
	char *p = line;

	while (*p) {
		while (*p == ' ' || *p == '\t') p++;
		if (!*p) break;
		if (n < 15) argv[n++] = p;
		while (*p && *p != ' ' && *p != '\t') p++;
		if (*p) *p++ = 0;
	}
	argv[n] = 0;
	return n;
}

static void run(char *line)
{
	int n = split(line);
	int pid;
	char *a[2];

	if (!n) return;

	if (!strcmp(argv[0], "exit")) {
		sys1(SYS_exit, 0);
	}
	if (!strcmp(argv[0], "cd")) {
		char *to = argv[1] ? argv[1] : "/";
		if (sys1(SYS_chdir, (int) to) < 0) puts("cd: no such directory\n\r");
		return;
	}
	if (!strcmp(argv[0], "pwd") || !strcmp(argv[0], "clear") ||
	    !strcmp(argv[0], "echo") ||
	    !strcmp(argv[0], "cat") || !strcmp(argv[0], "ls")) {
		/* 内建：pwd 没有 getcwd，就不报路径了；ls 只列当前目录 */
		if (!strcmp(argv[0], "pwd")) { puts("/\n\r"); return; }
		if (!strcmp(argv[0], "clear")) { puts("\033[H\033[2J"); return; }
		if (!strcmp(argv[0], "echo")) {
			int i;
			for (i = 1; i < n; i++) { puts(argv[i]); if (i + 1 < n) putc(' '); }
			nl();
			return;
		}
		if (!strcmp(argv[0], "cat")) {
			int fd, got;
			if (n < 2) { puts("cat: file?\n\r"); return; }
			fd = sys3(SYS_open, (int) argv[1], 0, 0);
			if (fd < 0) { puts("cat: cannot open\n\r"); return; }
			while ((got = sys3(SYS_read, fd, (int) buf, 1024)) > 0)
				sys3(SYS_write, 1, (int) buf, got);
			sys1(SYS_close, fd);
			return;
		}
		if (!strcmp(argv[0], "ls")) {
			int fd, got, i;
			char name[15];
			fd = sys3(SYS_open, (int) "/", 0, 0);
			if (fd < 0) { puts("ls: cannot open /\n\r"); return; }
			while ((got = sys3(SYS_read, fd, (int) buf, 1024)) > 0) {
				for (i = 0; i + 16 <= got; i += 16) {
					int k;
					for (k = 0; k < 14 && buf[i + 2 + k]; k++) name[k] = buf[i + 2 + k];
					name[k] = 0;
					if (k) { puts(name); putc(' '); }
				}
			}
			sys1(SYS_close, fd);
			nl();
			return;
		}
	}

	/* 外部命令：名字里没斜杠就补上 /bin/ */
	if (argv[0][0] != '/' ) {
		char path[64];
		int k = 0;
		path[k++] = '/'; path[k++] = 'b'; path[k++] = 'i'; path[k++] = 'n'; path[k++] = '/';
		while (*argv[0] && k < 60) path[k++] = *argv[0]++;
		path[k] = 0;
		a[0] = path; a[1] = 0;
		argv[0] = path;
	}

	pid = sys1(SYS_fork, 0);
	if (pid == 0) {
		sys3(SYS_execve, (int) argv[0], (int) argv, (int) envp);
		puts("sh: cannot execute\n\r");
		sys1(SYS_exit, 1);
	}
	if (pid > 0) sys3(SYS_waitpid, pid, 0, 0);
}

/* 从 fd 里读，按字节切行并执行 */
static void run_fd(int fd)
{
	int got, i, n = 0;

	while ((got = sys3(SYS_read, fd, (int) buf, 256)) > 0) {
		for (i = 0; i < got; i++) {
			char c = buf[i];
			if (c == '\n') {
				buf[n] = 0;
				run(buf);
				n = 0;
			} else if (n < 200) {
				buf[n++] = c;
			}
		}
	}
	if (n) { buf[n] = 0; run(buf); }
}

/* 往串口写一个字节，调 shell 时能用 dbg('x') 在串口日志里留标记 */
static void dbg(char c)
{
	__asm__ volatile("outb %%al,%%dx" :: "a"(c), "d"(0x3f8));
}

int main(int argc, char **av)
{
	envp[0] = "HOME=/";
	envp[1] = "PATH=/bin:/usr/bin";
	envp[2] = 0;

	if (argc > 1) {
		int fd = sys3(SYS_open, (int) av[1], 0, 0);
		if (fd < 0) { puts("sh: cannot open script\n\r"); sys1(SYS_exit, 1); }
		run_fd(fd);
		sys1(SYS_exit, 0);
	}

	for (;;) {
		int fd = sys3(SYS_open, (int) "/dev/tty0", 2, 0);
		if (fd > 0) sys1(SYS_close, fd);
		puts("hatch$ ");
		{
			int got, n = 0;
			char c;
			while ((got = sys3(SYS_read, 0, (int) &c, 1)) > 0) {
				if (c == '\n') break;
				if (c == 8 || c == 127) {
					if (n) { n--; puts("\b \b"); }
					continue;
				}
				if (n < 200) { buf[n++] = c; putc(c); }
			}
			if (got <= 0 && !n) sys1(SYS_exit, 0);
			buf[n] = 0;
			nl();
			run(buf);
		}
	}
}

/* PE 目标会想要 __main */
void __main(void) {}
