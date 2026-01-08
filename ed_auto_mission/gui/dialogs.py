"""Dialog windows for the GUI."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from typing import TYPE_CHECKING

from ed_auto_mission.core.types import MissionRule
from ed_auto_mission.core.config import AppConfig

if TYPE_CHECKING:
    pass


class MissionEditorDialog:
    """Dialog for creating or editing a mission rule."""

    def __init__(
        self,
        parent: tk.Tk | tk.Toplevel,
        title: str,
        rule: MissionRule | None = None,
    ):
        self.result: MissionRule | None = None

        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("1000x700")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self._create_widgets(rule)

        # Center on parent
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.dialog.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.dialog.winfo_height()) // 2
        self.dialog.geometry(f"+{x}+{y}")

        self.dialog.wait_window()

    def _create_widgets(self, rule: MissionRule | None) -> None:
        """Create dialog widgets."""
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Label
        ttk.Label(main_frame, text="Label:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.label_var = tk.StringVar(value=rule.label if rule else "")
        ttk.Entry(main_frame, textvariable=self.label_var, width=40).grid(
            row=0, column=1, sticky=tk.W, pady=5
        )

        # Detection patterns
        ttk.Label(main_frame, text="Detection Patterns:").grid(
            row=1, column=0, sticky=tk.NW, pady=5
        )

        pattern_frame = ttk.Frame(main_frame)
        pattern_frame.grid(row=1, column=1, sticky=tk.W, pady=5)

        self.pattern_text = tk.Text(pattern_frame, width=35, height=8)
        pattern_scroll = ttk.Scrollbar(pattern_frame, orient=tk.VERTICAL, command=self.pattern_text.yview)
        self.pattern_text.configure(yscrollcommand=pattern_scroll.set)

        self.pattern_text.pack(side=tk.LEFT, fill=tk.BOTH)
        pattern_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Pre-populate patterns
        if rule:
            pattern_lines = []
            for group in rule.needles:
                pattern_lines.append(" | ".join(group))
            self.pattern_text.insert(1.0, "\n".join(pattern_lines))

        ttk.Label(main_frame, text="(One group per line, use | for OR)", font=("", 8)).grid(
            row=2, column=1, sticky=tk.W
        )

        # Wing mission checkbox
        self.wing_var = tk.BooleanVar(value=rule.wing if rule else False)
        ttk.Checkbutton(main_frame, text="Wing Mission", variable=self.wing_var).grid(
            row=3, column=1, sticky=tk.W, pady=10
        )

        # Minimum value
        ttk.Label(main_frame, text="Min Value (CR):").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.value_var = tk.StringVar(value=str(rule.value) if rule and rule.value else "0")
        ttk.Entry(main_frame, textvariable=self.value_var, width=20).grid(
            row=4, column=1, sticky=tk.W, pady=5
        )

        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=20)

        ttk.Button(btn_frame, text="Save", command=self._save, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self._cancel, width=10).pack(side=tk.LEFT, padx=5)

    def _save(self) -> None:
        """Validate and save the mission rule."""
        label = self.label_var.get().strip()
        if not label:
            messagebox.showerror("Validation Error", "Label is required.")
            return

        # Parse patterns
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

        # Parse value
        try:
            value = int(self.value_var.get().replace(",", "").strip() or "0")
        except ValueError:
            messagebox.showerror("Validation Error", "Min Value must be a number.")
            return

        self.result = MissionRule(
            needles=needles,
            label=label,
            wing=self.wing_var.get(),
            value=value,
        )
        self.dialog.destroy()

    def _cancel(self) -> None:
        """Cancel the dialog."""
        self.dialog.destroy()


class SettingsDialog:
    """Dialog for application settings."""

    def __init__(self, parent: tk.Tk | tk.Toplevel, config: AppConfig):
        self.result: AppConfig | None = None
        self.config = config

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Settings")
        self.dialog.geometry("400x300")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self._create_widgets()

        # Center on parent
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.dialog.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.dialog.winfo_height()) // 2
        self.dialog.geometry(f"+{x}+{y}")

        self.dialog.wait_window()

    def _create_widgets(self) -> None:
        """Create dialog widgets."""
        main_frame = ttk.Frame(self.dialog, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        row = 0

        # Max missions
        ttk.Label(main_frame, text="Max Missions:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.max_var = tk.StringVar(value=str(self.config.max_missions))
        ttk.Entry(main_frame, textvariable=self.max_var, width=10).grid(
            row=row, column=1, sticky=tk.W, pady=5
        )
        row += 1

        # Poll interval
        ttk.Label(main_frame, text="Poll Interval (min):").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.poll_var = tk.StringVar(value=str(self.config.poll_interval_minutes))
        ttk.Entry(main_frame, textvariable=self.poll_var, width=10).grid(
            row=row, column=1, sticky=tk.W, pady=5
        )
        row += 1

        # Poll offset
        ttk.Label(main_frame, text="Poll Offset (min):").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.offset_var = tk.StringVar(value=str(self.config.poll_offset_minutes))
        ttk.Entry(main_frame, textvariable=self.offset_var, width=10).grid(
            row=row, column=1, sticky=tk.W, pady=5
        )
        row += 1

        # Discord webhook
        ttk.Label(main_frame, text="Discord Webhook:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.webhook_var = tk.StringVar(value=self.config.discord_webhook_url or "")
        ttk.Entry(main_frame, textvariable=self.webhook_var, width=30).grid(
            row=row, column=1, sticky=tk.W, pady=5
        )
        row += 1

        # Dry run
        self.dry_run_var = tk.BooleanVar(value=self.config.dry_run)
        ttk.Checkbutton(main_frame, text="Dry Run (log only, no actions)", variable=self.dry_run_var).grid(
            row=row, column=0, columnspan=2, sticky=tk.W, pady=5
        )
        row += 1

        # Debug OCR
        self.debug_var = tk.BooleanVar(value=self.config.debug_ocr)
        ttk.Checkbutton(main_frame, text="Debug OCR (save images)", variable=self.debug_var).grid(
            row=row, column=0, columnspan=2, sticky=tk.W, pady=5
        )
        row += 1

        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=row, column=0, columnspan=2, pady=20)

        ttk.Button(btn_frame, text="Save", command=self._save, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self._cancel, width=10).pack(side=tk.LEFT, padx=5)

    def _save(self) -> None:
        """Validate and save settings."""
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
            interactive=False,  # GUI mode is not interactive
        )
        self.dialog.destroy()

    def _cancel(self) -> None:
        """Cancel the dialog."""
        self.dialog.destroy()
