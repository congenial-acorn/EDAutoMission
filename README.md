# ED Auto Mission

Automatically accepts missions in Elite Dangerous based on configurable criteria. Ideal for automatically gathering missions across multiple mission board categories.

## Features

- **GUI Interface** - Visual mission configuration and control
- **Mission Categories** - Configure missions for different board categories (all, combat, transport, freelance, operations, support, thargoid)
- **Category Scanning** - Automatically navigates through all configured categories
- **Custom Mission Rules** - Add, edit, remove detection patterns
- **Import/Export** - Save and load mission configurations as JSON
- **Discord Notifications** - Get alerts when missions are accepted
- **Auto-scaling** - Works with any 16:9 resolution
- **Immediate Stop** - Stop button responds instantly (interrupts mid-scan)

## Requirements

- Python 3.10+
- [Tesseract OCR](https://github.com/tesseract-ocr/tessdoc/blob/main/Installation.md)
- Elite Dangerous

## Installation

```bash
# Clone the repository
git clone https://github.com/Tropingenie/EDAutoMission.git
cd EDAutoMission

# Install dependencies
pip install -e .

# Or using requirements.txt
pip install -r requirements.txt
```

### Tesseract Setup

Install Tesseract OCR for your platform:

- **Windows**: Install to `C:\Program Files\Tesseract-OCR` (default) or set `TESSERACT_PATH`
- **Linux**: `sudo apt install tesseract-ocr`
- **macOS**: `brew install tesseract`

## Usage

### GUI Mode (Default)

```bash
python main.py
```

The GUI allows you to:
- **Add/Edit/Remove** mission detection rules
- **Configure** max missions, poll interval, Discord webhook
- **Start/Stop** automation runner (stops immediately when clicked)
- **Import/Export** mission configurations as JSON
- **View logs** in real-time

### CLI Mode

```bash
python main.py --cli
```

1. Dock at a station and open Starport Services
2. Navigate to the Mission Board
3. Run the script
4. On non-Windows systems, switch back to the game within 5 seconds

Press `Ctrl+C` to stop.

## Configuration

### Via GUI

Edit → Settings to configure:
- Maximum missions
- Poll interval
- Discord webhook
- Dry run mode
- Debug OCR

### Via Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ED_MAX_MISSIONS` | `20` | Stop when this many missions are accepted |
| `ED_POLL_INTERVAL` | `10` | Minutes between mission board scans |
| `ED_DRY_RUN` | `false` | Log actions without executing (`1` to enable) |
| `ED_DEBUG_OCR` | `false` | Save OCR debug images (`1` to enable) |
| `DISCORD_WEBHOOK_URL` | - | Discord webhook for notifications |
| `TESSERACT_PATH` | auto | Path to Tesseract executable |

## Mission Categories

The script supports multiple mission board categories. When configuring a mission rule, select one or more categories:

- **all** - All missions (default board view)
- **combat** - Combat missions
- **transport** - Transport missions
- **freelance** - Freelance work
- **operations** - Operations missions
- **support** - Support missions
- **thargoid** - Thargoid-related missions

The scanner will automatically navigate to each configured category, scan all missions, accept matches, then move to the next category until all have been checked.

## Mission Rules

### Default Rules

The script comes with default rules for wing mining missions:
- **Bertrandite** (>49M CR) - Category: transport
- **Gold** (>40M CR) - Category: transport
- **Silver** (>49M CR) - Category: transport
- **Indite** (>39M CR) - Category: transport

### Custom Rules

In the GUI, click **Add** to create a custom rule:

- **Label**: Display name for the mission type
- **Detection Patterns**: Text patterns to match (one group per line)
  - Use `|` for OR within a group
  - Multiple lines = AND between groups
  - Example: `MINE | MINING | BLAST` on one line, `GOLD` on another
- **Categories**: Select one or more categories where this mission appears
- **Wing Mission**: Check if this should only match wing missions
- **Min Value**: Minimum credit value to accept

### Import/Export

Save your mission configurations to JSON:

```json
[
  {
    "label": "Gold Mining",
    "needles": [["MINE", "MINING", "BLAST"], ["GOLD"]],
    "categories": ["transport"],
    "wing": true,
    "value": 40000000
  }
]
```

Multiple categories can be specified:

```json
{
  "label": "Multi-category Mission",
  "categories": ["transport", "combat"],
  ...
}
```

## Project Structure

```
ed_auto_mission/
├── core/           # Domain logic (mission rules, runner, categories)
├── services/       # Infrastructure (OCR, input, screen capture, timing)
├── adapters/       # Game interaction implementation
└── gui/            # Graphical user interface
```

## Supported Resolutions

- All 16:9 resolutions (720p, 1080p, 1440p, 2160p)

## License

This repository is under the [MIT License](https://github.com/congenial-acorn/EDAutoMission/blob/main/LICENSE).

## Disclaimer

Use of automation tools violates Frontier's Terms of Service. Use at your own risk. The developer is not responsible for any actions taken against your account.

## Credits

Originally forked from [Tropingenie/EDAutoMission](https://github.com/Tropingenie/EDAutoMission)
