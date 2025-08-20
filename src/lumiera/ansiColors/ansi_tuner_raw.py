#!/usr/bin/env python3
# ansi_tuner_raw.py — combo previews + all-background grid + cleaner swatches
import sys, os, re, colorsys, termios, tty, select

PALETTE_FILE = "palette.txt"

def clamp(x, lo=0.0, hi=1.0): return lo if x<lo else hi if x>hi else x
def hex_to_rgb(hexstr):
    h = hexstr.strip().lstrip('#'); return int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
def rgb_to_hex(rgb): r,g,b = rgb; return f"{r:02x}{g:02x}{b:02x}"
def rgb_to_hsl(rgb):
    r,g,b = rgb; h,l,s = colorsys.rgb_to_hls(r/255.0, g/255.0, b/255.0); return (h,s,l)
def hsl_to_rgb(hsl):
    h,s,l = hsl; r,g,b = colorsys.hls_to_rgb(h,l,s); return int(r*255), int(g*255), int(b*255)
def hex_to_hsl(hx): return rgb_to_hsl(hex_to_rgb(hx))
def hsl_to_hex(hsl): return rgb_to_hex(hsl_to_rgb(hsl))

CATPPUCCIN_MOCHA_ANSI = [
    "1e1e2e","f38ba8","a6e3a1","f9e2af","89b4fa","cba6f7","94e2d5","cdd6f4",
    "45475a","eba0ac","94e2b6","ffe5b8","b3c8ff","d0b3ff","b5f1e3","ffffff",
]

def osc4(i,hx): r,g,b = hex_to_rgb(hx); return f"\033]4;{i};rgb:{r:02x}/{g:02x}/{b:02x}\007"
def osc10(hx): r,g,b = hex_to_rgb(hx); return f"\033]10;rgb:{r:02x}/{g:02x}/{b:02x}\007"
def osc11(hx): r,g,b = hex_to_rgb(hx); return f"\033]11;rgb:{r:02x}/{g:02x}/{b:02x}\007"

def apply_palette(pal):
    out = [osc4(i,hx) for i,hx in enumerate(pal[:16])]
    out.append(osc10(pal[7])); out.append(osc11(pal[0]))
    sys.stdout.write(''.join(out)); sys.stdout.flush()

def load_palette(path):
    if not os.path.exists(path): return None
    cols=[]
    with open(path,'r') as f:
        for line in f:
            t=line.strip()
            if not t or t.startswith('#'): continue
            if re.fullmatch(r'[0-9a-fA-F]{6}',t): cols.append(t.lower())
            if len(cols)==16: break
    return cols if len(cols)==16 else None

def save_palette(path,pal):
    with open(path,'w') as f:
        f.write("# palette.txt — 16 ANSI colors hex RRGGBB per line\n")
        for hx in pal[:16]: f.write(hx+"\n")

def sgr(code): return f"\033[{code}m"
RST = sgr(0)
def fg_code(i): return 30+i if i<8 else 90+(i-8)
def bg_code(i): return 40+i if i<8 else 100+(i-8)

# basic “semantic” roles so the mini snippets react to palette indices
def roles_from_indices(sel_idx, comp_idx):
    return {
        "comment": fg_code(8),           # bright black by default for comments
        "keyword": fg_code(sel_idx),     # selected color drives keywords
        "ident":   fg_code(sel_idx),     # and idents
        "string":  fg_code(comp_idx),    # companion is strings
        "number":  fg_code(comp_idx),    # and numbers
        "punct":   fg_code(7),           # keep punctuation near white for legibility
    }

STYLE = {"bold":"1", "dim":"2", "italic":"3", "underline":"4"}

def seg(text, *codes):
    return "".join(sgr(c) for c in codes if c) + text + RST

