from __future__ import annotations

import os
import queue
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk

from .config import AppConfig, load_config, save_config
from .processor import PassportProcessor, ProcessResult


class SettingsWindow:
    def __init__(self) -> None:
        self.cfg = load_config()
        self.root = tk.Tk()
        self.root.title("护照扫描件自动命名 - 设置")
        self.root.resizable(False, False)

        self.output_var = tk.StringVar(value=self.cfg.output_dir)
        self.failed_var = tk.StringVar(value=self.cfg.failed_dir)
        self.mode_var = tk.StringVar(value=self.cfg.mode)
        self.template_var = tk.StringVar(value=self.cfg.filename_template)
        self.prefer_cn_var = tk.BooleanVar(value=self.cfg.prefer_chinese)
        self.conf_var = tk.StringVar(value=str(self.cfg.min_confidence))

        self._build()

    def _build(self) -> None:
        frame = ttk.Frame(self.root, padding=16)
        frame.grid(row=0, column=0, sticky="nsew")

        ttk.Label(frame, text="输出目录").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Entry(frame, textvariable=self.output_var, width=52).grid(row=0, column=1, padx=8)
        ttk.Button(frame, text="选择", command=lambda: self._pick(self.output_var)).grid(row=0, column=2)

        ttk.Label(frame, text="失败目录").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Entry(frame, textvariable=self.failed_var, width=52).grid(row=1, column=1, padx=8)
        ttk.Button(frame, text="选择", command=lambda: self._pick(self.failed_var)).grid(row=1, column=2)

        ttk.Label(frame, text="文件处理").grid(row=2, column=0, sticky="w", pady=5)
        modes = ttk.Frame(frame)
        modes.grid(row=2, column=1, sticky="w")
        ttk.Radiobutton(modes, text="复制（推荐）", variable=self.mode_var, value="copy").pack(side="left")
        ttk.Radiobutton(modes, text="移动", variable=self.mode_var, value="move").pack(side="left", padx=12)

        ttk.Label(frame, text="文件名模板").grid(row=3, column=0, sticky="w", pady=5)
        ttk.Entry(frame, textvariable=self.template_var, width=52).grid(row=3, column=1, padx=8, sticky="w")
        ttk.Label(frame, text="必须包含 {name}").grid(row=3, column=2, sticky="w")

        ttk.Label(frame, text="最低置信度").grid(row=4, column=0, sticky="w", pady=5)
        ttk.Entry(frame, textvariable=self.conf_var, width=10).grid(row=4, column=1, padx=8, sticky="w")

        ttk.Checkbutton(frame, text="中文姓名优先，MRZ 英文姓名兜底", variable=self.prefer_cn_var).grid(
            row=5, column=1, sticky="w", padx=8, pady=8
        )

        info = "使用方法：保存设置后，将一个或多个 PDF/JPG/PNG/TIFF 拖到程序 EXE 上。"
        ttk.Label(frame, text=info).grid(row=6, column=0, columnspan=3, sticky="w", pady=(8, 12))

        buttons = ttk.Frame(frame)
        buttons.grid(row=7, column=0, columnspan=3, sticky="e")
        ttk.Button(buttons, text="打开输出目录", command=self._open_output).pack(side="left", padx=5)
        ttk.Button(buttons, text="保存", command=self._save).pack(side="left", padx=5)
        ttk.Button(buttons, text="关闭", command=self.root.destroy).pack(side="left")

    def _pick(self, var: tk.StringVar) -> None:
        selected = filedialog.askdirectory(initialdir=var.get() or str(Path.home()))
        if selected:
            var.set(selected)

    def _open_output(self) -> None:
        path = Path(self.output_var.get()).expanduser()
        path.mkdir(parents=True, exist_ok=True)
        try:
            os.startfile(path)  # type: ignore[attr-defined]
        except Exception:
            messagebox.showinfo("输出目录", str(path))

    def _save(self) -> None:
        try:
            cfg = AppConfig(
                output_dir=self.output_var.get().strip(),
                failed_dir=self.failed_var.get().strip(),
                mode=self.mode_var.get(),
                filename_template=self.template_var.get().strip(),
                prefer_chinese=bool(self.prefer_cn_var.get()),
                min_confidence=float(self.conf_var.get()),
            )
            save_config(cfg)
            messagebox.showinfo("保存成功", "设置已保存。现在可以把护照扫描件拖到程序上。")
        except Exception as exc:
            messagebox.showerror("设置错误", str(exc))

    def run(self) -> None:
        self.root.mainloop()


