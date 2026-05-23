#!/usr/bin/env python3
import os
import sys
import re
from pathlib import Path
from PIL import Image

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import (
    Header,
    Footer,
    Label,
    Input,
    Checkbox,
    Select,
    Button,
    RichLog,
    ListView,
    ListItem,
    ContentSwitcher,
)
from textual.binding import Binding

from png_tools.generate_mask import generate_mask
from png_tools.generate_preshift import generate_preshift
from png_tools.plowman.generate_collision_map import generate_tilemap as plowman_generate_tilemap
from png_tools.pacman.generate_collision_map import generate_tilemap as pacman_generate_tilemap


class FormGroup(Vertical):
    """A container with a border title for grouped options."""
    def __init__(self, border_title: str = "", **kwargs):
        super().__init__(**kwargs)
        self.border_title = border_title


class LogRedirector:
    """Redirects stdout/stderr writes directly into a Textual RichLog widget, removing ANSI escapes."""
    def __init__(self, log_widget):
        self.log_widget = log_widget
        self.buffer = ""
        self.ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

    def write(self, data):
        self.buffer += data
        while "\n" in self.buffer:
            line, self.buffer = self.buffer.split("\n", 1)
            # Remove ANSI colors/styling from line before writing
            clean_line = self.ansi_escape.sub('', line)
            self.log_widget.write(clean_line)

    def flush(self):
        pass


