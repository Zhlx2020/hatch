/*
 *  linux/kernel/exit.c
 *
 *  (C) 1991  Linus Torvalds
 */

#include <errno.h>
#include <signal.h>
#include <sys/wait.h>

#include <linux/sched.h>
#include <linux/kernel.h>
#include <linux/tty.h>
#include <asm/segment.h>

// 鎶婅繘绋嬬疆涓虹潯鐪犵姸鎬侊紝鐩村埌鏀跺埌淇″彿
int sys_pause(void);
// 鍏抽棴鎸囧畾鏂囦欢鐨勭郴缁熻皟鐢?
int sys_close(int fd);

//// 閲婃斁鎸囧畾杩涚▼鍗犵敤鐨勪换鍔℃Ы鍙婂叾浠诲姟鏁版嵁缁撴瀯鍗犵敤鐨勫唴瀛橀〉闈€?
// 鍙傛暟p鏄换鍔℃暟鎹粨鏋勬寚閽堛€傝鍑芥暟鍦ㄥ悗闈㈢殑sys_kill()鍜宻ys_waitpid()鍑芥暟涓璋冪敤銆?
// 鎵弿浠诲姟鎸囬拡鏁扮粍琛╰ask[]浠ュ鎵炬寚瀹氱殑浠诲姟銆傚鏋滄壘鍒帮紝鍒欓鍏堟竻绌鸿浠诲姟妲斤紝鐒跺悗
// 閲婃斁璇ヤ换鍔℃暟鎹粨鏋勬墍鍗犵敤鐨勫唴瀛橀〉闈紝鏈€鍚庢墽琛岃皟搴﹀嚱鏁板苟鍦ㄨ繑鍥炴椂绔嬪嵆閫€鍑恒€傚鏋?
// 鍦ㄤ换鍔℃暟缁勮〃涓病鏈夋壘鍒版寚瀹氫换鍔″搴旂殑椤癸紝鍒欏唴鏍竝anic. ;-)
void release(struct task_struct * p)
{
	int i;

	if (!p)                         // 濡傛灉杩涚▼鏁版嵁缁撴瀯鎸囬拡鏄疦ULL锛屽垯浠€涔堜篃涓嶅仛锛岄€€鍑恒€?
		return;
	for (i=1 ; i<NR_TASKS ; i++)    // 鎵弿浠诲姟鏁扮粍锛屽鎵炬寚瀹氫换鍔?
		if (task[i]==p) {
			task[i]=NULL;           // 缃┖璇ヤ换鍔￠」骞堕噴鏀剧浉鍏冲唴瀛橀〉銆?
			free_page((long)p);
			schedule();             // 閲嶆柊璋冨害(浼间箮娌℃湁蹇呰)
			return;
		}
	panic("trying to release non-existent task");       // 鎸囧畾浠诲姟鑻ヤ笉瀛樺湪鍒欐鏈?
}

//// 鍚戞寚瀹氫换鍔鍙戦€佷俊鍙穝ig, 鏉冮檺priv銆?
// 鍙傛暟锛歴ig - 淇″彿鍊硷紱p - 鎸囧畾浠诲姟鐨勬寚閽堬紱priv - 寮哄埗鍙戦€佷俊鍙风殑鏍囧織銆傚嵆涓嶉渶瑕佽€冭檻杩涚▼
// 鐢ㄦ埛灞炴€ф垨绾у埆鑰岃兘鍙戦€佷俊鍙风殑鏉冨埄銆傝鍑芥暟棣栧厛鍒ゆ柇鍙傛暟鐨勬纭€э紝鐒跺悗鍒ゆ柇鏉′欢鏄惁婊¤冻銆?
// 濡傛灉婊¤冻灏卞悜鎸囧畾杩涚▼鍙戦€佷俊鍙穝ig骞堕€€鍑猴紝鍚﹀垯杩斿洖涓鸿鍙敊璇彿銆?
static inline int send_sig(long sig,struct task_struct * p,int priv)
{
    // 鑻ヤ俊鍙蜂笉姝ｇ‘鎴栦换鍔℃寚閽堜负绌猴紝鍒欏嚭閿欓€€鍑恒€?
	if (!p || sig<1 || sig>32)
		return -EINVAL;
    // 濡傛灉寮哄埗鍙戦€佹爣蹇楃疆浣嶏紝鎴栬€呭綋鍓嶈繘绋嬬殑鏈夋晥鐢ㄦ埛鏍囪瘑绗?euid)灏辨槸鎸囧畾杩涚▼鐨別uid锛堜篃
    // 鍗虫槸鑷繁锛夛紝鎴栬€呭綋鍓嶈繘绋嬫槸瓒呯骇鐢ㄥ锛屽垯鍚戣繘绋媝鍙戦€佷俊鍙穝ig锛屽嵆鍦ㄨ繘绋媝浣嶅浘涓坊鍔犺
    // 淇″彿锛屽惁鍒欏嚭閿欓€€鍑恒€傚叾涓璼user()瀹氫箟涓?current->euid==0)锛岀敤浜庡垽鏂槸鍚︽槸瓒呯骇鐢ㄦ埛銆?
	if (priv || (current->euid==p->euid) || suser())
		p->signal |= (1<<(sig-1));
	else
		return -EPERM;
	return 0;
}

