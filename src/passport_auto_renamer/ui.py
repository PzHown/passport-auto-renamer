from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .config import AppConfig, load_config, save_config


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
            import os
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
