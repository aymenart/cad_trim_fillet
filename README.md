# CAD Trim & Fillet for IngeTrazo

[![IngeTrazo Extension](https://img.shields.io/badge/IngeTrazo-Extension-blue.svg)](https://ingetrazo.com/extensiones)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Version](https://img.shields.io/badge/Version-1.0.0-green.svg)]()

Professional 2D/3D CAD Trimming, Corner Fillet & Chamfer suite for **IngeTrazo** (the open-source BIM CAD software).

Developed by **Aymen Alhaddad (Architect & Developer)**.

🌐 Disponible también en español: [README.es.md](README.es.md)

---

## Features

### 1. Quick Trim
- Click any line segment to erase it between its nearest bounding intersections.
- Real-time hover preview glows in bright red with 'X' deletion markers.
- Cleans up orphan vertices and heals face topology automatically.

### 2. Boundary Trim
- Select a cutting boundary line first, then click intersecting lines to trim away the clicked side.

### 3. Tangent Fillet Arc
- Create smooth tangent circular arcs rounding corners between two lines.
- **Measurements Box (VCB) Support**: Type radius directly at any time (e.g. `0.5`, `1.2`) and press `Enter`.
- **Sharp Corner ($R=0$)**: Setting radius to `0` extends or trims edges to a sharp vertex.
- **B-Rep Face Healer**: Automatically updates incident surface polygons, deleting the outer wedge outside the arc.
- Real-time rubber-band circular arc preview in the viewport.

### 4. Chamfer Bevel
- Straight-line corner beveled connections with customizable distances ($D_1$, $D_2$).
- Full VCB distance entry support and automatic face trimming.

### 5. Settings Dialog
- Dedicated settings modal to adjust default fillet radius, arc segment resolution (smoothness), and chamfer distances.

### 6. Professional Architecture & Undo/Redo
- Full transactional undo/redo integration with IngeTrazo's `SnapshotImport` (`Ctrl+Z` / `Ctrl+Y`).
- Theme-adaptive high-DPI vector icons (supports both Dark and Light UI themes).
- Viewport context menu shortcuts on right-click.

### 7. Multi-language Interface (English / Spanish)
- Choose the language in the settings dialog (**Automatic / English / Español**). The choice is saved between sessions; restart IngeTrazo to apply it to menus and toolbar.
- With **Automatic**, Spanish is used if IngeTrazo or the system uses Spanish, English otherwise.
- To force a language from the code, set `FORCE_LANGUAGE = "en"` or `FORCE_LANGUAGE = "es"` near the top of `__init__.py`.
- To add another language, copy the `"en"` block inside `_TEXTS` and translate it.

---

## Installation

1. Download the latest `cad_trim_fillet_v1.0.0.zip` from [Releases](https://github.com/aymenart/cad_trim_fillet/releases).
2. Extract the folder `cad_trim_fillet` into your IngeTrazo plugins directory:
   - **Windows**: `%APPDATA%\IngeTrazo\plugins\`  
     (`C:\Users\<YourUser>\AppData\Roaming\IngeTrazo\plugins\`)
   - **Linux / Flatpak / AppImage**: `~/.config/IngeTrazo/plugins/`
3. Restart IngeTrazo. The **CAD Trim & Fillet** toolbar will appear at the top, along with menu entries under **Extensions > CAD Trim & Fillet**.

---

## License

This project is licensed under the GNU General Public License v3.0 or later (GPL-3.0-or-later).