class ProcessingWindow:
    """Show live batch progress while OCR runs on a background worker thread."""

    def __init__(self, paths: list[str], cfg: AppConfig) -> None:
        self.paths = paths
        self.cfg = cfg
        self.total = len(paths)
        self.completed = 0
        self.success = 0
        self.failed = 0
        self.result_code = 0
        self.running = True
        self.started_at = time.monotonic()
        self.events: queue.Queue[tuple] = queue.Queue()

        self.root = tk.Tk()
        self.root.title("护照自动命名 - 处理进度")
        self.root.geometry("780x560")
        self.root.minsize(680, 480)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self.status_var = tk.StringVar(value="准备初始化 OCR…")
        self.current_var = tk.StringVar(value="当前：等待开始")
        self.count_var = tk.StringVar(value=self._count_text())
        self.elapsed_var = tk.StringVar(value="耗时：0 秒")

        self._build()
        self.root.after(100, self._start_worker)
        self.root.after(100, self._poll_events)
        self.root.after(1000, self._update_elapsed)
        self.root.after(250, self.root.lift)

    def _build(self) -> None:
        outer = ttk.Frame(self.root, padding=18)
        outer.pack(fill="both", expand=True)

        ttk.Label(outer, text="护照扫描件自动命名", font=("Microsoft YaHei UI", 14, "bold")).pack(anchor="w")
        ttk.Label(outer, textvariable=self.status_var).pack(anchor="w", pady=(8, 3))
        ttk.Label(outer, textvariable=self.current_var).pack(anchor="w", pady=(0, 10))

        ttk.Label(outer, text="总体进度").pack(anchor="w")
        self.overall_bar = ttk.Progressbar(outer, mode="determinate", maximum=max(1, self.total), value=0)
        self.overall_bar.pack(fill="x", pady=(4, 8))

        meta = ttk.Frame(outer)
        meta.pack(fill="x", pady=(0, 10))
        ttk.Label(meta, textvariable=self.count_var).pack(side="left")
        ttk.Label(meta, textvariable=self.elapsed_var).pack(side="right")

        ttk.Label(outer, text="当前文件活动").pack(anchor="w")
        self.activity_bar = ttk.Progressbar(outer, mode="indeterminate")
        self.activity_bar.pack(fill="x", pady=(4, 12))

        ttk.Label(outer, text="处理记录").pack(anchor="w")
        self.log = scrolledtext.ScrolledText(outer, height=16, wrap="word", state="disabled")
        self.log.pack(fill="both", expand=True, pady=(4, 12))

        buttons = ttk.Frame(outer)
        buttons.pack(fill="x")
        ttk.Button(buttons, text="打开输出目录", command=self._open_output).pack(side="left")
        self.close_button = ttk.Button(buttons, text="处理中…", command=self.root.destroy, state="disabled")
        self.close_button.pack(side="right")

    def _start_worker(self) -> None:
        thread = threading.Thread(target=self._worker, name="passport-ocr-worker", daemon=True)
        thread.start()

    def _worker(self) -> None:
        self.events.put(("status", "正在初始化 OCR 模型，请稍候…"))
        try:
            processor = PassportProcessor(self.cfg)
        except Exception as exc:
            self.events.put(("fatal", f"OCR 初始化失败：{exc}"))
            return

        self.events.put(("status", "OCR 初始化完成，开始处理文件。"))
        for index, raw in enumerate(self.paths, start=1):
            source = Path(raw)
            self.events.put(("started", index, source))
            result = processor.process(source)
            self.events.put(("result", index, result))

        self.events.put(("done",))

    def _poll_events(self) -> None:
        while True:
            try:
                event = self.events.get_nowait()
            except queue.Empty:
                break
            self._handle_event(event)

        if self.running or not self.events.empty():
            self.root.after(100, self._poll_events)

    def _handle_event(self, event: tuple) -> None:
        kind = event[0]
        if kind == "status":
            self.status_var.set(str(event[1]))
            return

        if kind == "started":
            index: int = event[1]
            source: Path = event[2]
            self.current_var.set(f"当前：{source.name}")
            self.status_var.set(f"正在识别第 {index}/{self.total} 个文件…")
            self.overall_bar["value"] = index - 1
            self.activity_bar.start(12)
            self._append_log(f"▶ [{index}/{self.total}] {source.name}\n")
            return

        if kind == "result":
            result: ProcessResult = event[2]
            self.activity_bar.stop()
            self.completed += 1
            self.overall_bar["value"] = self.completed

            if result.success:
                self.success += 1
                detected = result.name_result.name if result.name_result else ""
                destination = result.destination.name if result.destination else ""
                self._append_log(f"✓ {result.source.name} → {destination}    姓名：{detected}\n")
            else:
                self.failed += 1
                self._append_log(f"✗ {result.source.name}    {result.message}\n")

            self.count_var.set(self._count_text())
            return

        if kind == "fatal":
            self.activity_bar.stop()
            self.running = False
            self.result_code = 2
            self.status_var.set(str(event[1]))
            self.current_var.set("当前：初始化失败")
            self._append_log(f"✗ {event[1]}\n")
            self._enable_close()
            return

        if kind == "done":
            self.activity_bar.stop()
            self.running = False
            self.result_code = 0 if self.failed == 0 else 1
            self.overall_bar["value"] = self.total
            self.current_var.set("当前：全部处理完成")
            self.status_var.set(f"处理完成：成功 {self.success} 个，失败 {self.failed} 个。")
            self.count_var.set(self._count_text())
            self._append_log("\n处理完成。\n")
            self._enable_close()
            self.root.bell()

    def _count_text(self) -> str:
        return f"总计 {self.total}  |  已完成 {self.completed}  |  成功 {self.success}  |  失败 {self.failed}"

    def _append_log(self, text: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", text)
        self.log.see("end")
        self.log.configure(state="disabled")

    def _update_elapsed(self) -> None:
        elapsed = int(time.monotonic() - self.started_at)
        self.elapsed_var.set(f"耗时：{elapsed} 秒")
        if self.running:
            self.root.after(1000, self._update_elapsed)

    def _enable_close(self) -> None:
        self.close_button.configure(text="关闭", state="normal")

    def _open_output(self) -> None:
        path = Path(self.cfg.output_dir).expanduser()
        path.mkdir(parents=True, exist_ok=True)
        try:
            os.startfile(path)  # type: ignore[attr-defined]
        except Exception:
            messagebox.showinfo("输出目录", str(path))

    def _on_close(self) -> None:
        if self.running:
            self.root.bell()
            self.status_var.set("正在处理中，请等待当前任务完成后再关闭。")
            return
        self.root.destroy()

    def run(self) -> int:
        self.root.mainloop()
        return self.result_code
