#!/usr/bin/env python3
# ansi_tuner_raw.py — arrow-compat + fallback keys + clearer hints
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

FG = {
    "comment": sgr(90), "keyword": sgr(34), "string":  sgr(32),
    "number":  sgr(36), "ident":   sgr(37), "punct":   sgr(37),
    "warning": sgr(33), "error":   sgr(31),
}
STYLE = {"bold": sgr(1), "dim": sgr(2), "italic": sgr(3), "underline": sgr(4)}

def colorize_demo():
    out=[]
    # Python
    out += [FG["comment"]+"# Python"+RST+"\n"]
    out += [FG["keyword"]+"def"+RST+" "+FG["ident"]+"fib"+RST+FG["punct"]+"("+RST+FG["ident"]+"n"+RST+FG["punct"]+": "+RST+FG["keyword"]+"int"+RST+FG["punct"]+") -> "+RST+FG["keyword"]+"int"+RST+":\n"]
    out += ["    "+FG["comment"]+"# comment: naive recursion"+RST+"\n"]
    out += ["    "+FG["keyword"]+"return"+RST+" "+FG["number"]+"1"+RST+" "+FG["keyword"]+"if"+RST+" "+FG["ident"]+"n"+RST+" < "+FG["number"]+"2"+RST+" "+FG["keyword"]+"else"+RST+" "+
            FG["ident"]+"fib"+RST+FG["punct"]+"("+RST+FG["ident"]+"n"+RST+"-"+FG["number"]+"1"+RST+FG["punct"]+")"+RST+" + "+
            FG["ident"]+"fib"+RST+FG["punct"]+"("+RST+FG["ident"]+"n"+RST+"-"+FG["number"]+"2"+RST+FG["punct"]+")"+RST+"\n\n"]
    # Shell
    out += [FG["comment"]+"# Shell"+RST+"\n"]
    out += [FG["comment"]+"# "+RST+FG["ident"]+"$"+RST+" "+FG["ident"]+"git"+RST+" "+FG["ident"]+"status"+RST+" && "+FG["ident"]+"echo"+RST+" "+FG["string"]+"\"ok\""+RST+"\n\n"]
    # JSON
    out += [FG["comment"]+"# JSON"+RST+"\n"]
    out += [FG["punct"]+"{ "+RST+FG["string"]+"\"name\""+RST+FG["punct"]+": "+RST+FG["string"]+"\"catppuccin\""+RST+FG["punct"]+", "+RST+
            FG["string"]+"\"flavor\""+RST+FG["punct"]+": "+RST+FG["string"]+"\"mocha\""+RST+FG["punct"]+", "+RST+
            FG["string"]+"\"ok\""+RST+FG["punct"]+": "+RST+FG["keyword"]+"true"+RST+" "+FG["punct"]+"}"+RST+"\n\n"]
    # C
    out += ["/* C */\n"]
    out += [FG["keyword"]+"#include"+RST+" "+FG["punct"]+"<"+RST+FG["ident"]+"stdio.h"+RST+FG["punct"]+">"+RST+"\n"]
    out += [FG["keyword"]+"int"+RST+" "+FG["ident"]+"main"+RST+FG["punct"]+"("+RST+FG["keyword"]+"void"+RST+FG["punct"]+")"+RST+" {\n"]
    out += ["    "+FG["ident"]+"printf"+RST+FG["punct"]+"("+RST+FG["string"]+"\"Hello, \""+RST+" "+
            STYLE["italic"]+FG["ident"]+"italic"+RST+" "+STYLE["bold"]+FG["ident"]+"bold"+RST+" "+
            STYLE["underline"]+FG["ident"]+"underline"+RST+FG["punct"]+"\\n\""+RST+FG["punct"]+");"+RST+"\n"]
    out += ["}\n"]
    return "".join(out)

def clear(): sys.stdout.write("\033[H\033[2J"); sys.stdout.flush()

def show(pal_hex,hsl,idx,chan,link_brights):
    h,s,l = hsl[idx]
    clear()
    print(f"idx={idx:02d} #{pal_hex[idx]} HSL={int(h*360)}° {int(s*100)}% {int(l*100)}% link_brights={'ON' if link_brights else 'OFF'}")
    chan_lbl = " ".join(f"[{c}]" if i==chan else c for i,c in enumerate("HSL"))
    print("Channels:", chan_lbl)
    print("(h/l = prev/next channel, j/k = small -, + ; J/K = big -, + ; ,/. = prev/next color)")
    print()
    # Swatches
    wide = "█████"
    for row in (range(0,8),range(8,16)):
        print(" ".join(f"{sgr(bg_code(i))}{wide}{RST}{sgr(fg_code(i))}{wide}{RST}" for i in row))
    print()
    # Attributes (spaced)
    def row_for(name, code):
        blocks = " ".join(f"{sgr(code)}{sgr(fg_code(i))}{wide}{RST}" for i in range(16))
        print(f"{name:<10}{blocks}\n")
    row_for("Normal",""); row_for("Bold","1"); row_for("Dim","2"); row_for("Italic","3"); row_for("Underline","4")
    print(colorize_demo())

def read_key():
    # returns: 'UP','DN','LT','RT','PGUP','PGDN' or single chars
    dr,_,_ = select.select([sys.stdin],[],[],0.2)
    if not dr: return None
    ch=sys.stdin.read(1)
    if ch!='\x1b': return ch
    # Possible CSI or SS3
    # CSI: ESC [ A/B/C/D/5~/6~
    # SS3: ESC O A/B/C/D
    if select.select([sys.stdin],[],[],0.01)[0]:
        ch2=sys.stdin.read(1)
        if ch2=='[':  # CSI
            ch3=sys.stdin.read(1)
            if   ch3=='A': return 'UP'
            elif ch3=='B': return 'DN'
            elif ch3=='C': return 'RT'
            elif ch3=='D': return 'LT'
            elif ch3=='5' and sys.stdin.read(1)=='~': return 'PGUP'
            elif ch3=='6' and sys.stdin.read(1)=='~': return 'PGDN'
        elif ch2=='O':  # SS3
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

        def recompute():
            eff=hsl[:]
            if link_brights:
                eff = hsl[:8]+[[h,s,clamp(l+0.12,0,1)] for h,s,l in hsl[:8]]
            pal_hex=[hsl_to_hex(tuple(v)) for v in eff[:16]]
            apply_palette(pal_hex); return pal_hex

        pal_hex=recompute(); show(pal_hex,hsl,idx,chan,link_brights)

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
            elif k in '0123456789abcdefABCDEF': idx=int(k,16)
            elif k in ('LT','h','H'): chan=(chan-1)%3
            elif k in ('RT','l','L'): chan=(chan+1)%3
            elif k in ('UP','k','K','PGUP'): adjust(amount_big=(k in ('K','PGUP')), sign=+1)
            elif k in ('DN','j','J','PGDN'): adjust(amount_big=(k in ('J','PGDN')), sign=-1)

            pal_hex=recompute(); show(pal_hex,hsl,idx,chan,link_brights)

    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old); print(RST,end="")

if __name__=="__main__":
    import colorsys
    main()