//// 缁堟浼氳瘽(session)
static void kill_session(void)
{
	struct task_struct **p = NR_TASKS + task;   // 鎸囬拡*p棣栧厛鎸囧悜浠诲姟鏁扮粍鏈€鏈
	
    // 鎵弿浠诲姟鎸囬拡鏁扮粍锛屽浜庢墍鏈夌殑浠诲姟(闄や换鍔?浠ュ)锛屽鏋滃叾浼氳瘽鍙穝ession绛変簬褰撳墠杩涚▼鐨?
    // 浼氳瘽鍙峰氨鍚戝畠鍙戦€佹寕鏂繘绋嬩俊鍙稴IGHUP銆?
	while (--p > &FIRST_TASK) {
		if (*p && (*p)->session == current->session)
			(*p)->signal |= 1<<(SIGHUP-1);      // 鍙戦€佹寕鏂繘绋嬩俊鍙?
	}
}

/*
 * XXX need to check permissions needed to send signals to process
 * groups, etc. etc.  kill() permissions semantics are tricky!
 */
//// 绯荤粺璋冪敤kill()鍙敤浜庡悜浠讳綍杩涚▼鎴栬繘绋嬬粍鍙戦€佷换浣曚俊鍙凤紝鑰屽苟闈炲彧鏄潃姝昏繘绋嬨€?-)
// 鍙傛暟pid鏄繘绋嬪彿锛泂ig鏄渶瑕佸彂閫佺殑淇″彿銆?
// 濡傛灉pid > 0, 鍒欎俊鍙疯鍙戦€佺粰杩涚▼鍙锋槸pid鐨勮繘绋嬨€?
// 濡傛灉pid = 0, 閭ｄ箞淇″彿灏变細琚彂閫佺粰褰撳墠杩涚▼鐨勮繘绋嬬粍涓殑鎵€鏈夎繘绋嬨€?
// 濡傛灉pid = -1,鍒欎俊鍙穝ig灏变細鍙戦€佺粰闄ょ涓€涓繘绋?鍒濆杩涚▼init)澶栫殑鎵€鏈夎繘绋?
// 濡傛灉pid < -1,鍒欎俊鍙穝ig灏嗗彂閫佺粰杩涚▼缁?pid鐨勬墍鏈夎繘绋嬨€?
// 濡傛灉淇″彿sig=0,鍒欎笉鍙戦€佷俊鍙凤紝浣嗕粛浼氳繘琛岄敊璇鏌ャ€傚鏋滄垚鍔熷垯杩斿洖0.
// 璇ュ嚱鏁版壂鎻忎换鍔℃暟缁勮〃锛屽苟鏍规嵁pid鐨勫€煎婊¤冻鏉′欢鐨勮繘绋嬪彂閫佹寚瀹氫俊鍙穝ig銆傝嫢pid=0,
// 琛ㄦ槑褰撳墠杩涚▼鏄繘绋嬬粍缁勯暱锛屽洜姝ら渶瑕佸悜鎵€鏈夌粍鍐呰繘绋嬪己鍒跺彂閫佷俊鍙穝ig.
int sys_kill(int pid,int sig)
{
	struct task_struct **p = NR_TASKS + task;
	int err, retval = 0;

	if (!pid) while (--p > &FIRST_TASK) {
		if (*p && (*p)->pgrp == current->pid) 
			if ((err=send_sig(sig,*p,1)))           // 寮哄埗鍙戦€佷俊鍙?
				retval = err;
	} else if (pid>0) while (--p > &FIRST_TASK) {
		if (*p && (*p)->pid == pid) 
			if ((err=send_sig(sig,*p,0)))
				retval = err;
	} else if (pid == -1) while (--p > &FIRST_TASK) {
		if ((err = send_sig(sig,*p,0)))
			retval = err;
	} else while (--p > &FIRST_TASK)
		if (*p && (*p)->pgrp == -pid)
			if ((err = send_sig(sig,*p,0)))
				retval = err;
	return retval;
}