class PNGToolsTUIApp(App):
    """A premium, modern Textual terminal interface for the png_tools suite."""

    TITLE = "PNG Tools Suite TUI"
    SUBTITLE = "Configure and execute blitter & collision map generators interactively"

    CSS = """
    Screen {
        background: #0f111a;
        color: #a6accd;
    }

    #main-layout {
        layout: horizontal;
        height: 1fr;
        max-height: 44;
    }

    #sidebar {
        width: 38;
        height: 100%;
        background: #141622;
        border-right: tall #23263b;
        padding: 1;
    }

    #content {
        width: 1fr;
        height: 100%;
        background: #0f111a;
        padding: 1;
    }

    #columns-container {
        layout: horizontal;
        height: 1fr;
        min-height: 42;
        margin-bottom: 1;
    }

    .column {
        height: 100%;
        padding-right: 1;
    }

    #col1 {
        width: 50;
    }

    #col2 {
        width: 55;
    }

    #col3 {
        width: 1fr;
    }

    .section-title {
        text-style: bold;
        color: #00f0ff;
        margin-bottom: 1;
        background: #1b1e2e;
        padding: 0 1;
        height: 1;
    }

    .form-group {
        background: #151825;
        border: round white;
        padding: 1;
        margin-bottom: 1;
    }

    #col1 .form-group {
        max-height: 16;
    }

    #col2 .form-group {
        max-height: 24;
    }

    #col3 .form-group {
        max-height: 12;
    }

    .form-row {
        layout: horizontal;
        height: 3;
        margin-bottom: 1;
        content-align: left middle;
    }

    .form-label {
        width: 18;
        color: #828bb8;
        content-align: left middle;
    }

    .form-input {
        width: 1fr;
    }

    .form-checkbox {
        width: 1fr;
    }

    ListView {
        background: #0a0b10;
        border: round #23263b;
        height: 16;
        margin-bottom: 1;
    }

    ListItem {
        padding: 0 1;
        color: #a6accd;
    }

    ListItem:hover {
        background: #1c1e30;
    }

    ListItem.--highlight {
        background: #00f0ff;
        color: #0f111a;
        text-style: bold;
    }

    #info-panel {
        background: #0d0f18;
        border: round #1e2133;
        padding: 1;
        height: 1fr;
        max-height: 20;
        width: 1fr;
        color: #717cbe;
    }

    Button {
        width: 1fr;
        height: 3;
        border: none;
        text-style: bold;
        margin-bottom: 1;
    }

    #btn-run {
        background: #00f0ff;
        color: #0f111a;
    }

    #btn-run:hover {
        background: #00c8d6;
        color: #0f111a;
    }

    #btn-analyze {
        background: #10b981;
        color: white;
    }

    #btn-analyze:hover {
        background: #059669;
    }

    #analysis-log {
        background: #0a0b10;
        border: round #23263b;
        height: 1fr;
        max-height: 20;
        margin-top: 1;
        margin-bottom: 1;
    }

    #logs-container {
        height: 1fr;
        min-height: 12;
        border-top: tall #23263b;
        background: #0a0b10;
        padding: 0 1;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("r", "run_tool", "Run Tool", show=True),
        Binding("a", "analyze_file", "Analyze Target", show=True),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.png_files = []
        self.scan_files()

    def scan_files(self):
        """Scan the png/ directory for valid source PNG files."""
        png_dir = Path("png")
        if not png_dir.exists():
            return

        for f in png_dir.iterdir():
            if f.is_file() and f.suffix.lower() == ".png":
                # Exclude obvious generated output files to prevent clutter
                name_lower = f.name.lower()
                if any(suffix in name_lower for suffix in ["_mask.png", "_tilemap.png", "_shifted.png", "_shifted_reverse.png"]):
                    continue
                self.png_files.append(f)

        self.png_files.sort(key=lambda p: p.name.lower())

    def compose(self) -> ComposeResult:
        yield Header()

        with Container(id="main-layout"):
            # Left Sidebar: file selection & file preview
            with Vertical(id="sidebar"):
                yield Label(" PNG Source Files", classes="section-title")
                
                # File List
                self.file_list = ListView(*[
                    ListItem(Label(f.name), id=f"png_{i}")
                    for i, f in enumerate(self.png_files)
                ], id="file-list")
                yield self.file_list

                # Info/Details Panel
                yield Label(" Selected File Details", classes="section-title")
                self.info_label = Label(
                    "[dim]Select a PNG file from the list above to view metadata and auto-fill configuration parameters.[/dim]",
                    id="info-panel"
                )
                yield self.info_label

            # Right Panel: options form
            with VerticalScroll(id="content"):
                yield Label(" Tool & Configurations", classes="section-title")

                with Horizontal(id="columns-container"):
                    # Column 1: General configuration
                    with Vertical(id="col1", classes="column"):
                        with FormGroup(border_title="Tool & Destination Selection", classes="form-group"):
                            with Horizontal(classes="form-row"):
                                yield Label("Active Tool:", classes="form-label")
                                tool_options = [
                                    ("Generate Mask", "mask"),
                                    ("Generate Preshift", "preshift"),
                                    ("Plowman Collision", "plowman-map"),
                                    ("Pac-Man Collision", "pacman-map"),
                                ]
                                self.select_tool = Select(tool_options, value="mask", classes="form-input")
                                yield self.select_tool

                            with Horizontal(classes="form-row"):
                                yield Label("Target PNG:", classes="form-label")
                                self.input_png = Input(placeholder="No PNG selected", classes="form-input")
                                yield self.input_png

                            with Horizontal(classes="form-row"):
                                yield Label("Output Dir:", classes="form-label")
                                self.input_output_dir = Input(value="png", placeholder="e.g. png", classes="form-input")
                                yield self.input_output_dir

                    # Column 2: Tool-specific configuration
                    with Vertical(id="col2", classes="column"):
                        with ContentSwitcher(initial="switch-mask") as switcher:
                            self.content_switcher = switcher

                            # 1. Mask Generator Panel (No configuration needed)
                            with FormGroup(border_title="2-Bit Mask Configuration", id="switch-mask", classes="form-group"):
                                yield Label(
                                    "[bold cyan]Mask Generation[/bold cyan]\n\n"
                                    "Creates a 2-bit transparency mask.\n"
                                    "• Index 0: Transparent\n"
                                    "• Index 1: White (Opaque mask)\n"
                                    "• Index 2: Black\n\n"
                                    "Saves result as [dim]{basename}_mask.png[/dim].",
                                    classes="form-input"
                                )

                            # 2. Preshift Options Panel
                            with FormGroup(border_title="Sprite Preshifter Options", id="switch-preshift", classes="form-group"):
                                with Horizontal(classes="form-row"):
                                    yield Label("Shift Count:", classes="form-label")
                                    self.input_shifts = Input(value="16", placeholder="e.g. 16", classes="form-input")
                                    yield self.input_shifts

                                with Horizontal(classes="form-row"):
                                    yield Label("Buffer Width:", classes="form-label")
                                    self.input_buffer = Input(value="16", placeholder="e.g. 16", classes="form-input")
                                    yield self.input_buffer

                                with Horizontal(classes="form-row"):
                                    yield Label("Reverse Shift:", classes="form-label")
                                    self.cb_reverse = Checkbox("Reverse (Left-Shift)", value=False, classes="form-checkbox")
                                    yield self.cb_reverse

                            # 3. Collision Map Options Panel
                            with FormGroup(border_title="Collision Map Options", id="switch-collision", classes="form-group"):
                                with Horizontal(classes="form-row"):
                                    yield Label("Tile Width:", classes="form-label")
                                    self.input_tile_w = Input(value="16", placeholder="e.g. 16", classes="form-input")
                                    yield self.input_tile_w

                                with Horizontal(classes="form-row"):
                                    yield Label("Tile Height:", classes="form-label")
                                    self.input_tile_h = Input(value="16", placeholder="e.g. 16", classes="form-input")
                                    yield self.input_tile_h

                                with Horizontal(classes="form-row"):
                                    yield Label("Tolerance:", classes="form-label")
                                    self.input_tolerance = Input(value="0", placeholder="e.g. 2px or 0", classes="form-input")
                                    yield self.input_tolerance

                                with Horizontal(classes="form-row"):
                                    yield Label("Preview Scale:", classes="form-label")
                                    self.input_scale = Input(value="3", placeholder="e.g. 3", classes="form-input")
                                    yield self.input_scale

                                with Horizontal(classes="form-row"):
                                    yield Label("Objects Sheet:", classes="form-label")
                                    self.input_objects = Input(placeholder="png/pacman_map_objects.png", classes="form-input")
                                    yield self.input_objects

                    # Column 3: Actions & Preview
                    with Vertical(id="col3", classes="column"):
                        with FormGroup(border_title="Execution Triggers", classes="form-group"):
                            yield Button("Run Active Tool (R)", id="btn-run")
                            yield Button("Analyze Target (A)", id="btn-analyze")

                        yield Label(" Output Preview & Details", classes="section-title")
                        self.analysis_log = RichLog(highlight=True, markup=True, id="analysis-log")
                        yield self.analysis_log

        # Bottom section: interactive logs
        with Vertical(id="logs-container"):
            yield Label(" Execution Terminal Logs", classes="section-title")
            self.execution_log = RichLog(highlight=True, markup=True)
            yield self.execution_log

        yield Footer()

    def on_mount(self) -> None:
        self.execution_log.write("[bold green]PNG Tools Suite TUI initialized successfully.[/bold green]")
        self.execution_log.write("Select a PNG file in the sidebar list to get started.")

        self.analysis_log.write("[bold cyan]No analysis run yet.[/bold cyan]")
        self.analysis_log.write("Highlight a file and press [bold green]Analyze (A)[/bold green] to examine PNG details.")

        # Focus file list on launch
        self.file_list.focus()

    def on_list_view_selected(self, message: ListView.Selected) -> None:
        self.handle_list_selection(message)

    def on_list_view_highlighted(self, message: ListView.Highlighted) -> None:
        self.handle_list_selection(message)

    def handle_list_selection(self, message) -> None:
        """Process selections or navigation updates on the PNG file list."""
        if not message.item:
            return

        idx = int(message.item.id.split("_")[1])
        selected_file = self.png_files[idx]

        # Avoid redundant configuration triggers
        if self.input_png.value == str(selected_file):
            return

        self.auto_configure(selected_file)

    def auto_configure(self, png_path: Path):
        """Dynamically configure the active tool and form parameters based on the selected file."""
        stem_clean = png_path.stem.lower()

        # Update core path input
        self.input_png.value = str(png_path)

        # Smart-guess the correct tool mode
        guessed_tool = "mask"  # default
        if "sprite" in stem_clean:
            guessed_tool = "preshift"
        elif "stage" in stem_clean:
            if "plowman" in stem_clean:
                guessed_tool = "plowman-map"
            else:
                guessed_tool = "pacman-map"
        elif "tiles" in stem_clean:
            guessed_tool = "mask"

        self.select_tool.value = guessed_tool

        # Output directory smart default
        if guessed_tool in ["mask", "preshift"]:
            self.input_output_dir.value = "png"
        else:
            self.input_output_dir.value = "collision"

        # Populate sidebar info card
        file_size = png_path.stat().st_size
        try:
            with Image.open(png_path) as img:
                width, height = img.size
                mode = img.mode
        except Exception:
            width, height = "Unknown", "Unknown"
            mode = "Unknown"

        info = f"[bold white]{png_path.name}[/bold white]\n"
        info += f"  Size: {file_size:,} bytes\n"
        info += f"  Dims: {width} x {height} px\n"
        info += f"  Mode: {mode}\n\n"
        info += f"  Suggested Tool:\n  [cyan]{guessed_tool.upper()}[/cyan]\n\n"
        info += "[dim cyan]Press 'R' to run tool\nPress 'A' to analyze file[/dim cyan]"
        
        self.info_label.update(info)

        # Clear analysis log with instructions
        self.analysis_log.clear()
        self.analysis_log.write(f"[bold cyan]Selected Target: {png_path.name}[/bold cyan]")
        self.analysis_log.write("-" * 40)
        self.analysis_log.write("Click [bold green]Analyze Target (A)[/bold green] or press key [bold cyan]A[/bold cyan] to analyze file format and options.")

    def on_select_changed(self, event: Select.Changed) -> None:
        """Trigger view updates and defaults when switching active tools."""
        if event.select == self.select_tool:
            val = event.value
            if not val:
                return

            if val == "mask":
                self.content_switcher.current = "switch-mask"
                self.input_output_dir.value = "png"
            elif val == "preshift":
                self.content_switcher.current = "switch-preshift"
                self.input_output_dir.value = "png"
            elif val in ["plowman-map", "pacman-map"]:
                self.content_switcher.current = "switch-collision"
                self.input_output_dir.value = "collision"
                self.guess_objects_sheet()

    def guess_objects_sheet(self):
        """Search and configure optimal object mapping sheets."""
        bpl_file = self.input_png.value
        if not bpl_file:
            return

        bpl_path = Path(bpl_file)
        tool_val = self.select_tool.value

        if "pacman" in tool_val:
            guess = "png/pacman_map_objects.png"
        elif "plowman" in tool_val:
            guess = "png/plowman_map_objects.png"
        else:
            guess = f"png/{bpl_path.stem}-objects.png"
            if not os.path.exists(guess):
                guess = "png/pacman_map_objects.png"

        self.input_objects.value = guess

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-run":
            self.action_run_tool()
        elif event.button.id == "btn-analyze":
            self.action_analyze_file()

    def parse_px_int(self, val) -> int:
        """Converts string expressions like '2px' to integer numbers."""
        if isinstance(val, int):
            return val
        val_str = str(val).strip().lower()
        if val_str.endswith('px'):
            val_str = val_str[:-2]
        try:
            return int(val_str)
        except ValueError:
            return 0

    def action_run_tool(self) -> None:
        """Run the currently selected tool with options compiled from the form inputs."""
        target = self.input_png.value
        if not target or not os.path.exists(target):
            self.execution_log.write("[bold red]Error: Target PNG file does not exist![/bold red]")
            return

        tool = self.select_tool.value
        output_dir = self.input_output_dir.value or "png"

        self.execution_log.write("-" * 60)
        self.execution_log.write(f"[bold green]Executing Tool '{tool}' on {Path(target).name}...[/bold green]")

        # Setup standard output and standard error redirection
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        redirector = LogRedirector(self.execution_log)
        sys.stdout = redirector
        sys.stderr = redirector

        try:
            if tool == "mask":
                generate_mask(target, output_dir)
            elif tool == "preshift":
                # Read parameter inputs
                shifts = int(self.input_shifts.value or 16)
                buf_size = int(self.input_buffer.value or 16)
                reverse = self.cb_reverse.value

                name_only = Path(target).stem
                suffix_filename = f"{name_only}_shifted_reverse.png" if reverse else f"{name_only}_shifted.png"
                final_out = os.path.join(output_dir, suffix_filename)

                generate_preshift(target, final_out, num_shifts=shifts, buffer_size=buf_size, reverse_shift=reverse)
            elif tool == "plowman-map":
                tile_w = int(self.input_tile_w.value or 16)
                tile_h = int(self.input_tile_h.value or 16)
                tol = self.parse_px_int(self.input_tolerance.value or 0)
                scale = int(self.input_scale.value or 3)
                obj_sprite = self.input_objects.value or None

                plowman_generate_tilemap(target, output_dir, tile_w, tile_h, scale, tol, obj_sprite)
            elif tool == "pacman-map":
                tile_w = int(self.input_tile_w.value or 16)
                tile_h = int(self.input_tile_h.value or 16)
                tol = self.parse_px_int(self.input_tolerance.value or 0)
                scale = int(self.input_scale.value or 3)
                obj_sprite = self.input_objects.value or None

                pacman_generate_tilemap(target, output_dir, tile_w, tile_h, scale, tol, obj_sprite)

            self.execution_log.write("[bold green]🎉 SUCCESS! Execution completed successfully.[/bold green]")
        except Exception as e:
            self.execution_log.write(f"[bold red]CRITICAL EXCEPTION during tool run: {e}[/bold red]")
            import traceback
            for line in traceback.format_exc().splitlines():
                self.execution_log.write(f"[red]{line}[/red]")
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

    def action_analyze_file(self) -> None:
        """Perform non-destructive diagnostics on target file formats, color systems, and option alignments."""
        target = self.input_png.value
        if not target or not os.path.exists(target):
            self.execution_log.write("[bold red]Error: Target PNG file does not exist![/bold red]")
            return

        tool = self.select_tool.value
        self.execution_log.write(f"Diagnosing structure of [bold yellow]{Path(target).name}[/bold yellow]...")

        self.analysis_log.clear()
        self.analysis_log.write(f"[bold yellow]File Diagnosis: {Path(target).name}[/bold yellow]")
        self.analysis_log.write("=" * 45)

        try:
            with Image.open(target) as img:
                w, h = img.size
                mode = img.mode
                info_dict = img.info

            self.analysis_log.write(f"  Dimensions:  [cyan]{w} x {h} pixels[/cyan]")
            self.analysis_log.write(f"  Color Mode:  [cyan]{mode}[/cyan]")
            
            # Format-specific diagnoses
            if tool == "mask":
                self.analysis_log.write("\n[bold cyan]Mask Diagnostic Report:[/bold cyan]")
                if mode == "P":
                    self.analysis_log.write("  [green]✓ Clean indexed PNG palette found.[/green]")
                    self.analysis_log.write("  Transparent index (transparency): " + str(info_dict.get("transparency", "None")))
                elif mode == "RGBA":
                    self.analysis_log.write("  [yellow]⚠ Alpha-channel layout detected.[/yellow]")
                    self.analysis_log.write("  Generator will evaluate alpha transparency during conversion.")
                else:
                    self.analysis_log.write("  [yellow]⚠ RGB/direct color layout detected.[/yellow]")
                    self.analysis_log.write("  Pure black (0,0,0) will default to transparent pixels.")

            elif tool == "preshift":
                self.analysis_log.write("\n[bold cyan]Sprite Preshift Diagnostic Report:[/bold cyan]")
                if mode == "P":
                    self.analysis_log.write("  [green]✓ Clean indexed PNG palette detected.[/green]")
                    self.analysis_log.write("  Palette size preservation is guaranteed.")
                else:
                    self.analysis_log.write("  [bold red]✖ Critical error: Image is not in mode 'P'.[/bold red]")
                    self.analysis_log.write("  This tool strictly requires 8-bit indexed palette PNGs.")

            elif tool in ["plowman-map", "pacman-map"]:
                self.analysis_log.write("\n[bold cyan]Collision Map Diagnostic Report:[/bold cyan]")
                tile_w = int(self.input_tile_w.value or 16)
                tile_h = int(self.input_tile_h.value or 16)
                
                cols = w // tile_w
                rows = h // tile_h
                rem_w = w % tile_w
                rem_h = h % tile_h

                self.analysis_log.write(f"  Target Tile Size: [cyan]{tile_w}x{tile_h}[/cyan]")
                self.analysis_log.write(f"  Computed Grid:    [cyan]{cols} Columns x {rows} Rows[/cyan] ({cols * rows} tiles)")
                
                if rem_w > 0 or rem_h > 0:
                    self.analysis_log.write(f"  [yellow]⚠ Size Warning: Image is not a clean multiple of tile size.[/yellow]")
                    self.analysis_log.write(f"    Leftover space: {rem_w}px horizontal, {rem_h}px vertical.")
                else:
                    self.analysis_log.write("  [green]✓ Image dimensions match grid layout perfectly.[/green]")

                obj_sprite = self.input_objects.value
                if obj_sprite and os.path.exists(obj_sprite):
                    self.analysis_log.write(f"  [green]✓ Map objects sheet found:[/green] [dim]{Path(obj_sprite).name}[/dim]")
                elif obj_sprite:
                    self.analysis_log.write(f"  [yellow]⚠ Objects sheet specified but file not found.[/yellow]")
                else:
                    self.analysis_log.write("  [dim]No mapping objects sheet configured.[/dim]")

            self.analysis_log.write("-" * 45)
            self.analysis_log.write("[bold green]Diagnosis complete. System checks passed.[/bold green]")
        except Exception as e:
            self.analysis_log.write(f"[bold red]Diagnostics failure: {e}[/bold red]")

    def action_quit(self) -> None:
        self.exit()


def main():
    app = PNGToolsTUIApp()
    app.run()


if __name__ == "__main__":
    main()
