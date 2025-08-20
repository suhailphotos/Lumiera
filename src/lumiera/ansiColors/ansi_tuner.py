
#!/usr/bin/env python3
# ansi_tuner.py
# A tiny TUI to live-tune the 16 ANSI colors via OSC 4 and preview code/styles.
#
# Controls (read this first):
#   - 0..9, a..f : pick color index 0..15
#   - ←/→        : select channel (H, S, L)
#   - ↑/↓        : nudge selected channel by small step
#   - SHIFT+↑/↓  : nudge by big step
#   - [ / ]      : previous / next color
#   - space      : toggle link brights (when on, bright = lighter version of base 0..7)
#   - s          : save palette to palette.txt
#   - r          : reset to built-in Catppuccin Mocha preset
#   - q          : quit
#
# Notes:
#   - Works best in terminals that support OSC 4/10/11 (Ghostty, iTerm2, WezTerm, kitty, Alacritty, ...).
#   - If running under tmux, ensure your tmux passes OSC sequences through (modern tmux usually does).
#   - The preview shows attributes (bold/italic/underline), swatches, and a small multi-language snippet.
#
# No external deps. Python 3.8+ recommended.

import curses
import colorsys
import os
import sys
import re
import time

PALETTE_FILE = "palette.txt"

# --- Helper: hex <-> rgb <-> hsl ---

def clamp(x, lo=0.0, hi=1.0):
    return lo if x < lo else hi if x > hi else x

def hex_to_rgb(hexstr):
    h = hexstr.strip().lstrip('#')
    if len(h) != 6 or not re.fullmatch(r'[0-9a-fA-F]{6}', h):
        raise ValueError(f"Bad hex: {hexstr}")
    r = int(h[0:2], 16)
    g = int(h[2:4], 16)
    b = int(h[4:6], 16)
    return r, g, b

def rgb_to_hex(rgb):
    r, g, b = rgb
    return f"{r:02x}{g:02x}{b:02x}"

def rgb_to_hsl(rgb):
    r, g, b = rgb
    h, l, s = colorsys.rgb_to_hls(r/255.0, g/255.0, b/255.0)
    # colorsys uses HLS; we want HSL for UI labeling but keep the order we manipulate
    return (h, s, l)  # returning as H, S, L

def hsl_to_rgb(hsl):
    h, s, l = hsl
    r, g, b = colorsys.hls_to_rgb(h, l, s)  # note HLS!
    return (int(round(r*255)), int(round(g*255)), int(round(b*255)))

def hex_to_hsl(hexstr):
    return rgb_to_hsl(hex_to_rgb(hexstr))

def hsl_to_hex(hsl):
    return rgb_to_hex(hsl_to_rgb(hsl))


# --- Built-in Catppuccin Mocha-ish preset for 16 ANSI slots ---
# These values are taken from common Catppuccin Mocha terminal ports; treat as a good starting point.
# You will tweak them live anyway.
CATPPUCCIN_MOCHA_ANSI = [
    "1e1e2e",  # 0 black   (base)
    "f38ba8",  # 1 red
    "a6e3a1",  # 2 green
    "f9e2af",  # 3 yellow
    "89b4fa",  # 4 blue
    "cba6f7",  # 5 magenta
    "94e2d5",  # 6 cyan
    "cdd6f4",  # 7 white   (text)
    "45475a",  # 8 br_black  (surface1)
    "eba0ac",  # 9 br_red    (maroon)
    "94e2b6",  # 10 br_green (slightly brighter green-ish)
    "ffe5b8",  # 11 br_yellow
    "b3c8ff",  # 12 br_blue
    "d0b3ff",  # 13 br_magenta
    "b5f1e3",  # 14 br_cyan
    "ffffff",  # 15 br_white
]


# --- Terminal control: apply 16 colors + set fg/bg from indices 7/0 ---

def osc4_set_color(index, hexstr):
    rr, gg, bb = hex_to_rgb(hexstr)
    return f"\033]4;{index};rgb:{rr:02x}/{gg:02x}/{bb:02x}\007"

def osc10_set_fg(hexstr):
    rr, gg, bb = hex_to_rgb(hexstr)
    return f"\033]10;rgb:{rr:02x}/{gg:02x}/{bb:02x}\007"

def osc11_set_bg(hexstr):
    rr, gg, bb = hex_to_rgb(hexstr)
    return f"\033]11;rgb:{rr:02x}/{gg:02x}/{bb:02x}\007"