//// 閫氱煡鐖惰繘绋?- 鍚戣繘绋媝id鍙戦€佷俊鍙稴IGCHLD锛涢粯璁ゆ儏鍐典笅瀛愯繘绋嬪皢鍋滄鎴栫粓姝€?
// 濡傛灉娌℃湁鎵惧埌鐖惰繘绋嬶紝鍒欒嚜宸遍噴鏀俱€備絾鏍规嵁POSIX.1瑕佹眰锛岃嫢鐖惰繘绋嬪凡鍏堣缁堟锛?
// 鍒欏瓙杩涚▼搴旇琚垵濮嬭繘绋?鏀跺銆?
static void tell_father(int pid)
{
	int i;

	if (pid)
        // 鎵弿杩涘煄鏁扮粍琛紝瀵绘壘鎸囧畾杩涚▼pid锛屽苟鍚戝叾鍙戦€佸瓙杩涚▼灏嗗仠姝㈡垨缁堟淇″彿SIGCHLD銆?
		for (i=0;i<NR_TASKS;i++) {
			if (!task[i])
				continue;
			if (task[i]->pid != pid)
				continue;
			task[i]->signal |= (1<<(SIGCHLD-1));
			return;
		}
/* if we don't find any fathers, we just release ourselves */
/* This is not really OK. Must change it to make father 1 */
	printk("BAD BAD - no father found\n\r");
	release(current);               // 濡傛灉娌℃湁鎵惧埌鐖惰繘绋嬶紝鍒欒嚜宸遍噴鏀?
}

