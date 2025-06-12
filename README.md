# Color Sorting Game

A minimal web-based game skeleton that demonstrates how to manage multiple screens on a mobile layout. The game includes:

- **Start Screen** – presented when the page loads. Press **Start** to begin.
- **Game Screen** – shows the current level. Press **Complete Level** to finish a level.
- **Level Completed Screen** – displays when a level is completed. Press **Next Level** to continue to the next level.

Each screen fills the entire viewport so there is no scrolling on mobile devices. The JavaScript manages transitions between screens and keeps track of the current level number, starting from 1.

This project is intended as a simple starting point for expanding into a full puzzle game where players sort colors into the correct order.

## Getting Started

Open `index.html` in a modern browser to try the demo. No build step or external dependencies are required.

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
sides and 15% at the bottom. Bases are positioned in a grid with 20% of the base
width separating cells horizontally and 50% of the base width separating rows
vertically. A constant **BASE_BOTTOM** controls how far from the bottom of the
base the first object is stacked (20% of the base width in this demo). Objects
are drawn one above another so they appear stacked on the platform. Everything is
scaled uniformly to fit the available space.
