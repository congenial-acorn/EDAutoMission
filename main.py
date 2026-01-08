#!/usr/bin/env python3
"""
ED Auto Mission - Elite Dangerous mission automation tool.

Usage:
    python main.py          # Launch GUI
    python main.py --cli    # Run in CLI mode (headless)
    python main.py --help   # Show help

Environment variables:
    ED_MAX_MISSIONS     - Maximum missions to collect (default: 20)
    ED_POLL_INTERVAL    - Minutes between mission board scans (default: 10)
    ED_DRY_RUN          - Set to "1" to log actions without executing
    ED_DEBUG_OCR        - Set to "1" to save OCR debug images
    DISCORD_WEBHOOK_URL - Discord webhook for notifications
"""

import sys


def main() -> int:
    """Main entry point - launches GUI by default, CLI with --cli flag."""
    args = sys.argv[1:]

    if "--help" in args or "-h" in args:
        print(__doc__)
        print("Options:")
        print("  --cli     Run in command-line mode (no GUI)")
        print("  --help    Show this help message")
        return 0

    if "--cli" in args:
        # CLI mode
        from ed_auto_mission.main import main as cli_main
        return cli_main()
    else:
        # GUI mode (default)
        try:
            from ed_auto_mission.gui import run_gui
            run_gui()
            return 0
        except ImportError as e:
            print(f"GUI dependencies not available: {e}")
            print("Falling back to CLI mode...")
            from ed_auto_mission.main import main as cli_main
            return cli_main()


if __name__ == "__main__":
    sys.exit(main())
