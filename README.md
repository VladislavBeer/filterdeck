# filterdeck
This program allows you to apply real-time webcam filters with OpenCV: 26 effects, adjustable parameters, and a savable quick-swap hotbar.

## Features

* Simple and clear interface.
* 26 unique filters, including:
  * X-ray,
  * Neon Edges,
  * Thermal,
  * Fisheye,
  * Glitch,
  * Vintage,
  * Sketch,
  * Oil Paint,
  * Pixelate,
  * a CRT-style "Mr. House" effect,
  * and many more.
* Side-by-side view of the original and filtered feed
* Adjustable parameters (threshold, kernel size, pixel size) with the arrow keys
* Quick-swap hotbar: assign filters to number slots and jump between them instantly
* Hotbar saved to `hotbar.json`, so it survives restarts
* Capture images from the filtered frame

## Getting started

Requires Python 3.8+, a webcam, and:
* OpenCV
* NumPy

## Installation:

```bash
git clone https://github.com/VladislavBeer/filterdeck
cd filterdeck
python filterdeck.py
```

## Controls

| Key | Action |
|-----|--------|
| `f` | Next filter |
| `1`-`9` | Switch to the filter in that hotbar slot |
| `Shift` + `1`-`9` | Assign the current filter to that slot |
| `Up` / `Down` | Adjust threshold, kernel size, or pixel size (depends on filter) |
| `c` | Capture the filtered frame |
| `q` | Quit |

## How it works

Each filter is a standalone function that takes a BGR frame and returns a processed frame. The main loop reads from the webcam, applies the active filter, and displays both feeds. The hotbar is a 9-slot list serialised to JSON on every change.

## License


Copyright (c) 2026 VladislavBeer

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
