# Color Sorting Game

A web-based game. The game includes:

- **Start Screen** – presented when the page loads. Press **Start** to begin.
- **Game Screen** – shows the current level with a **Reset Level** button.
- **Completion Overlay** – appears on top of the level when it is solved and contains a **Next Level** button.

Each screen fills the entire viewport so there is no scrolling on mobile devices. The JavaScript manages transitions between screens and keeps track of the current level number, starting from 1.

Levels automatically advance once every base is full with objects of a single color or is empty.

## Getting Started

Open `www/index.html` in a modern browser to try the demo. No build step or external dependencies are required.

## Level Configuration

Levels are defined in `levels.json`. The file contains a JSON array where each
element describes one level. A level is made of rows, each containing a list of
cells. Every cell specifies a `baseHeight` integer and a list of `objects` which
are just color strings. For example:

```json
{
  "rows": [
    [
      { "baseHeight": 1, "objects": ["green"] },
      { "baseHeight": 0, "objects": [] }
    ]
  ]
}
```

The game script loads this configuration on startup so new levels can be added
without modifying the JavaScript.

## Level Rendering

Each base is drawn using an image named `img/base_{baseHeight}.png` and each
object uses `img/object_{name}.png`. The canvas reserves 5% of the screen on the
sides and bottom and 15% at the top for the control buttons. Bases are positioned in a grid with 20% of
the base width separating cells horizontally and 50% of the base width
separating rows vertically. A constant **BASE_BOTTOM** controls how far from the
bottom of the base the first object is stacked (25% of the base width in this
demo). Objects keep their original aspect ratio when scaled so they may not be
perfectly square. Everything is scaled uniformly to fit the available space.
