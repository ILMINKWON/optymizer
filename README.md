# System Optimizer

A lightweight Python app that automatically detects high-load processes on boot and lets you terminate them with one click — keeping your system running smoothly from the moment it starts.

---

## Features

- Detects CPU and memory-heavy processes on startup
- Classifies each process as **Warning** or **Danger** based on thresholds
- Shows overall system memory status as a banner
- Select processes to terminate via checkboxes
- Gracefully handles permission errors (non-root processes)

---

## File Structure

```
system-optimizer/
├── optimizer.py   # Main program
└── README.md
```

---

## Thresholds

### Per-Process

| Level | CPU | Memory |
|---|---|---|
| Warning | >= 30% | >= 500 MB |
| Danger  | >= 50% | >= 1,024 MB (1 GB) |

### Overall System Memory

| Level | Usage | Reason |
|---|---|---|
| Warning | >= 75% | Free memory drops below 25% — swap may begin, causing sluggishness |
| Danger  | >= 85% | Swap is actively occurring — disk I/O bottleneck causes severe lag |

> **What is swap?** When RAM runs out, the OS uses disk space as temporary memory. Since disks are 100x slower than RAM, heavy swapping is one of the most common causes of noticeable lag.

---

## Setup — Autostart on Boot

**1. Register (run once)**
```bash
bash setup_autostart.sh
```

This creates `~/.config/autostart/system-optimizer.desktop`. Linux reads this folder on every boot and launches `optimizer.py` automatically.

**2. Done.** The optimizer runs on every boot from now on.

---

## Usage

1. The app opens automatically on boot and scans running processes
2. A loading window appears briefly while scanning
3. If no heavy processes are found → a "System OK" popup appears and closes
4. If heavy processes are found → a window lists them with severity labels
5. Check the ones you want to terminate → click **"Optimize"**

---

## Warning Labels

| Label | Color | Meaning |
|---|---|---|
| `[Warning]` | Orange | May cause sluggishness |
| `[Danger]`  | Red    | Serious performance degradation |

---

## Requirements

- Python 3.x
- `psutil` (`pip install psutil`)
- Linux with GNOME (or any desktop environment supporting `~/.config/autostart`)
