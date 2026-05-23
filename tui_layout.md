# png_tools TUI Layout Specifications & Element Sizing

This document outlines the structural hierarchy of the proposed terminal user interface (TUI) for the `png_tools` project, along with the element names (IDs/classes) and their exact sizing in **character columns (widths)** and **lines (heights)**.

---

## 🗺️ TUI Visual Blueprint

Below is the layout map as rendered by Textual. Dimensions are expressed as `[Width x Height]` in character cells:

```text
+-----------------------------------------------------------------------------------------------------------------------+
|                                              HEADER (Title & Subtitle)                                                |
+-----------------------------------------------------------------------------------------------------------------------+
|                                              #main-layout [width: 100%, height: 1fr, max-height: 44]                  |
| +------------------------------------+------------------------------------------------------------------------------+ |
| | #sidebar                           | #content (VerticalScroll) [width: 1fr, height: 1fr]                          | |
| | [width: 38, height: 1fr]           |                                                                              | |
| |                                    |  Label(" Tool & Configurations")                                            | |
| |  Label(" PNG Source Files")        |                                                                              | |
| |  ListView (self.file_list)         |  #columns-container [width: 1fr, height: 1fr, min-height: 42]                | |
| |   - height: 16                     |  +--------------------+--------------------+-------------------------------+ | |
| |                                    |  | #col1              | #col2              | #col3                         | | |
| |  Label(" Selected File Details")   |  | [width: 50, H:100%]| [width: 55, H:100%]| [width: 1fr, height: 100%]    | | |
| |  Label (self.info_label)           |  |                    |                    |                               | | |
| |   - max-height: 20                 |  | FormGroup          | ContentSwitcher    | FormGroup                     | | |
| |                                    |  | (border_title)     | (active_group)     | (border_title)                | | |
| |                                    |  | - Active Tool      | -> MaskOptions     | - Run Active Tool Button      | | |
| |                                    |  | - Target PNG       | -> PreshiftOptions | - Analyze Image Button        | | |
| |                                    |  | - Output Directory | -> CollisionMap    |   - max-height: 12            | | |
| |                                    |  |                    |    Options         | Label(" Output Preview")      | | |
| |                                    |  |                    |                    |                               | | |
| |                                    |  |                    |                    | #analysis-log                 | | |
| |                                    |  |                    |                    | [W:1fr, H:1fr, max-H:20]      | | |
| |                                    |  +--------------------+--------------------+-------------------------------+ | |
| +------------------------------------+------------------------------------------------------------------------------+ |
+-----------------------------------------------------------------------------------------------------------------------+
|                                              #logs-container [width: 100%, height: 1fr, min-height: 12]              |
|  Label(" Execution Terminal Logs")                                                                                    |
|  RichLog (self.execution_log)                                                                                         |
+-----------------------------------------------------------------------------------------------------------------------+
|                                                       FOOTER                                                          |
+-----------------------------------------------------------------------------------------------------------------------+
```

---

## 📊 Detailed Sizing Specifications

Textual layouts are fully text-cell based (no pixels). Here are the exact constraints:

### 1. Left Sidebar Panel
* **Container**: `Vertical(id="sidebar")`
  * **Width**: Fixed `38` character cells (`width: 38;`).
  * **Height**: `1fr` (fills the vertical space of the screen).
* **Inner Components**:
  * **PNG Files List (`self.file_list`, ID: `#file-list`)**: Height is `16` cells. It scans the `png/` directory and shows source `.png` files, ignoring generated suffix files (`_mask.png`, `_tilemap.png`, `_shifted.png`).
  * **Details Panel (`self.info_label`, ID: `#info-panel`)**: Height is `1fr` with a **Fixed Max-Height of `20` rows** (`max-height: 20;`) and **Width is `1fr`** (occupies 100% of available sidebar width, perfectly aligning borders with the file list view!).

---

### 2. Right Options Panel
* **Container**: `VerticalScroll(id="content")`
  * **Width**: `1fr` (takes up all remaining width left by the sidebar, which is `WindowWidth - 38`).
  * **Height**: `1fr` (fills the remaining screen height above the bottom execution log).

---

### 3. Sizing Columns in the Grid
* **Main Grid Container**: `Horizontal(id="columns-container")`
  * **Width**: `1fr` (fills `#content`).
  * **Height**: Stretches dynamically to fill the available height (`height: 1fr;`), with a minimum of `42` lines (`min-height: 42;`) so form inputs never overflow or get squished.
* **Column 1 (`#col1`)**:
  * **Width**: **Fixed `50` cells** (`width: 50;`).
  * **Height**: Stretches to `100%` of parent height.
  * Contains the tool select dropdown, the input PNG path field (dynamic syncing), and output directory field.
* **Column 2 (`#col2`)**:
  * **Width**: **Fixed `55` cells** (`width: 55;`).
  * **Height**: Stretches to `100%` of parent height.
  * Contains a `ContentSwitcher` showing dynamic `FormGroup` parameters depending on the active tool.
* **Column 3 (`#col3`)**:
  * **Width**: `1fr` (receives whatever width is left over: `(WindowWidth - 38) - 105`).
  * **Height**: Stretches to `100%` of parent height.
  * **Column 3 Inner Components**:
    - **Buttons Panel (`FormGroup`, class: `.form-group`)**: Constrained to a **Fixed Max-Height of `12` rows** (`max-height: 12;`). Contains control triggers ("Run Active Tool", "Analyze Selected").
    - **Analysis Preview (`#analysis-log`, ID: `#analysis-log`)**: Stretches to `height: 1fr;` with a **Fixed Max-Height of `20` rows** (`max-height: 20;`). Displays a real-time text summary table of the selected PNG file diagnostics.

---

## 🎨 Color Palette & Premium Theme

The TUI will implement a curated dark-mode theme to match the retro blitter feel:
- **Background**: Deep Indigo/Navy Space (`#0f111a`)
- **Sidebar Accent**: Dark Slate (`#141622`)
- **Borders & Grids**: Sleek Cobalt (`#23263b`)
- **Primary Text**: Ice Blue (`#a6accd`)
- **Primary Accents/Headers**: Bright Cyan (`#00f0ff`)
- **Success Indicators**: Neon Emerald (`#10b981`)
- **Warnings/Alerts**: Vivid Gold/Amber (`#f59e0b`)