//// 绋嬪簭閫€鍑哄鐞嗗嚱鏁般€?
// 璇ュ嚱鏁板皢鎶婂綋鍓嶈繘绋嬬疆涓篢ASK_ZOMBIE鐘舵€侊紝鐒跺悗鍘绘墽琛岃皟搴﹀嚱鏁皊chedule()锛屼笉鍐嶈繑鍥炪€?
// 鍙傛暟code鏄€€鍑虹姸鎬佺爜锛屾垨绉颁负閿欒鐮併€?
int do_exit(long code)
{
	int i;
    // 棣栧厛閲婃斁褰撳墠杩涚▼浠ｇ爜娈靛拰鏁版嵁娈垫墍鍗犵殑鍐呭瓨椤点€傚嚱鏁癴ree_page_tables()鐨勭涓€涓弬鏁?
    // (get_base()杩斿洖鍊?鎸囨槑鍦–PU绾挎€у湴鍧€绌洪棿涓捣濮嬪熀鍦板潃锛岀2涓?get_limit()杩斿洖鍊?
    // 璇存槑娆查噴鏀剧殑瀛楄妭闀垮害鍊笺€俫et_base()瀹忎腑鐨刢urrent->ldt[1]缁欏嚭杩涚▼浠ｇ爜娈垫弿杩扮鐨?
    // 浣嶇疆(current->ldt[2]缁欏嚭杩涚▼浠ｇ爜娈垫弿杩扮鐨勪綅缃?锛沢et_limit()涓?x0f鏄繘绋嬩唬鐮佹
    // 鐨勯€夋嫨绗?0x17鏄繘鍩庢暟鎹鐨勯€夋嫨绗?銆傚嵆鍦ㄥ彇娈靛熀鍦板潃鏃朵娇鐢ㄨ娈电殑鎻忚堪绗︽墍澶勫湴鍧€浣滀负
    // 鍙傛暟锛屽彇娈甸暱搴︽椂浣跨敤璇ユ鐨勯€夋嫨绗︿綔涓哄弬鏁般€俧ree_page_tables()鍑芥暟浣嶄簬mm/memory.c
    // 鏂囦欢涓€?
	free_page_tables(get_base(current->ldt[1]),get_limit(0x0f));
	free_page_tables(get_base(current->ldt[2]),get_limit(0x17));
    // 濡傛灉褰撳墠杩涚▼鏈夊瓙杩涚▼锛屽氨灏嗗瓙杩涚▼鐨刦ather缃负1(鍏剁埗杩涚▼鏀逛负杩涚▼1锛屽嵆init杩涚▼)銆?
    // 濡傛灉璇ュ瓙杩涚▼宸茬粡澶勪簬鍍垫(ZOMBIE)鐘舵€侊紝鍒欏悜杩涚▼1鍙戦€佸瓙杩涚▼涓淇″彿SIGCHLD銆?
	for (i=0 ; i<NR_TASKS ; i++)
		if (task[i] && task[i]->father == current->pid) {
			task[i]->father = 1;
			if (task[i]->state == TASK_ZOMBIE)
				/* assumption task[1] is always init */
				(void) send_sig(SIGCHLD, task[1], 1);
		}
    // 鍏抽棴褰撳墠杩涚▼鎵撳紑鐫€鐨勬墍鏈夋枃浠躲€?
	for (i=0 ; i<NR_OPEN ; i++)
		if (current->filp[i])
			sys_close(i);
    // 瀵瑰綋鍓嶈繘绋嬬殑宸ヤ綔鐩綍pwd锛屾牴鐩綍root浠ュ強鎵ц绋嬪簭鏂囦欢鐨刬鑺傜偣杩涜鍚屾鎿嶄綔锛屾斁鍥?
    // 鍚勪釜i鑺傜偣骞跺垎鍒疆绌?閲婃斁)銆?
	iput(current->pwd);
	current->pwd=NULL;
	iput(current->root);
	current->root=NULL;
	iput(current->executable);
	current->executable=NULL;
    // 濡傛灉褰撳墠杩涚▼鏄細璇濆ご棰?leader)杩涚▼骞朵笖鍏舵湁鎺у埗缁堢锛屽垯閲婃斁璇ョ粓绔€?
	if (current->leader && current->tty >= 0)
		tty_table[current->tty].pgrp = 0;
    // 濡傛灉褰撳墠杩涚▼涓婃浣跨敤杩囧崗澶勭悊鍣紝鍒欏皢last_task_used_math缃┖銆?
	if (last_task_used_math == current)
		last_task_used_math = NULL;
    // 濡傛灉褰撳墠杩涚▼鏄痩eader杩涚▼锛屽垯缁堟璇ヤ細璇濈殑鎵€鏈夌浉鍏宠繘绋嬨€?
	if (current->leader)
		kill_session();
    // 鎶婂綋鍓嶈繘绋嬬疆涓哄兊姝荤姸鎬侊紝琛ㄦ槑褰撳墠杩涚▼宸茬粡閲婃斁浜嗚祫婧愩€傚苟淇濆瓨灏嗙敱鐖惰繘绋嬭鍙栫殑閫€鍑虹爜銆?
	current->state = TASK_ZOMBIE;
	current->exit_code = code;
    // 閫氱煡鐖惰繘绋嬶紝涔熷嵆鍚戠埗杩涚▼鍙戦€佷俊鍙稴IGCHLD - 瀛愯繘绋嬪皢鍋滄鎴栫粓姝€?
	tell_father(current->father);
	schedule();                     // 閲嶆柊璋冨害杩涚▼杩愯锛屼互璁╃埗杩涚▼澶勭悊鍍垫鍏朵粬鐨勫杽鍚庝簨瀹溿€?
    // 涓嬮潰鐨剅eturn璇彞浠呯敤浜庡幓鎺夎鍛婁俊鎭€傚洜涓鸿繖涓嚱鏁颁笉杩斿洖锛屾墍浠ヨ嫢鍦ㄥ嚱鏁板悕鍓嶅姞鍏抽敭瀛?
    // volatile锛屽氨鍙互鍛婅瘔gcc缂栬瘧鍣ㄦ湰鍑芥暟涓嶄細杩斿洖鐨勭壒娈婃儏鍐点€傝繖鏍峰彲璁ゞcc浜х敓鏇村ソ涓€浜涚殑浠ｇ爜锛?
    // 骞朵笖鍙互涓嶇敤鍐嶅啓return璇彞涔熶笉浼氫骇鐢熷亣璀﹀憡淇℃伅銆?
	return (-1);	/* just to suppress warnings */
}