def mini_code(sel_idx, comp_idx, flip=False):
    R = roles_from_indices(comp_idx, sel_idx) if flip else roles_from_indices(sel_idx, comp_idx)
    out=[]
    # Python
    out += [seg("# Python\n", R["comment"])]
    out += [seg("def ", R["keyword"])+seg("fib", R["ident"])+seg("(",)+seg("n", R["ident"])+seg(": ")+seg("int", R["keyword"])+seg(") -> ")+seg("int", R["keyword"])+seg(":\n")]
    out += ["    "+seg("# comment: naive recursion\n", R["comment"])]
    out += ["    "+seg("return ", R["keyword"])+seg("1", R["number"])+seg(" if ", R["keyword"])+seg("n", R["ident"])+seg(" < ")+seg("2", R["number"])+seg(" else ", R["keyword"]) +
            seg("fib", R["ident"])+seg("(")+seg("n", R["ident"])+seg("-")+seg("1", R["number"])+seg(")")+seg(" + ")+
            seg("fib", R["ident"])+seg("(")+seg("n", R["ident"])+seg("-")+seg("2", R["number"])+seg(")")+"\n\n"]
    # JSON
    out += [seg("# JSON\n", R["comment"])]
    out += [seg("{ ")+seg("\"name\"", R["string"])+seg(": ")+seg("\"catppuccin\"", R["string"])+seg(", ")+
            seg("\"flavor\"", R["string"])+seg(": ")+seg("\"mocha\"", R["string"])+seg(", ")+
            seg("\"ok\"", R["string"])+seg(": ")+seg("true", R["keyword"])+seg(" }")+ "\n"]
    return "".join(out)

def clear(): sys.stdout.write("\033[H\033[2J"); sys.stdout.flush()

def show(pal_hex,hsl,idx,chan,link_brights, comp_idx):
    h,s,l = hsl[idx]
    clear()
    print(f"idx={idx:02d} #{pal_hex[idx]}   companion={comp_idx:02d} #{pal_hex[comp_idx]}   HSL={int(h*360)}° {int(s*100)}% {int(l*100)}%   link_brights={'ON' if link_brights else 'OFF'}")
    chan_lbl = " ".join(f"[{c}]" if i==chan else c for i,c in enumerate("HSL"))
    print("Channels:", chan_lbl)
    print("(h/l or ←/→ channel • j/k or ↓/↑ step • J/K or PgDn/PgUp big • ,/. prev/next color • {/} companion • s save • space link-brights • q quit)\n")

    # Swatches (two rows, per index: BG████ FG████)
    wide = "█████"
    for row in (range(0,8),range(8,16)):
        line=[]
        for i in row:
            line.append(f"{sgr(bg_code(i))}{wide}{RST}{sgr(fg_code(i))}{wide}{RST}")
        print(" ".join(line))
    print()

    # Attributes per color (wider, spaced)
    def row_for(name, code):
        blocks = " ".join(f"{sgr(code)}{sgr(fg_code(i))}{wide}{RST}" for i in range(16))
        print(f"{name:<10}{blocks}")
    for nm,cd in [("Normal",""),("Bold","1"),("Dim","2"),("Italic","3"),("Underline","4")]:
        row_for(nm, cd)
    print()

    # Pair style grid: fg=selected on bg=companion, then inverse (short words show style)
    sample = ["Aa", seg("Aa","1"), seg("Aa","2"), seg("Aa","3"), seg("Aa","4")]
    print(f"Pair styles  fg={idx:02d} on bg={comp_idx:02d}  |  fg={comp_idx:02d} on bg={idx:02d}")
    left  = " ".join(f"{sgr(fg_code(idx))}{sgr(bg_code(comp_idx))}{t}{RST}" for t in sample)
    right = " ".join(f"{sgr(fg_code(comp_idx))}{sgr(bg_code(idx))}{t}{RST}" for t in sample)
    print(left+"    |    "+right+"\n")

    # Mini code colored two ways (selected vs companion swapped)
    print("Mini code  (keywords/idents = selected, strings/comments = companion):")
    print(mini_code(idx, comp_idx))
    print("Mini code  (flipped roles):")
    print(mini_code(idx, comp_idx, flip=True))

    # All-backgrounds grid: selected color text on every bg 0..15 (styles)
    print("\nSelected color on all backgrounds:")
    for b in range(16):
        cells = [
            "Aa", seg("Aa","1"), seg("Aa","2"), seg("Aa","3"), seg("Aa","4")
        ]
        row = " ".join(f"{sgr(bg_code(b))}{sgr(fg_code(idx))}{t}{RST}" for t in cells)
        print(f"bg {b:02d}: {row}")
    print()