def apply_palette(palette_hex):
    # palette_hex: list of 16 hex strings (RRGGBB)
    out = []
    for i, hx in enumerate(palette_hex[:16]):
        out.append(osc4_set_color(i, hx))
    # default fg from 7, bg from 0
    out.append(osc10_set_fg(palette_hex[7]))
    out.append(osc11_set_bg(palette_hex[0]))
    sys.stdout.write(''.join(out))
    sys.stdout.flush()


# --- Load/save palette.txt (allows comments and blank lines) ---

def load_palette_from_file(path):
    if not os.path.exists(path):
        return None
    colors = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            line = line.lstrip('#').strip()
            if re.fullmatch(r'[0-9a-fA-F]{6}', line):
                colors.append(line.lower())
            if len(colors) == 16:
                break
    if len(colors) != 16:
        return None
    return colors

def save_palette_to_file(path, palette):
    header = """\
# palette.txt — 16 ANSI colors (indexes 0..15). Lines below are hex RRGGBB.
# Comments are allowed and ignored. Extra lines are ignored.
# 0..7  = normal  (black, red, green, yellow, blue, magenta, cyan, white)
# 8..15 = bright  (br_black .. br_white)
"""
    with open(path, 'w', encoding='utf-8') as f:
        f.write(header)
        for i, hx in enumerate(palette[:16]):
            f.write(f"{hx}\n")


# --- Preview content ---

PREVIEW_SNIPPET = r'''# Python
def fib(n: int) -> int:
    # comment: naive recursion
    return 1 if n < 2 else fib(n-1) + fib(n-2)

# Shell
# $ git status && echo "ok"
# JSON
{ "name": "catppuccin", "flavor": "mocha", "ok": true }

/* C */
#include <stdio.h> // underline, italic, bold samples below
int main(void) {
    printf("Hello, [3mitalic[0m, [1mbold[0m, [4munderline[0m!
");
    return 0;
}
'''

def sgr(code): return f"[{code}m"
RST = sgr(0)

def build_palette_swatches():
    # 0..15 : show bg and fg squares using 40..47/100..107 and 30..37/90..97
    lines = []
    def fg_code(i):
        return 30 + i if i < 8 else 90 + (i-8)
    def bg_code(i):
        return 40 + i if i < 8 else 100 + (i-8)
    for row in (range(0,8), range(8,16)):
        parts = []
        for i in row:
            parts.append(f"{sgr(bg_code(i))}  {RST}")  # bg block
            parts.append(f"{sgr(fg_code(i))}██{RST}")  # fg block
        lines.append(' '.join(parts))
    return lines

def build_attr_matrix():
    attrs = [
        ("Normal", ""),
        ("Bold", "1"),
        ("Dim", "2"),
        ("Italic", "3"),
        ("Underline", "4"),
    ]
    def fg_code(i):
        return 30 + i if i < 8 else 90 + (i-8)
    lines = []
    for title, a in attrs:
        row = [f"{title:<9} "]
        for i in range(16):
            row.append(f"{sgr(a)}{sgr(fg_code(i))}██{RST}")
        lines.append(''.join(row))
    return lines


# --- TUI ---

H_LABELS = ["H", "S", "L"]

