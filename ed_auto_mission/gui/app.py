"""Main GUI application window."""

from __future__ import annotations

import json
import logging
import queue
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from typing import TYPE_CHECKING

from ed_auto_mission.core.types import MissionRule
from ed_auto_mission.core.mission_registry import MissionRegistry, DEFAULT_MISSIONS
from ed_auto_mission.core.config import AppConfig
from ed_auto_mission.gui.dialogs import MissionEditorDialog, SettingsDialog
from ed_auto_mission.gui.runner import RunnerThread

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class QueueHandler(logging.Handler):
    def __init__(self, log_queue: queue.Queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record: logging.LogRecord) -> None:
        self.log_queue.put(self.format(record))


class EDAutoMissionApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("ED Auto Mission")
        self._set_initial_window_size()
        self.root.minsize(600, 400)

        self.registry = MissionRegistry(DEFAULT_MISSIONS)
        self.config = AppConfig.from_env()
        self.runner_thread: RunnerThread | None = None
        self.log_queue: queue.Queue = queue.Queue()

        self._setup_logging()
        self._create_menu()
        self._create_main_layout()
        self._populate_mission_list()
        self._consume_logs()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self.root.bind("<Configure>", self._on_window_resize)

    def _set_initial_window_size(self) -> None:
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        width = int(screen_width * 0.8)
        height = int(screen_height * 0.8)

        max_width = 1500
        max_height = 1200

        width = min(width, max_width)
        height = min(height, max_height)

        x = (screen_width - width) // 2
        y = (screen_height - height) // 2

        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def _setup_logging(self) -> None:
        handler = QueueHandler(self.log_queue)
        handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%H:%M:%S"))
        handler.setLevel(logging.INFO)

        root_logger = logging.getLogger()
        root_logger.addHandler(handler)
        root_logger.setLevel(logging.DEBUG)

    def _create_menu(self) -> None:
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Import Missions...", command=self._import_missions)
        file_menu.add_command(label="Export Missions...", command=self._export_missions)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_close)

        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Settings...", command=self._show_settings)
        edit_menu.add_separator()
        edit_menu.add_command(label="Reset to Defaults", command=self._reset_defaults)

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)

    def _create_main_layout(self) -> None:
        style = ttk.Style()
        style.configure("Treeview", rowheight=50)

        paned = ttk.PanedWindow(self.root, orient=tk.VERTICAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        top_frame = ttk.Frame(paned)
        paned.add(top_frame, weight=3)

        list_frame = ttk.LabelFrame(top_frame, text="Mission Rules", padding=5)
        list_frame.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        columns = ("label", "needles", "wing", "min_value", "categories")
        self.mission_tree = ttk.Treeview(list_frame, columns=columns, show="headings", selectmode="browse")

        self.mission_tree.heading("label", text="Label")
        self.mission_tree.heading("needles", text="Detection Patterns")
        self.mission_tree.heading("wing", text="Wing")
        self.mission_tree.heading("min_value", text="Min Value (CR)")
        self.mission_tree.heading("categories", text="Categories")

        self.mission_tree.column("label", width=100)
        self.mission_tree.column("needles", width=200)
        self.mission_tree.column("wing", width=50)
        self.mission_tree.column("min_value", width=100)
        self.mission_tree.column("categories", width=150)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.mission_tree.yview)
        self.mission_tree.configure(yscrollcommand=scrollbar.set)

        self.mission_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.mission_tree.bind("<Double-1>", lambda e: self._edit_mission())
        self.mission_tree.bind("<Configure>", lambda e: self._on_treeview_resize())

        btn_frame = ttk.Frame(top_frame, padding=5)
        btn_frame.pack(fill=tk.Y, side=tk.RIGHT)

        ttk.Button(btn_frame, text="Add", command=self._add_mission, width=10).pack(pady=2)
        ttk.Button(btn_frame, text="Edit", command=self._edit_mission, width=10).pack(pady=2)
        ttk.Button(btn_frame, text="Remove", command=self._remove_mission, width=10).pack(pady=2)
        ttk.Separator(btn_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        ttk.Button(btn_frame, text="Move Up", command=self._move_up, width=10).pack(pady=2)
        ttk.Button(btn_frame, text="Move Down", command=self._move_down, width=10).pack(pady=2)

        bottom_frame = ttk.Frame(paned)
        paned.add(bottom_frame, weight=2)

        log_frame = ttk.LabelFrame(bottom_frame, text="Log", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        self.log_text = tk.Text(log_frame, state=tk.DISABLED, wrap=tk.WORD)
        log_scroll = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scroll.set)

        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        ctrl_frame = ttk.Frame(bottom_frame, padding=5)
        ctrl_frame.pack(fill=tk.Y, side=tk.RIGHT)

        self.status_var = tk.StringVar(value="Stopped")
        ttk.Label(ctrl_frame, text="Status:").pack(anchor=tk.W)
        self.status_label = ttk.Label(ctrl_frame, textvariable=self.status_var, font=("", 10, "bold"))
        self.status_label.pack(anchor=tk.W, pady=(0, 10))

        ttk.Label(ctrl_frame, text="Initial Missions:").pack(anchor=tk.W)
        self.initial_missions_var = tk.StringVar(value="0")
        self.initial_missions_entry = ttk.Entry(ctrl_frame, textvariable=self.initial_missions_var, width=10)
        self.initial_missions_entry.pack(anchor=tk.W, pady=(0, 10))

        self.start_btn = ttk.Button(ctrl_frame, text="Start", command=self._toggle_runner, width=12)
        self.start_btn.pack(pady=5)

        ttk.Button(ctrl_frame, text="Clear Log", command=self._clear_log, width=12).pack(pady=5)

    def _on_treeview_resize(self) -> None:
        tree_width = self.mission_tree.winfo_width()

        if tree_width > 100:
            scrollbar_width = 20
            available_width = tree_width - scrollbar_width

            widths = {
                "label": available_width * 0.15,
                "needles": available_width * 0.45,
                "wing": available_width * 0.08,
                "min_value": available_width * 0.12,
                "categories": available_width * 0.20,
            }

            for col, width in widths.items():
                self.mission_tree.column(col, width=int(width))

    def _on_window_resize(self, event) -> None:
        if event.widget == self.root:
            self.root.after(50, self._on_treeview_resize)

    def _populate_mission_list(self) -> None:
        for item in self.mission_tree.get_children():
            self.mission_tree.delete(item)

        for rule in self.registry.all():
            needles_str = " AND ".join(
                "(" + "|".join(group) + ")" for group in rule.needles
            )
            categories_str = ", ".join(rule.categories) if rule.categories else "-"
            self.mission_tree.insert("", tk.END, values=(
                rule.label,
                needles_str,
                "Yes" if rule.wing else "No",
                f"{rule.value:,}" if rule.value else "-",
                categories_str,
            ))

    def _add_mission(self) -> None:
        dialog = MissionEditorDialog(self.root, "Add Mission")
        if dialog.result:
            self.registry.add_rule(dialog.result)
            self._populate_mission_list()
            self._log("Added mission rule: " + dialog.result.label)

    def _edit_mission(self) -> None:
        selection = self.mission_tree.selection()
        if not selection:
            messagebox.showinfo("Edit Mission", "Please select a mission to edit.")
            return

        idx = self.mission_tree.index(selection[0])
        rules = self.registry.all()
        if idx >= len(rules):
            return

        rule = rules[idx]
        dialog = MissionEditorDialog(self.root, "Edit Mission", rule)
        if dialog.result:
            self.registry.remove(rule)
            all_rules = self.registry.all()
            self.registry.clear()
            for i, r in enumerate(all_rules):
                if i == idx:
                    self.registry.add_rule(dialog.result)
                self.registry.add_rule(r)
            if idx >= len(all_rules):
                self.registry.add_rule(dialog.result)

            self._populate_mission_list()
            self._log("Updated mission rule: " + dialog.result.label)

    def _remove_mission(self) -> None:
        selection = self.mission_tree.selection()
        if not selection:
            messagebox.showinfo("Remove Mission", "Please select a mission to remove.")
            return

        idx = self.mission_tree.index(selection[0])
        rules = self.registry.all()
        if idx >= len(rules):
            return

        rule = rules[idx]
        if messagebox.askyesno("Confirm Remove", f"Remove mission rule '{rule.label}'?"):
            self.registry.remove(rule)
            self._populate_mission_list()
            self._log("Removed mission rule: " + rule.label)

    def _move_up(self) -> None:
        selection = self.mission_tree.selection()
        if not selection:
            return

        idx = self.mission_tree.index(selection[0])
        if idx == 0:
            return

        rules = self.registry.all()
        self.registry.clear()
        rules[idx], rules[idx - 1] = rules[idx - 1], rules[idx]
        self.registry.add_many(rules)
        self._populate_mission_list()

        children = self.mission_tree.get_children()
        if idx - 1 < len(children):
            self.mission_tree.selection_set(children[idx - 1])

    def _move_down(self) -> None:
        selection = self.mission_tree.selection()
        if not selection:
            return

        idx = self.mission_tree.index(selection[0])
        rules = self.registry.all()
        if idx >= len(rules) - 1:
            return

        self.registry.clear()
        rules[idx], rules[idx + 1] = rules[idx + 1], rules[idx]
        self.registry.add_many(rules)
        self._populate_mission_list()

        children = self.mission_tree.get_children()
        if idx + 1 < len(children):
            self.mission_tree.selection_set(children[idx + 1])

    def _toggle_runner(self) -> None:
        if self.runner_thread and self.runner_thread.is_alive():
            self._stop_runner()
        else:
            self._start_runner()

    def _start_runner(self) -> None:
        try:
            initial = int(self.initial_missions_var.get())
        except ValueError:
            initial = 0

        try:
            from ed_auto_mission.services.screen import ScreenService
            from ed_auto_mission.services.ocr import OCRService, setup_tesseract
            from ed_auto_mission.services.input import InputService
            from ed_auto_mission.services.process import ensure_game_running
            from ed_auto_mission.services.window import focus_elite_dangerous
            from ed_auto_mission.adapters import EliteDangerousGame

            setup_tesseract(self.config.tesseract_path)
            ensure_game_running()
            focus_elite_dangerous()

            screen = ScreenService()
            ocr = OCRService(screen, debug_output=self.config.debug_ocr)
            input_service = InputService(dry_run=self.config.dry_run)
            game = EliteDangerousGame(
                screen=screen,
                ocr=ocr,
                input_service=input_service,
                debug_output=self.config.debug_ocr,
            )
        except (ImportError, RuntimeError, FileNotFoundError) as e:
            self._log(f"Failed to initialize: {e}")
            messagebox.showerror("Initialization Error", str(e))
            return

        self.runner_thread = RunnerThread(
            game=game,
            registry=self.registry,
            config=self.config,
            initial_missions=initial,
            on_complete=self._on_runner_complete,
        )
        self.runner_thread.start()

        self.status_var.set("Running")
        self.start_btn.configure(text="Stop")
        self._log("Mission runner started")

    def _stop_runner(self) -> None:
        if self.runner_thread:
            self.runner_thread.stop()
            self.runner_thread = None

        self.status_var.set("Stopped")
        self.start_btn.configure(text="Start")
        self._log("Mission runner stopped")

    def _on_runner_complete(self, total_missions: int) -> None:
        self.root.after(0, lambda: self._runner_finished(total_missions))

    def _runner_finished(self, total_missions: int) -> None:
        self.status_var.set("Completed")
        self.start_btn.configure(text="Start")
        self.runner_thread = None
        self._log(f"Mission runner completed. Total missions: {total_missions}")

    def _show_settings(self) -> None:
        dialog = SettingsDialog(self.root, self.config)
        if dialog.result:
            self.config = dialog.result
            self._log("Settings updated")

    def _reset_defaults(self) -> None:
        if messagebox.askyesno("Reset to Defaults", "Reset all mission rules to defaults?"):
            self.registry.clear()
            self.registry.add_many(DEFAULT_MISSIONS)
            self._populate_mission_list()
            self._log("Mission rules reset to defaults")

    def _import_missions(self) -> None:
        path = filedialog.askopenfilename(
            title="Import Missions",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if not path:
            return

        try:
            with open(path, "r") as f:
                data = json.load(f)

            self.registry.clear()
            for item in data:
                categories = item.get("categories", [])
                if isinstance(categories, list):
                    categories = tuple(categories)
                rule = MissionRule(
                    needles=item["needles"],
                    label=item["label"],
                    wing=item.get("wing", False),
                    value=item.get("value", 0),
                    categories=categories,
                )
                self.registry.add_rule(rule)

            self._populate_mission_list()
            self._log(f"Imported {len(data)} missions from {Path(path).name}")
        except (json.JSONDecodeError, KeyError, OSError) as e:
            messagebox.showerror("Import Error", f"Failed to import: {e}")

    def _export_missions(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Export Missions",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if not path:
            return

        try:
            data = [
                {
                    "label": rule.label,
                    "needles": rule.needles,
                    "wing": rule.wing,
                    "value": rule.value,
                    "categories": list(rule.categories),
                }
                for rule in self.registry.all()
            ]

            with open(path, "w") as f:
                json.dump(data, f, indent=2)

            self._log(f"Exported {len(data)} missions to {Path(path).name}")
        except (OSError, TypeError) as e:
            messagebox.showerror("Export Error", f"Failed to export: {e}")

    def _show_about(self) -> None:
        messagebox.showinfo(
            "About ED Auto Mission",
            "ED Auto Mission v2.0.0\n\n"
            "Automatically accepts missions in Elite Dangerous.\n\n"
            "https://github.com/Tropingenie/EDAutoMission"
        )

    def _log(self, message: str) -> None:
        self.log_queue.put(f"[INFO] {message}")

    def _clear_log(self) -> None:
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def _consume_logs(self) -> None:
        try:
            while True:
                message = self.log_queue.get_nowait()
                self.log_text.configure(state=tk.NORMAL)
                self.log_text.insert(tk.END, message + "\n")
                self.log_text.see(tk.END)
                self.log_text.configure(state=tk.DISABLED)
        except queue.Empty:
            pass

        self.root.after(100, self._consume_logs)

    def _on_close(self) -> None:
        if self.runner_thread and self.runner_thread.is_alive():
            if messagebox.askyesno("Confirm Exit", "Runner is active. Stop and exit?"):
                self._stop_runner()
            else:
                return

        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


def run_gui() -> None:
    app = EDAutoMissionApp()
    app.run()


if __name__ == "__main__":
    run_gui()
