import psutil
import tkinter as tk
from tkinter import messagebox
import time

# 주의 기준
CPU_WARN = 30.0     # CPU 30% 이상
MEM_WARN = 500      # 메모리 500MB 이상
MEM_TOTAL_WARN = 75 # 전체 메모리 사용률 75% 이상

# 위험 기준
CPU_DANGER = 50.0    # CPU 50% 이상
MEM_DANGER = 1024    # 메모리 1GB 이상
MEM_TOTAL_DANGER = 85  # 전체 메모리 사용률 85% 이상

# 절대 종료하면 안 되는 시스템 프로세스
SYSTEM_PROCESSES = {
    'systemd', 'kthreadd', 'init', 'kworker', 'ksoftirqd', 'migration',
    'rcu_sched', 'watchdog', 'sshd', 'dbus-daemon', 'gnome-shell',
    'Xorg', 'Xwayland', 'python3', 'optimizer.py', 'launcher.py'
}


def get_system_status():
    mem = psutil.virtual_memory()
    usage_pct = mem.percent
    if usage_pct >= MEM_TOTAL_DANGER:
        level = 'danger'
        msg = f"전체 메모리 사용률 {usage_pct:.1f}% — 심각한 성능 저하 원인입니다."
    elif usage_pct >= MEM_TOTAL_WARN:
        level = 'warn'
        msg = f"전체 메모리 사용률 {usage_pct:.1f}% — 원활하지 않을 수 있습니다."
    else:
        level = 'ok'
        msg = f"전체 메모리 사용률 {usage_pct:.1f}% — 양호합니다."
    return {'level': level, 'msg': msg, 'usage_pct': usage_pct}


def classify(cpu, mem_mb):
    if cpu >= CPU_DANGER or mem_mb >= MEM_DANGER:
        return 'danger'
    if cpu >= CPU_WARN or mem_mb >= MEM_WARN:
        return 'warn'
    return None


def get_heavy_processes():
    # 첫 번째 호출로 CPU 측정 초기화
    for proc in psutil.process_iter():
        try:
            proc.cpu_percent()
        except Exception:
            pass

    time.sleep(1.5)

    heavy = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
        try:
            info = proc.info
            name = info['name'] or ''
            cpu = info['cpu_percent'] or 0.0
            mem_mb = info['memory_info'].rss / (1024 * 1024) if info['memory_info'] else 0

            if name.lower() in SYSTEM_PROCESSES:
                continue

            level = classify(cpu, mem_mb)
            if level:
                heavy.append({
                    'pid': info['pid'],
                    'name': name,
                    'cpu': round(cpu, 1),
                    'mem_mb': round(mem_mb, 1),
                    'level': level,
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    return sorted(heavy, key=lambda x: x['mem_mb'], reverse=True)


LEVEL_COLOR = {'danger': '#e53935', 'warn': '#FF8C00'}
LEVEL_LABEL = {'danger': '[위험]', 'warn': '[주의]'}
LEVEL_DESC  = {
    'danger': '심각한 성능 저하 원인입니다.',
    'warn':   '원활하지 않을 수 있습니다.',
}


class OptimizerApp:
    def __init__(self, root, processes, sys_status):
        self.root = root
        self.root.title("시스템 최적화")
        self.root.geometry("620x460")
        self.root.resizable(False, False)
        self.processes = processes
        self.sys_status = sys_status
        self.vars = []
        self.build_ui()

    def build_ui(self):
        tk.Label(self.root, text="시스템 최적화", font=("Arial", 14, "bold")).pack(pady=10)

        # 전체 메모리 상태 배너
        s = self.sys_status
        banner_color = LEVEL_COLOR.get(s['level'], '#2e7d32')
        banner_text = s['msg']
        tk.Label(self.root, text=banner_text, bg=banner_color, fg="white",
                 font=("Arial", 10, "bold"), pady=5).pack(fill=tk.X, padx=20)

        tk.Label(self.root, text="부하가 높은 프로세스가 감지됐습니다. 종료할 항목을 선택하세요.",
                 fg="gray").pack(pady=4)

        # 헤더
        header = tk.Frame(self.root)
        header.pack(fill=tk.X, padx=20, pady=(4, 0))
        tk.Label(header, text="선택", width=5).pack(side=tk.LEFT)
        tk.Label(header, text="상태", width=8).pack(side=tk.LEFT)
        tk.Label(header, text="프로세스명", width=18, anchor="w").pack(side=tk.LEFT)
        tk.Label(header, text="CPU %", width=8).pack(side=tk.LEFT)
        tk.Label(header, text="메모리(MB)", width=11).pack(side=tk.LEFT)
        tk.Label(header, text="경고", width=22, anchor="w").pack(side=tk.LEFT)

        tk.Frame(self.root, height=1, bg="gray").pack(fill=tk.X, padx=20)

        # 프로세스 목록
        list_frame = tk.Frame(self.root)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20)

        for proc in self.processes:
            var = tk.BooleanVar(value=True)
            color = LEVEL_COLOR.get(proc['level'], 'black')
            row = tk.Frame(list_frame)
            row.pack(fill=tk.X, pady=2)
            tk.Checkbutton(row, variable=var, width=3).pack(side=tk.LEFT)
            tk.Label(row, text=LEVEL_LABEL[proc['level']], width=8,
                     fg=color, font=("Arial", 9, "bold")).pack(side=tk.LEFT)
            tk.Label(row, text=proc['name'], width=18, anchor="w").pack(side=tk.LEFT)
            tk.Label(row, text=f"{proc['cpu']}%", width=8, fg=color).pack(side=tk.LEFT)
            tk.Label(row, text=f"{proc['mem_mb']}", width=11, fg=color).pack(side=tk.LEFT)
            tk.Label(row, text=LEVEL_DESC[proc['level']], fg=color,
                     font=("Arial", 8)).pack(side=tk.LEFT)
            self.vars.append((var, proc))

        # 버튼
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=12)
        tk.Button(btn_frame, text="최적화 (선택 종료)", command=self.optimize,
                  bg="#e53935", fg="white", width=16).pack(side=tk.LEFT, padx=8)
        tk.Button(btn_frame, text="그냥 닫기", command=self.root.destroy,
                  width=12).pack(side=tk.LEFT, padx=8)

    def optimize(self):
        selected = [(var, proc) for var, proc in self.vars if var.get()]
        if not selected:
            messagebox.showwarning("알림", "선택된 프로세스가 없습니다.")
            return

        killed, failed = [], []
        for _, proc in selected:
            try:
                p = psutil.Process(proc['pid'])
                p.terminate()
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
    # 로딩 창
    loading = tk.Tk()
    loading.title("시스템 분석 중...")
    loading.geometry("300x80")
    loading.resizable(False, False)
    tk.Label(loading, text="부하 프로세스 분석 중...", font=("Arial", 11)).pack(expand=True)
    loading.update()

    processes = get_heavy_processes()
    sys_status = get_system_status()
    loading.destroy()

    if not processes:
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo("시스템 최적화", f"부하가 높은 프로세스가 없습니다.\n{sys_status['msg']}")
        root.destroy()
        return

    root = tk.Tk()
    OptimizerApp(root, processes, sys_status)
    root.mainloop()


if __name__ == "__main__":
    main()