class TUI:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        curses.curs_set(0)
        self.height, self.width = self.stdscr.getmaxyx()

        # Load palette or default
        pal = load_palette_from_file(PALETTE_FILE)
        self.palette = pal if pal else CATPPUCCIN_MOCHA_ANSI[:]

        # Internal HSL representation for editing
        self.hsl = [list(hex_to_hsl(hx)) for hx in self.palette]

        # Which color index and which channel 0(H)/1(S)/2(L)
        self.idx = 4  # start at blue
        self.chan = 2 # start on Lightness
        self.link_brights = False  # if True, 8..15 mirror 0..7 with +lightness

        # Steps for up/down
        self.small_step = [1/360, 0.01, 0.02]  # H, S, L
        self.big_step   = [5/360, 0.05, 0.08]

        # Initial apply
        self.apply_now()

    def apply_now(self):
        # If link brights, derive 8..15 from 0..7 with an L+ boost (clamped)
        if self.link_brights:
            boost = 0.12
            derived = []
            for i in range(8):
                h, s, l = self.hsl[i]
                l2 = clamp(l + boost, 0.0, 1.0)
                derived.append([h, s, l2])
            effective_hsl = self.hsl[:8] + derived
        else:
            effective_hsl = self.hsl

        # Apply to terminal
        pal_hex = [hsl_to_hex(tuple(hsl)) for hsl in effective_hsl[:16]]
        apply_palette(pal_hex)

        # Also keep .palette synced so we can save easily
        self.palette = pal_hex

    def draw(self):
        self.stdscr.erase()

        # Title / help
        help1 = "ansi_tuner — arrows=H/S/L adjust, 0–f pick color, [ ] prev/next, SPACE link-brights, S save, R reset, Q quit"
        self.stdscr.addstr(0, 0, help1[:self.width-1])

        # Current selection line
        current = f" idx={self.idx:02d} hex=#{self.palette[self.idx]}  HSL="
        h, s, l = self.hsl[self.idx]
        hsl_txt = f"{int(round(h*360))}°, {int(round(s*100))}%, {int(round(l*100))}%"
        current += hsl_txt
        current += f"   link_brights={'ON' if self.link_brights else 'OFF'}"
        self.stdscr.addstr(1, 0, current[:self.width-1])

        # Channel indicators
        chan_line = "Channels: "
        for i, lbl in enumerate(H_LABELS):
            if i == self.chan:
                chan_line += f"[{lbl}] "
            else:
                chan_line += f" {lbl}  "
        self.stdscr.addstr(2, 0, chan_line[:self.width-1])

        # Swatches
        y = 4
        for line in build_palette_swatches():
            if y < self.height - 1:
                self.stdscr.addstr(y, 0, line[:self.width-1])
            y += 1

        # Attr matrix
        y += 1
        for line in build_attr_matrix():
            if y < self.height - 1:
                self.stdscr.addstr(y, 0, line[:self.width-1])
            y += 1

        # Code snippet (bounded by screen)
        y += 1
        for ln in PREVIEW_SNIPPET.splitlines():
            if y < self.height - 1:
                self.stdscr.addstr(y, 0, ln[:self.width-1])
            y += 1

        self.stdscr.refresh()

    def run(self):
        while True:
            self.draw()
            ch = self.stdscr.getch()

            # Quit
            if ch in (ord('q'), ord('Q')):
                break

            # Save
            elif ch in (ord('s'), ord('S')):
                save_palette_to_file(PALETTE_FILE, self.palette)

            # Reset
            elif ch in (ord('r'), ord('R')):
                self.palette = CATPPUCCIN_MOCHA_ANSI[:]
                self.hsl = [list(hex_to_hsl(hx)) for hx in self.palette]
                self.apply_now()

            # Link brights
            elif ch == ord(' '):
                self.link_brights = not self.link_brights
                self.apply_now()

            # Prev/next color
            elif ch == ord('['):
                self.idx = (self.idx - 1) % 16
            elif ch == ord(']'):
                self.idx = (self.idx + 1) % 16

            # Number/hex keys to select 0..15
            elif ch in range(ord('0'), ord('9')+1):
                self.idx = int(chr(ch), 16)
            elif ch in range(ord('a'), ord('f')+1):
                self.idx = int(chr(ch), 16)
            elif ch in range(ord('A'), ord('F')+1):
                self.idx = int(chr(ch), 16)

            # Left/right switch channel
            elif ch == curses.KEY_LEFT:
                self.chan = (self.chan - 1) % 3
            elif ch == curses.KEY_RIGHT:
                self.chan = (self.chan + 1) % 3

            # Up/down adjust channel (small/big)
            elif ch == curses.KEY_UP or ch == curses.KEY_DOWN:
                # Detect shift isn't portable in curses; offer PageUp/PageDown for big steps.
                step = self.small_step[self.chan]
                sign = 1.0 if ch == curses.KEY_UP else -1.0
                h, s, l = self.hsl[self.idx]
                if self.chan == 0:   # H
                    h = (h + sign*step) % 1.0
                elif self.chan == 1: # S
                    s = clamp(s + sign*step, 0.0, 1.0)
                else:                # L
                    l = clamp(l + sign*step, 0.0, 1.0)
                self.hsl[self.idx] = [h, s, l]
                self.apply_now()

            # PageUp/PageDown as BIG steps
            elif ch in (curses.KEY_PPAGE, curses.KEY_NPAGE):
                sign = 1.0 if ch == curses.KEY_PPAGE else -1.0
                step = self.big_step[self.chan]
                h, s, l = self.hsl[self.idx]
                if self.chan == 0:
                    h = (h + sign*step) % 1.0
                elif self.chan == 1:
                    s = clamp(s + sign*step, 0.0, 1.0)
                else:
                    l = clamp(l + sign*step, 0.0, 1.0)
                self.hsl[self.idx] = [h, s, l]
                self.apply_now()

            # Ignore other keys
            else:
                pass


def main():
    # Try to apply initial palette (file or builtin) before curses
    pal = load_palette_from_file(PALETTE_FILE) or CATPPUCCIN_MOCHA_ANSI
    apply_palette(pal)

    curses.wrapper(lambda stdscr: TUI(stdscr).run())

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
