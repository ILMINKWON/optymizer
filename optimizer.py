import psutil
import tkinter as tk
from tkinter import messagebox, ttk
import time

# 주의 기준
CPU_WARN = 30.0
MEM_WARN = 500
MEM_TOTAL_WARN = 75

# 위험 기준
CPU_DANGER = 50.0
MEM_DANGER = 1024
MEM_TOTAL_DANGER = 85

SYSTEM_PROCESSES = {
    'systemd', 'kthreadd', 'init', 'kworker', 'ksoftirqd', 'migration',
    'rcu_sched', 'watchdog', 'sshd', 'dbus-daemon', 'gnome-shell',
    'Xorg', 'Xwayland', 'python3', 'optimizer.py', 'launcher.py'
}

LEVEL_COLOR = {'danger': '#e53935', 'warn': '#FF8C00', 'ok': '#2e7d32'}
LEVEL_LABEL = {'danger': '[위험]', 'warn': '[주의]', 'ok': ''}


def get_system_status():
    mem = psutil.virtual_memory()
    pct = mem.percent
    used_gb = mem.used / (1024 ** 3)
    total_gb = mem.total / (1024 ** 3)
    if pct >= MEM_TOTAL_DANGER:
        level = 'danger'
        msg = f"전체 메모리 {used_gb:.1f}GB / {total_gb:.1f}GB ({pct:.1f}%) — 심각한 성능 저하 원인입니다."
    elif pct >= MEM_TOTAL_WARN:
        level = 'warn'
        msg = f"전체 메모리 {used_gb:.1f}GB / {total_gb:.1f}GB ({pct:.1f}%) — 원활하지 않을 수 있습니다."
    else:
        level = 'ok'
        msg = f"전체 메모리 {used_gb:.1f}GB / {total_gb:.1f}GB ({pct:.1f}%) — 양호합니다."
    return {'level': level, 'msg': msg}


def classify(cpu, mem_mb):
    if cpu >= CPU_DANGER or mem_mb >= MEM_DANGER:
        return 'danger'
    if cpu >= CPU_WARN or mem_mb >= MEM_WARN:
        return 'warn'
    return 'ok'