def read_key():
    # returns: 'UP','DN','LT','RT','PGUP','PGDN' or single chars
    dr,_,_ = select.select([sys.stdin],[],[],0.2)
    if not dr: return None
    ch=sys.stdin.read(1)
    if ch!='\x1b': return ch
    # CSI or SS3
    if select.select([sys.stdin],[],[],0.01)[0]:
        ch2=sys.stdin.read(1)
        if ch2=='[':
            ch3=sys.stdin.read(1)
            if   ch3=='A': return 'UP'
            elif ch3=='B': return 'DN'
            elif ch3=='C': return 'RT'
            elif ch3=='D': return 'LT'
            elif ch3=='5' and sys.stdin.read(1)=='~': return 'PGUP'
            elif ch3=='6' and sys.stdin.read(1)=='~': return 'PGDN'
        elif ch2=='O':
            ch3=sys.stdin.read(1)
            if   ch3=='A': return 'UP'
            elif ch3=='B': return 'DN'
            elif ch3=='C': return 'RT'
            elif ch3=='D': return 'LT'
    return 'ESC'

def main():
    fd=sys.stdin.fileno(); old=termios.tcgetattr(fd); tty.setcbreak(fd)
    try:
        pal=load_palette(PALETTE_FILE) or CATPPUCCIN_MOCHA_ANSI[:]
        hsl=[list(hex_to_hsl(hx)) for hx in pal]
        idx,chan,link_brights=4,2,False
        comp_idx = 5  # start with magenta as companion

        def recompute():
            eff=hsl[:]
            if link_brights:
                eff = hsl[:8]+[[h,s,clamp(l+0.12,0,1)] for h,s,l in hsl[:8]]
            pal_hex=[hsl_to_hex(tuple(v)) for v in eff[:16]]
            apply_palette(pal_hex); return pal_hex

        pal_hex=recompute(); show(pal_hex,hsl,idx,chan,link_brights,comp_idx)

        def adjust(amount_big=False, sign=+1):
            step_small = [1/360, 0.01, 0.02]
            step_big   = [5/360, 0.05, 0.08]
            step = step_big[chan] if amount_big else step_small[chan]
            h,s,l = hsl[idx]
            if chan==0: h=(h + sign*step) % 1.0
            elif chan==1: s=clamp(s + sign*step, 0.0, 1.0)
            else: l=clamp(l + sign*step, 0.0, 1.0)
            hsl[idx] = [h,s,l]

        while True:
            k=read_key()
            if not k: continue

            if k in ('q','Q'): break
            elif k in ('s','S'): save_palette(PALETTE_FILE, pal_hex)
            elif k in ('r','R'): hsl=[list(hex_to_hsl(hx)) for hx in CATPPUCCIN_MOCHA_ANSI]
            elif k == ' ': link_brights = not link_brights
            elif k in (',','<'): idx=(idx-1)%16
            elif k in ('.','>'): idx=(idx+1)%16
            elif k in ('{',): comp_idx=(comp_idx-1)%16
            elif k in ('}',): comp_idx=(comp_idx+1)%16
            elif k in '0123456789abcdefABCDEF': idx=int(k,16)
            elif k in ('LT','h','H'): chan=(chan-1)%3
            elif k in ('RT','l','L'): chan=(chan+1)%3
            elif k in ('UP','k','K','PGUP'): adjust(amount_big=(k in ('K','PGUP')), sign=+1)
            elif k in ('DN','j','J','PGDN'): adjust(amount_big=(k in ('J','PGDN')), sign=-1)

            pal_hex=recompute(); show(pal_hex,hsl,idx,chan,link_brights,comp_idx)

    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old); print(RST,end="")

if __name__=="__main__":
    import colorsys
    main()