//// 绯荤粺璋冪敤exit()锛岀粓姝㈣繘绋嬨€?
// 鍙傛暟error_code鏄敤鎴风▼搴忔彁渚涚殑閫€鍑虹姸鎬佷俊鎭紝鍙湁浣庡瓧鑺傛湁鏁堛€傛妸error_code宸︾Щ8bit鏄痺ait()鎴?
// waitpid()鍑芥暟鐨勮姹傘€備綆瀛楄妭涓皢鐢ㄦ潵淇濆瓨wait()鐨勭姸鎬佷俊鎭€備緥濡傦紝濡傛灉杩涚▼澶勭悊鏆傚仠鐘舵€?TASK_STOPPED),
// 閭ｄ箞鍏朵綆瀛楄妭灏辩瓑浜?x7f. wait()鎴杦aitpid()鍒╃敤杩欎簺瀹忓氨鍙互鍙栧緱瀛愯繘绋嬬殑閫€鍑虹姸鎬佺爜鎴栧瓙杩涚▼缁堟鐨勫師鍥犮€?
int sys_exit(int error_code)
{
	return do_exit((error_code&0xff)<<8);
}

//// 绯荤粺璋冪敤waipid().鎸傝捣褰撳墠杩涚▼锛岀洿鍒皃id鎸囧畾鐨勫瓙杩涚▼閫€鍑?缁堟)鎴栨敹鍒拌姹傜粓姝㈣杩涚▼鐨勪俊鍙凤紝
// 鎴栬€呮槸闇€瑕佽皟鐢ㄤ竴涓俊鍙峰彞鏌?淇″彿澶勭悊绋嬪簭)銆傚鏋減id鎵€鎸囧悜鐨勫瓙杩涚▼鏃╁凡閫€鍑?宸叉垚鎵€璋撶殑鍍垫杩涚▼)锛?
// 鍒欐湰璋冪敤灏嗙珛鍒昏繑鍥炪€傚瓙杩涚▼浣跨敤鐨勬墍鏈夎祫婧愬皢閲婃斁銆?
// 濡傛灉pid > 0锛岃〃绀虹瓑寰呰繘绋嬪彿绛変簬pid鐨勫瓙杩涚▼銆?
// 濡傛灉pid = 0, 琛ㄧず绛夊緟杩涚▼缁勫彿绛変簬褰撳墠杩涚▼缁勫彿鐨勪换浣曞瓙杩涚▼銆?
// 濡傛灉pid < -1,琛ㄧず绛夊緟杩涚▼缁勫彿绛変簬pid缁濆鍊肩殑浠讳綍瀛愯繘绋嬨€?
// 濡傛灉pid = -1,琛ㄧず绛夊緟浠讳綍瀛愯繘绋嬨€?
// 濡?options = WUNTRACED,琛ㄧず濡傛灉瀛愯繘绋嬫槸鍋滄鐨勶紝涔熼┈涓婅繑鍥?鏃犻』璺熻釜)
// 鑻?options = WNOHANG, 琛ㄧず濡傛灉娌℃湁瀛愯繘绋嬮€€鍑烘垨缁堟灏遍┈涓婅繑鍥炪€?
// 濡傛灉杩斿洖鐘舵€佹寚閽?stat_addr涓嶄负绌猴紝鍒欏氨灏嗙姸鎬佷俊鎭繚瀛樺埌閭ｉ噷銆?
// 鍙傛暟pid鏄繘绋嬪彿锛?stat_addr鏄繚瀛樼姸鎬佷俊鎭綅缃殑鎸囬拡锛宱ptions鏄痺aitpid閫夐」銆?
int sys_waitpid(pid_t pid,unsigned long * stat_addr, int options)
{
	int flag, code;             // flag鏍囧織鐢ㄤ簬鍚庨潰琛ㄧず鎵€閫夊嚭鐨勫瓙杩涚▼澶勪簬灏辩华鎴栫潯鐪犳€併€?
	struct task_struct ** p;

	verify_area(stat_addr,4);
repeat:
	flag=0;
    // 浠庝换鍔℃暟缁勬湯绔紑濮嬫壂鎻忔墍鏈変换鍔★紝璺宠繃绌洪」銆佹湰杩涚▼椤逛互鍙婇潪褰撳墠杩涚▼鐨勫瓙杩涚▼椤广€?
	for(p = &LAST_TASK ; p > &FIRST_TASK ; --p) {
		if (!*p || *p == current)
			continue;
		if ((*p)->father != current->pid)
			continue;
        // 姝ゆ椂鎵弿閫夋嫨鍒扮殑杩涚▼p鑲畾鏄綋鍓嶈繘绋嬬殑瀛愯繘绋嬨€?
        // 濡傛灉绛夊緟鐨勫瓙杩涚▼鍙穚id>0锛屼絾涓庤鎵弿瀛愯繘绋媝鐨刾id涓嶇浉绛夛紝璇存槑瀹冩槸褰撳墠杩涚▼鍙﹀鐨?
        // 瀛愯繘绋嬶紝浜庢槸璺宠繃璇ヨ繘绋嬶紝鎺ョ潃鎵弿涓嬩竴涓繘绋嬨€?
		if (pid>0) {
			if ((*p)->pid != pid)
				continue;
        // 鍚﹀垯锛屽鏋滄寚瀹氱瓑寰呰繘绋嬬殑pid=0,琛ㄧず姝ｅ湪绛夊緟杩涚▼缁勫彿绛変簬褰撳墠杩涚▼缁勫彿鐨勪换浣曞瓙杩涚▼銆?
        // 濡傛灉姝ゆ椂琚壂鎻忚繘绋媝鐨勮繘绋嬬粍鍙蜂笌褰撳墠杩涚▼鐨勭粍鍙蜂笉绛夛紝鍒欒烦杩囥€?
		} else if (!pid) {
			if ((*p)->pgrp != current->pgrp)
				continue;
        // 鍚﹀垯锛屽鏋滄寚瀹氱殑pid < -1,琛ㄧず姝ｅ湪绛夊緟杩涚▼缁勫彿绛変簬pid缁濆鍊肩殑浠讳綍瀛愯繘绋嬨€傚鏋滄鏃?
        // 琚壂鎻忚繘绋媝鐨勭粍鍙蜂笌pid鐨勭粷瀵瑰€间笉绛夛紝鍒欒烦杩囥€?
		} else if (pid != -1) {
			if ((*p)->pgrp != -pid)
				continue;
		}
        // 濡傛灉鍓?涓pid鐨勫垽鏂兘涓嶇鍚堬紝鍒欒〃绀哄綋鍓嶈繘绋嬫鍦ㄧ瓑寰呭叾浠讳綍瀛愯繘绋嬶紝涔熷嵆pid=-1鐨勬儏鍐碉紝
        // 姝ゆ椂鎵€閫夋嫨鍒扮殑杩涚▼p鎴栬€呮槸鍏惰繘绋嬪彿绛変簬鎸囧畾pid锛屾垨鑰呮槸褰撳墠杩涚▼缁勪腑鐨勪换浣曞瓙杩涚▼锛屾垨鑰?
        // 鏄繘绋嬪彿绛変簬鎸囧畾pid缁濆鍊肩殑瀛愯繘绋嬶紝鎴栬€呮槸浠讳綍瀛愯繘绋?姝ゆ椂鎸囧畾鐨刾id绛変簬-1).鎺ヤ笅鏉ユ牴鎹?
        // 杩欎釜瀛愯繘绋媝鎵€澶勭殑鐘舵€佹潵澶勭悊銆?
		switch ((*p)->state) {
            // 瀛愯繘绋媝澶勪簬鍋滄鐘舵€佹椂锛屽鏋滄鏃禬UNTRACED鏍囧織娌℃湁缃綅锛岃〃绀虹▼搴忔棤椤荤珛鍒昏繑鍥烇紝浜庢槸
            // 缁х画鎵弿澶勭悊鍏朵粬杩涚▼銆傚鏋淲UNTRACED缃綅锛屽垯鎶婄姸鎬佷俊鎭?x7f鏀惧叆*stat_addr锛屽苟绔嬪埢
            // 杩斿洖瀛愯繘绋嬪彿pid.杩欓噷0x7f琛ㄧず鐨勮繑鍥炵姸鎬佹槸wifstopped锛堬級瀹忎负鐪熴€?
			case TASK_STOPPED:
				if (!(options & WUNTRACED))
					continue;
				put_fs_long(0x7f,stat_addr);
				return (*p)->pid;
            // 濡傛灉瀛愯繘绋媝澶勪簬鍍垫鐘舵€侊紝鍒欓鍏堟妸瀹冨湪鐢ㄦ埛鎬佸拰鍐呮牳鎬佽繍琛岀殑鏃堕棿鍒嗗埆绱鍒板綋鍓嶈繘绋?
            // (鐖惰繘绋?涓紝鐒跺悗鍙栧嚭瀛愯繘绋嬬殑pid鍜岄€€鍑虹爜锛屽苟閲婃斁璇ュ瓙杩涚▼銆傛渶鍚庤繑鍥炲瓙杩涚▼鐨勯€€鍑虹爜鍜宲id.
			case TASK_ZOMBIE:
				current->cutime += (*p)->utime;
				current->cstime += (*p)->stime;
				flag = (*p)->pid;                   // 涓存椂淇濆瓨瀛愯繘绋媝id
				code = (*p)->exit_code;             // 鍙栧瓙杩涚▼鐨勯€€鍑虹爜
				release(*p);                        // 閲婃斁璇ュ瓙杩涚▼
				put_fs_long(code,stat_addr);        // 缃姸鎬佷俊鎭负閫€鍑虹爜鍊?
				return flag;                        // 杩斿洖瀛愯繘绋嬬殑pid
            // 濡傛灉杩欎釜瀛愯繘绋媝鐨勭姸鎬佹棦涓嶆槸鍋滄涔熶笉鏄兊姝伙紝閭ｄ箞灏辩疆flag=1,琛ㄧず鎵惧埌杩囦竴涓鍚?
            // 瑕佹眰鐨勫瓙杩涚▼锛屼絾鏄畠澶勪簬杩愯鎬佹垨鐫＄湢鎬併€?
			default:
				flag=1;
				continue;
		}
	}
    // 鍦ㄤ笂闈㈠浠诲姟鏁扮粍鎵弿缁撴潫鍚庯紝濡傛灉flag琚疆浣嶏紝璇存槑鏈夌鍚堢瓑寰呰姹傜殑瀛愯繘绋嬪苟娌℃湁澶勪簬閫€鍑烘垨
    // 鍍垫鐘舵€併€傚鏋滄鏃跺凡璁剧疆WNOHANG閫夐」(琛ㄧず鑻ユ病鏈夊瓙杩涚▼澶勪簬閫€鍑烘垨缁堟鎬佸氨绔嬪埢杩斿洖)锛屽氨
    // 绔嬪埢杩斿洖0锛岄€€鍑恒€傚惁鍒欐妸褰撳墠杩涚▼缃负鍙腑鏂瓑寰呯姸鎬佸苟閲嶆柊鎵ц璋冨害銆傚綋鍙堝紑濮嬫墽琛屾湰杩涚▼鏃讹紝
    // 濡傛灉鏈繘绋嬫病鏈夋敹鍒伴櫎SIGCHLD浠ュ鐨勪俊鍙凤紝鍒欒繕鏄噸澶嶅鐞嗐€傚惁鍒欙紝杩斿洖鍑洪敊鐮佲€樹腑鏂郴缁熻皟鐢ㄢ€?
    // 骞堕€€鍑恒€傞拡瀵硅繖涓嚭閿欏彿鐢ㄦ埛绋嬪簭搴旇鍐嶇户缁皟鐢ㄦ湰鍑芥暟绛夊緟瀛愯繘绋嬨€?
	if (flag) {
		if (options & WNOHANG)                  // options = WNOHANG,鍒欑珛鍒昏繑鍥炪€?
			return 0;
		current->state=TASK_INTERRUPTIBLE;      // 缃綋鍓嶈繘绋嬩负鍙腑鏂瓑寰呮€?
		schedule();                             // 閲嶆柊璋冨害銆?
		if (!(current->signal &= ~(1<<(SIGCHLD-1))))
			goto repeat;
		else
			return -EINTR;                      // 杩斿洖鍑洪敊鐮?涓柇鐨勭郴缁熻皟鐢?
	}
    // 鑻ユ病鏈夋壘鍒扮鍚堣姹傜殑瀛愯繘绋嬶紝鍒欒繑鍥炲嚭閿欑爜(瀛愯繘绋嬩笉瀛樺湪)銆?
	return -ECHILD;
}