def get_all_processes():
    for proc in psutil.process_iter():
        try:
            proc.cpu_percent()
        except Exception:
            pass

    time.sleep(1.5)

    all_procs = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
        try:
            info = proc.info
            name = info['name'] or ''
            if name.lower() in SYSTEM_PROCESSES:
                continue
            cpu = info['cpu_percent'] or 0.0
            mem_mb = info['memory_info'].rss / (1024 * 1024) if info['memory_info'] else 0
            if mem_mb < 1:
                continue
            level = classify(cpu, mem_mb)
            all_procs.append({
                'pid': info['pid'],
                'name': name,
                'cpu': round(cpu, 1),
                'mem_mb': round(mem_mb, 1),
                'level': level,
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    return sorted(all_procs, key=lambda x: x['mem_mb'], reverse=True)


class OptimizerApp:
    def __init__(self, root, all_procs, sys_status):
        self.root = root
        self.root.title("시스템 최적화")
        self.root.geometry("680x520")
        self.root.resizable(False, False)
        self.all_procs = all_procs
        self.heavy = [p for p in all_procs if p['level'] != 'ok']
        self.sys_status = sys_status
        self.vars = {}
        self.build_ui()

    def build_ui(self):
        tk.Label(self.root, text="시스템 최적화", font=("Arial", 14, "bold")).pack(pady=8)

        # 전체 메모리 배너
        s = self.sys_status
        tk.Label(self.root, text=s['msg'],
                 bg=LEVEL_COLOR[s['level']], fg="white",
                 font=("Arial", 10, "bold"), pady=5).pack(fill=tk.X, padx=20)

        # 탭
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=8)

        # 탭1: 부하 프로세스
        tab1 = tk.Frame(notebook)
        notebook.add(tab1, text=f"  부하 프로세스 ({len(self.heavy)}개)  ")
        self.build_process_tab(tab1, self.heavy, show_checkbox=True)

        # 탭2: 전체 목록 (상위 20개)
        tab2 = tk.Frame(notebook)
        notebook.add(tab2, text=f"  전체 목록 (상위 {min(20, len(self.all_procs))}개)  ")
        self.build_process_tab(tab2, self.all_procs[:20], show_checkbox=False)

        # 버튼
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=8)
        tk.Button(btn_frame, text="선택 프로세스 종료", command=self.optimize,
                  bg="#e53935", fg="white", width=16).pack(side=tk.LEFT, padx=8)
        tk.Button(btn_frame, text="닫기", command=self.root.destroy,
                  width=10).pack(side=tk.LEFT, padx=8)

    def build_process_tab(self, parent, procs, show_checkbox):
        # 헤더
        header = tk.Frame(parent)
        header.pack(fill=tk.X, padx=8, pady=(6, 2))
        if show_checkbox:
            tk.Label(header, text="선택", width=5).pack(side=tk.LEFT)
        tk.Label(header, text="상태", width=8).pack(side=tk.LEFT)
        tk.Label(header, text="프로세스명", width=20, anchor="w").pack(side=tk.LEFT)
        tk.Label(header, text="CPU %", width=8).pack(side=tk.LEFT)
        tk.Label(header, text="메모리(MB)", width=12).pack(side=tk.LEFT)

        tk.Frame(parent, height=1, bg="gray").pack(fill=tk.X, padx=8)

        # 스크롤 가능한 목록
        canvas = tk.Canvas(parent, height=300)
        scrollbar = tk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        frame = tk.Frame(canvas)

        frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        if not procs:
            tk.Label(frame, text="부하가 높은 프로세스가 없습니다.", fg="gray", pady=20).pack()
            return

        for proc in procs:
            color = LEVEL_COLOR.get(proc['level'], 'black') if proc['level'] != 'ok' else 'black'
            row = tk.Frame(frame)
            row.pack(fill=tk.X, pady=1)

            if show_checkbox:
                var = tk.BooleanVar(value=proc['level'] != 'ok')
                tk.Checkbutton(row, variable=var, width=3).pack(side=tk.LEFT)
                self.vars[proc['pid']] = (var, proc)

            label = LEVEL_LABEL.get(proc['level'], '')
            tk.Label(row, text=label, width=8, fg=color,
                     font=("Arial", 9, "bold")).pack(side=tk.LEFT)
            tk.Label(row, text=proc['name'], width=20, anchor="w").pack(side=tk.LEFT)
            tk.Label(row, text=f"{proc['cpu']}%", width=8, fg=color).pack(side=tk.LEFT)
            tk.Label(row, text=f"{proc['mem_mb']}", width=12, fg=color).pack(side=tk.LEFT)

    def optimize(self):
        selected = [(var, proc) for var, proc in self.vars.values() if var.get()]
        if not selected:
            messagebox.showwarning("알림", "선택된 프로세스가 없습니다.")
            return

        killed, failed = [], []
        for _, proc in selected:
            try:
                psutil.Process(proc['pid']).terminate()
                killed.append(proc['name'])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                failed.append(proc['name'])

        msg = ""
        if killed:
            msg += f"종료 완료: {', '.join(killed)}\n"
        if failed:
            msg += f"권한 부족으로 종료 실패: {', '.join(failed)}"

        messagebox.showinfo("최적화 완료", msg.strip())
        self.root.destroy()


def main():
    loading = tk.Tk()
    loading.title("시스템 분석 중...")
    loading.geometry("300x80")
    loading.resizable(False, False)
    tk.Label(loading, text="프로세스 분석 중...", font=("Arial", 11)).pack(expand=True)
    loading.update()

    all_procs = get_all_processes()
    sys_status = get_system_status()
    loading.destroy()

    root = tk.Tk()
    OptimizerApp(root, all_procs, sys_status)
    root.mainloop()


if __name__ == "__main__":
    main()
