"""Dialog windows for the GUI."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from typing import TYPE_CHECKING

from ed_auto_mission.core.types import MissionRule
from ed_auto_mission.core.config import AppConfig
from ed_auto_mission.core.category_navigator import CategoryNavigator

if TYPE_CHECKING:
    pass

AVAILABLE_CATEGORIES = ["all", "combat", "transport", "freelance", "operations", "support", "thargoid"]


class MissionEditorDialog:
    def __init__(
        self,
        parent: tk.Tk | tk.Toplevel,
        title: str,
        rule: MissionRule | None = None,
    ):
        self.result: MissionRule | None = None

        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("600x600")
        self.dialog.minsize(500, 500)
        self.dialog.resizable(True, True)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self._create_widgets(rule)

        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.dialog.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.dialog.winfo_height()) // 2
        self.dialog.geometry(f"+{x}+{y}")

        self.dialog.wait_window()

    def _create_widgets(self, rule: MissionRule | None) -> None:
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        main_frame.columnconfigure(1, weight=1)

        # Label
        ttk.Label(main_frame, text="Label:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.label_var = tk.StringVar(value=rule.label if rule else "")
        ttk.Entry(main_frame, textvariable=self.label_var, width=40).grid(
            row=0, column=1, sticky=tk.EW, pady=5
        )

        # Detection patterns
        ttk.Label(main_frame, text="Detection Patterns:").grid(
            row=1, column=0, sticky=tk.NW, pady=5
        )

        pattern_frame = ttk.Frame(main_frame)
        pattern_frame.grid(row=1, column=1, sticky=tk.EW, pady=5)

        self.pattern_text = tk.Text(pattern_frame, width=35, height=6)
        pattern_scroll = ttk.Scrollbar(pattern_frame, orient=tk.VERTICAL, command=self.pattern_text.yview)
        self.pattern_text.configure(yscrollcommand=pattern_scroll.set)

        self.pattern_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        pattern_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        if rule:
            pattern_lines = []
            for group in rule.needles:
                pattern_lines.append(" | ".join(group))
            self.pattern_text.insert(1.0, "\n".join(pattern_lines))

        ttk.Label(main_frame, text="(One group per line, use | for OR. Use CAPS)", font=("", 8)).grid(
            row=2, column=1, sticky=tk.W
        )

        # Wing mission checkbox
        self.wing_var = tk.BooleanVar(value=rule.wing if rule else False)
        ttk.Checkbutton(main_frame, text="Wing Mission", variable=self.wing_var).grid(
            row=3, column=1, sticky=tk.W, pady=5
        )

        # Minimum value
        ttk.Label(main_frame, text="Min Value (CR):").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.value_var = tk.StringVar(value=str(rule.value) if rule and rule.value else "0")
        ttk.Entry(main_frame, textvariable=self.value_var, width=20).grid(
            row=4, column=1, sticky=tk.EW, pady=5
        )

        # Categories
        ttk.Label(main_frame, text="Categories:").grid(row=5, column=0, sticky=tk.NW, pady=5)

        cat_frame = ttk.Frame(main_frame)
        cat_frame.grid(row=5, column=1, sticky=tk.W, pady=5)

        self.category_vars: dict[str, tk.BooleanVar] = {}
        existing_categories = set(rule.categories) if rule else set()

        for i, cat in enumerate(AVAILABLE_CATEGORIES):
            var = tk.BooleanVar(value=cat in existing_categories)
            self.category_vars[cat] = var
            ttk.Checkbutton(cat_frame, text=cat.capitalize(), variable=var).grid(
                row=i // 4, column=i % 4, sticky=tk.W, padx=5
            )

        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=6, column=0, columnspan=2, pady=20)

        ttk.Button(btn_frame, text="Save", command=self._save, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self._cancel, width=10).pack(side=tk.LEFT, padx=5)

    def _save(self) -> None:
        label = self.label_var.get().strip()
        if not label:
            messagebox.showerror("Validation Error", "Label is required.")
            return

        pattern_text = self.pattern_text.get(1.0, tk.END).strip()
        if not pattern_text:
            messagebox.showerror("Validation Error", "At least one detection pattern is required.")
            return

        needles: list[list[str]] = []
        for line in pattern_text.split("\n"):
            line = line.strip()
            if line:
                group = [p.strip().upper() for p in line.split("|") if p.strip()]
                if group:
                    needles.append(group)

        if not needles:
            messagebox.showerror("Validation Error", "At least one detection pattern is required.")
            return

        try:
            value = int(self.value_var.get().replace(",", "").strip() or "0")
        except ValueError:
            messagebox.showerror("Validation Error", "Min Value must be a number.")
            return

        categories = tuple(cat for cat, var in self.category_vars.items() if var.get())
        if not categories:
            messagebox.showerror("Validation Error", "At least one category must be selected.")
            return

        self.result = MissionRule(
            needles=needles,
            label=label,
            wing=self.wing_var.get(),
            value=value,
            categories=categories,
        )
        self.dialog.destroy()

    def _cancel(self) -> None:
        self.dialog.destroy()


class SettingsDialog:
    def __init__(self, parent: tk.Tk | tk.Toplevel, config: AppConfig):
        self.result: AppConfig | None = None
        self.config = config

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Settings")
        self.dialog.geometry("500x400")
        self.dialog.minsize(400, 300)
        self.dialog.resizable(True, True)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self._create_widgets()

        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.dialog.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.dialog.winfo_height()) // 2
        self.dialog.geometry(f"+{x}+{y}")

        self.dialog.wait_window()

    def _create_widgets(self) -> None:
        main_frame = ttk.Frame(self.dialog, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        main_frame.columnconfigure(1, weight=1)

        row = 0

        ttk.Label(main_frame, text="Max Missions:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.max_var = tk.StringVar(value=str(self.config.max_missions))
        ttk.Entry(main_frame, textvariable=self.max_var, width=10).grid(
            row=row, column=1, sticky=tk.EW, pady=5
        )
        row += 1

        ttk.Label(main_frame, text="Poll Interval (min):").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.poll_var = tk.StringVar(value=str(self.config.poll_interval_minutes))
        ttk.Entry(main_frame, textvariable=self.poll_var, width=10).grid(
            row=row, column=1, sticky=tk.EW, pady=5
        )
        row += 1

        ttk.Label(main_frame, text="Poll Offset (min):").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.offset_var = tk.StringVar(value=str(self.config.poll_offset_minutes))
        ttk.Entry(main_frame, textvariable=self.offset_var, width=10).grid(
            row=row, column=1, sticky=tk.EW, pady=5
        )
        row += 1

        ttk.Label(main_frame, text="Discord Webhook:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.webhook_var = tk.StringVar(value=self.config.discord_webhook_url or "")
        ttk.Entry(main_frame, textvariable=self.webhook_var, width=30).grid(
            row=row, column=1, sticky=tk.EW, pady=5
        )
        row += 1

        self.dry_run_var = tk.BooleanVar(value=self.config.dry_run)
        ttk.Checkbutton(main_frame, text="Dry Run (log only, no actions)", variable=self.dry_run_var).grid(
            row=row, column=0, columnspan=2, sticky=tk.W, pady=5
        )
        row += 1

        self.debug_var = tk.BooleanVar(value=self.config.debug_ocr)
        ttk.Checkbutton(main_frame, text="Debug OCR (save images)", variable=self.debug_var).grid(
            row=row, column=0, columnspan=2, sticky=tk.W, pady=5
        )
        row += 1

        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=row, column=0, columnspan=2, pady=20)

        ttk.Button(btn_frame, text="Save", command=self._save, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self._cancel, width=10).pack(side=tk.LEFT, padx=5)

    def _save(self) -> None:
        try:
            max_missions = int(self.max_var.get())
            poll_interval = int(self.poll_var.get())
            poll_offset = int(self.offset_var.get())
        except ValueError:
            messagebox.showerror("Validation Error", "Numeric fields must contain valid numbers.")
            return

        webhook = self.webhook_var.get().strip() or None

        self.result = AppConfig(
            max_missions=max_missions,
            poll_interval_minutes=poll_interval,
            poll_offset_minutes=poll_offset,
            discord_webhook_url=webhook,
            dry_run=self.dry_run_var.get(),
            debug_ocr=self.debug_var.get(),
            interactive=False,
        )
        self.dialog.destroy()

    def _cancel(self) -> None:
        self.dialog.destroy()
