# Nebulatro

A Balatro card order tracker with modifier overlays, custom card designs, and dynamic spacing. Track your card sequences by clicking cards with enhancements, editions, and seals applied.

## Setup

### 1. Install Dependencies

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
# venv\Scripts\activate  # On Windows

# Install Python packages
pip3 install -r requirements.txt

# Install tkinter (macOS only)
brew install python-tk@3.13
```

### 2. Add Game Resources

**Option A: Use Game Resources (Recommended)**

Copy the `resources` folder from your Balatro game installation to this directory:

```
Balatro-Calc/
  resources/
    textures/
      1x/
        8BitDeck_opt2.png
        Enhancers.png
        Jokers.png
        Tarots.png
        boosters.png
        ...
```

The app will automatically use these files via `resource_mapping.json`.

**Option B: Use Fallback Assets**

If you don't have access to game resources, the app will fall back to sprite sheets in the `assets/` folder. These should follow the naming convention: `COLSxROWS Description.png` (e.g., `13x4 Playing Cards.png`).

### 3. Run the App

```bash
source venv/bin/activate
python3 balatro_tracker.py
```

## Usage

- Click any card in the grid to add it to your sequence
- The order appears at the bottom with smaller card images
- Use "Undo Last" to remove the most recent card
- Use "Clear Order" to start over

## Features

- **Game Resource Integration**: Uses Balatro's own sprite sheets with fallback to custom assets
- **Card Modifiers**: Select Enhancements, Editions, and Seals that overlay onto cards
  - Background modifiers (Bonus, Mult, Wild) replace card backing
  - Blend modes for realistic effects (multiply, color)
  - Real-time preview on all cards
- **Dynamic Card Spacing**: Cards overlap when window is resized (up to 70%)
- **Click to Track**: Click cards to add to sequence with current modifiers applied
- **Export**: Save card order as CSV with modifiers (e.g., `AS+Mult+Foil,KS,QH+Red_Seal`)
- **Dark Theme**: Matches macOS dark mode
- **Undo/Clear**: Remove last card or reset entire sequence


## Configuration

### Resource Mapping (`resource_mapping.json`)

Maps game resource files to sprite sheet definitions. Edit this file to:
- Add new sprite sheets
- Update grid dimensions
- Define card names and positions

### Card Order (`card_order_config.json`)

Configures:
- Playing card display order (suits, ranks)
- Modifier indices and names
- Render modes (overlay, background)
- Blend modes (normal, multiply, color)
- Opacity values

## Project Structure

```
balatro_tracker.py          # Main application
sprite_loader.py            # Sprite sheet loader
card_order_config.json      # Card display configuration
resource_mapping.json       # Game resource mappings
requirements.txt            # Python dependencies
resources/                  # Game resources (not included - copy from game)
assets/                     # Fallback sprite sheets
SPRITE_SETUP.md            # Sprite sheet guide
```

## Requirements

- Python 3.13+
- Pillow (PIL) for image processing
- tkinter for GUI (requires python-tk on macOS)

## Notes

- The `resources/` folder is not included in the repository due to size and copyright
- Copy it from your Balatro game installation directory
- Fallback assets in `assets/` folder work if resources are unavailable
- Generated files (`card_order_*.txt`) are excluded from git

## License

This is a fan-made tool for Balatro. Game assets belong to their respective owners.
