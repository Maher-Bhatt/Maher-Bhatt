"""Generates the animated SVG assets for the GitHub profile README.

Run:  python tools/build_assets.py

Every SVG is self-contained (no JS, no web fonts) so GitHub's image proxy renders
it. Motion is CSS + SMIL only. Under prefers-reduced-motion every element shows
its resting state, which is the finished frame.
"""
import math
import random
import re
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "assets"
OUT.mkdir(exist_ok=True)

SANS = "'Inter','SF Pro Display',-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
MONO = "'JetBrains Mono','SF Mono',ui-monospace,Menlo,Consolas,monospace"

BG = "#09090B"
PANEL = "#111114"
INK = "#EDEDEF"
MUTED = "#8E8E98"
DIM = "#56565F"
LINE = "#1F1F25"
GO = "#6FCF97"

# key, name, descriptor, accent
PROJECTS = [
    ("qavironel", "Qavironel", "STUDIO · FOUNDER", "#EE5216"),
    ("kalki", "K.A.L.K.I.", "AI ASSISTANT", "#E9B949"),
    ("codedroid", "CodeDroid", "ANDROID IDE", "#7FC8A0"),
    ("civic", "Civic Sathi", "CIVIC PLATFORM", "#5BB8C4"),
    ("portfolio", "maherbhatt.me", "CINEMATIC PORTFOLIO", "#A99BF0"),
    ("campus", "CampusLoop", "CAMPUS PLATFORM", "#7AA7F5"),
    ("ztees", "Z Tees", "CLIENT · STREETWEAR", "#E88A8A"),
    ("cip", "Classic Infra", "CLIENT · INFRASTRUCTURE", "#D2B48C"),
]
ACC = {k: c for k, _, _, c in PROJECTS}

REDUCED = "@media (prefers-reduced-motion: reduce){*{animation:none!important}}"
EASE = "cubic-bezier(.65,0,.35,1)"
OUTE = "cubic-bezier(.16,1,.3,1)"

# The Qavironel Q, from the studio's own icon (viewBox 0 0 128 128).
Q_LOOP = "M78 14 H50 L19 45 V75 L47 103 H75 L92 86 V55 L81 34"
Q_EXIT = "M69 71 L108 110"


def svg(w, h, label, body, css=""):
    body = re.sub(r"&(?![a-zA-Z]+;|#)", "&amp;", body)
    label = label.replace("&", "&amp;")
    return f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{label}">
<style>
text{{font-family:{SANS}}}
.mono{{font-family:{MONO}}}
.draw{{stroke-dasharray:1;animation:draw 1.8s {EASE} backwards}}
@keyframes draw{{from{{stroke-dashoffset:1}}}}
.fade{{animation:fade 1.1s ease backwards}}
@keyframes fade{{from{{opacity:0}}}}
.rise{{animation:rise 1.2s {OUTE} backwards}}
@keyframes rise{{from{{opacity:0;transform:translateY(14px)}}}}
{css}
{REDUCED}
</style>
{body}
</svg>
"""


def grain(id_="g", op=0.045):
    return (f'<filter id="{id_}"><feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2" stitchTiles="stitch"/>'
            f'<feColorMatrix values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 {op} 0"/></filter>')


def dotgrid(id_="dots", gap=24, op=.07):
    return (f'<pattern id="{id_}" width="{gap}" height="{gap}" patternUnits="userSpaceOnUse">'
            f'<circle cx="{gap / 2}" cy="{gap / 2}" r=".9" fill="#FFFFFF" fill-opacity="{op}"/></pattern>')


def d_of(pts):
    return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)


def offset(pts, d):
    """True parallel offset of a polyline (keeps 45-degree bends parallel)."""
    lines = []
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        dx, dy = x1 - x0, y1 - y0
        L = math.hypot(dx, dy)
        nx, ny = -dy / L, dx / L
        lines.append(((x0 + nx * d, y0 + ny * d), (dx / L, dy / L)))
    out = [lines[0][0]]
    for (a, u), (b, v) in zip(lines, lines[1:]):
        den = u[0] * v[1] - u[1] * v[0]
        if abs(den) < 1e-9:
            out.append(b)
            continue
        t = ((b[0] - a[0]) * v[1] - (b[1] - a[1]) * v[0]) / den
        out.append((a[0] + t * u[0], a[1] + t * u[1]))
    (x1, y1) = pts[-1]
    (x0, y0) = pts[-2]
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy)
    out.append((x1 - dy / L * d, y1 + dx / L * d))
    return out


def route(x_from, y_from, x_to, y_to, tail=36):
    """Horizontal, one 45-degree run, horizontal: the Qavironel routing motif."""
    sgn = 1 if x_to > x_from else -1
    dy = abs(y_to - y_from)
    x_diag_end = x_to - sgn * tail
    x_turn = x_diag_end - sgn * dy
    return [(x_from, y_from), (x_turn, y_from), (x_diag_end, y_to), (x_to, y_to)]


def chips(items, y, x=32, size=12):
    out, cx = [], x
    cw = size * .6
    for t in items:
        w = len(t) * cw + 22
        out.append(
            f'<rect x="{cx:.1f}" y="{y}" width="{w:.1f}" height="24" rx="12" fill="#FFFFFF" fill-opacity=".03" stroke="#FFFFFF" stroke-opacity=".09"/>'
            f'<text class="mono" x="{cx + w / 2:.1f}" y="{y + 16}" text-anchor="middle" font-size="{size}" fill="{MUTED}">{t}</text>')
        cx += w + 8
    return "".join(out)


def frame(W, H, accent, inner, rx=22, glow_at=("50%", "0%", "75%"), glow_op=.18):
    cx, cy, r = glow_at
    return f"""<defs>
<clipPath id="cc"><rect width="{W}" height="{H}" rx="{rx}"/></clipPath>
<radialGradient id="glow" cx="{cx}" cy="{cy}" r="{r}"><stop offset="0" stop-color="{accent}" stop-opacity="{glow_op}"/><stop offset="1" stop-color="{accent}" stop-opacity="0"/></radialGradient>
<linearGradient id="edge" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{accent}" stop-opacity="0"/><stop offset=".5" stop-color="{accent}" stop-opacity=".85"/><stop offset="1" stop-color="{accent}" stop-opacity="0"/></linearGradient>
{grain()}{dotgrid()}
</defs>
<g clip-path="url(#cc)">
<rect width="{W}" height="{H}" fill="{BG}"/><rect width="{W}" height="{H}" fill="url(#glow)"/>
{inner}
<rect width="{W}" height="{H}" filter="url(#g)"/>
</g>
<rect x="{W * .2}" y="0" width="{W * .6}" height="1" fill="url(#edge)"/>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="{rx - .5}" fill="none" stroke="#FFFFFF" stroke-opacity=".08"/>"""


# ======================================================================= HERO
def hero():
    W, H = 1200, 660
    left, right = PROJECTS[:4], PROJECTS[4:]
    node_y = [112, 220, 392, 490]
    end_y = [250, 294, 338, 382]
    routes, labels, packets = [], [], []
    for side, items in (("L", left), ("R", right)):
        for i, (k, name, desc, c) in enumerate(items):
            ny, ey = node_y[i], end_y[i]
            nx, ex = (60, 292) if side == "L" else (1140, 908)
            pts = route(nx, ny, ex, ey)
            pid = f"r{side}{i}"
            delay = .5 + i * .18 + (0 if side == "L" else .09)
            for off in (-8, 8):
                routes.append(f'<path class="draw" pathLength="1" d="{d_of(offset(pts, off))}" fill="none" stroke="#FFFFFF" stroke-opacity=".09" style="animation-delay:{delay + .15:.2f}s"/>')
            routes.append(f'<path id="{pid}" class="draw" pathLength="1" d="{d_of(pts)}" fill="none" stroke="{c}" stroke-opacity=".85" stroke-width="1.4" style="animation-delay:{delay:.2f}s"/>')
            routes.append(f'<circle class="fade" cx="{ex}" cy="{ey}" r="2.6" fill="{c}" style="animation-delay:{delay + 1.5:.2f}s"/>')
            anchor, lx = ("start", 48) if side == "L" else ("end", 1152)
            labels.append(
                f'<g class="fade" style="animation-delay:{delay + .2:.2f}s">'
                f'<circle cx="{nx}" cy="{ny}" r="10" fill="{BG}" stroke="{c}" stroke-opacity=".4"/><circle cx="{nx}" cy="{ny}" r="3.6" fill="{c}"/>'
                f'<text class="mono" x="{lx}" y="{ny - 36 if ey > ny else ny + 32}" text-anchor="{anchor}" font-size="12" letter-spacing="1.6" fill="{c}">{name.upper()}</text>'
                f'<text class="mono" x="{lx}" y="{ny - 20 if ey > ny else ny + 48}" text-anchor="{anchor}" font-size="9.5" letter-spacing="1.4" fill="{DIM}">{desc}</text></g>')
            b = 3.0 + i * .7 + (0 if side == "L" else .35)
            packets.append(
                f'<circle r="2.6" fill="{c}" opacity="0"><animateMotion dur="4.2s" begin="{b:.2f}s" repeatCount="indefinite" calcMode="spline" keyPoints="0;1;1" keyTimes="0;.55;1" keySplines=".5 0 .5 1;0 0 1 1"><mpath xlink:href="#{pid}"/></animateMotion>'
                f'<animate attributeName="opacity" values="0;1;1;0;0" keyTimes="0;.06;.5;.56;1" dur="4.2s" begin="{b:.2f}s" repeatCount="indefinite"/></circle>')

    pills = [("Open to internships & freelance", True), ("Vadodara, India", False), ("B.Tech CSE · ITM SLS Baroda", False)]
    widths = [len(t) * 6.9 + (44 if dot else 30) for t, dot in pills]
    gap = 10
    x = 600 - (sum(widths) + gap * (len(pills) - 1)) / 2
    pill_el = []
    for (t, dot), w in zip(pills, widths):
        tx = x + (32 if dot else 15)
        pill_el.append(f'<rect x="{x:.1f}" y="404" width="{w:.1f}" height="30" rx="15" fill="#FFFFFF" fill-opacity=".03" stroke="#FFFFFF" stroke-opacity=".1"/>')
        if dot:
            pill_el.append(f'<circle cx="{x + 18:.1f}" cy="419" r="3.5" fill="{GO}"/><circle class="ping" cx="{x + 18:.1f}" cy="419" r="3.5" fill="{GO}"/>')
        pill_el.append(f'<text class="mono" x="{tx:.1f}" y="423.5" font-size="11.5" fill="{INK if dot else MUTED}">{t}</text>')
        x += w + gap

    stats = [("Microsoft Store", "K.A.L.K.I. PUBLISHED"), ("2nd place", "BSIDES BUG BOUNTY"),
             ("SIH 2026", "CIVIC SATHI · NEXT ROUND"), ("27+", "VERIFIED CREDENTIALS")]
    st_el = []
    for i, (v, l) in enumerate(stats):
        cx = 150 + i * 300
        st_el.append(f'<g class="rise" style="animation-delay:{2.4 + i * .12:.2f}s"><text x="{cx}" y="612" text-anchor="middle" font-size="22" font-weight="650" letter-spacing="-.4" fill="{INK}">{v}</text>'
                     f'<text class="mono" x="{cx}" y="634" text-anchor="middle" font-size="9.5" letter-spacing="1.6" fill="{DIM}">{l}</text></g>')
        if i:
            st_el.append(f'<line class="fade" x1="{cx - 150}" y1="592" x2="{cx - 150}" y2="636" stroke="{LINE}" style="animation-delay:2.4s"/>')

    css = f"""
.orb{{opacity:.13;animation:drift 32s ease-in-out infinite alternate}}
@keyframes drift{{0%{{transform:translate(0,0)}}50%{{transform:translate(50px,-30px)}}100%{{transform:translate(-40px,24px)}}}}
.name{{animation:up 1.4s {OUTE} .35s backwards}}
@keyframes up{{from{{transform:translateY(120px)}}}}
.ping{{transform-box:fill-box;transform-origin:center;animation:ping 2s {OUTE} infinite}}
@keyframes ping{{from{{transform:scale(1);opacity:.6}}to{{transform:scale(3.2);opacity:0}}}}
.rule{{stroke-dasharray:1;animation:draw 1.6s {EASE} 2.2s backwards}}
"""
    orbs = "".join(
        f'<circle class="orb" cx="{x}" cy="{y}" r="{r}" fill="{ACC[k]}" style="animation-duration:{t}s;animation-delay:-{t // 3}s"/>'
        for k, x, y, r, t in [("qavironel", 600, 300, 220, 28), ("portfolio", 860, 220, 160, 33), ("campus", 360, 380, 170, 31), ("kalki", 420, 180, 130, 36)]
    )
    body = f"""<defs>
<clipPath id="c"><rect width="{W}" height="{H}" rx="24"/></clipPath>
<clipPath id="nameclip"><rect x="0" y="222" width="{W}" height="128"/></clipPath>
<filter id="blur" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="80"/></filter>
{grain()}{dotgrid(op=.08)}
<radialGradient id="gridmask" cx="50%" cy="45%" r="60%"><stop offset="0" stop-color="#fff" stop-opacity=".9"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>
<mask id="gm"><rect width="{W}" height="{H}" fill="url(#gridmask)"/></mask>
<linearGradient id="ink" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FFFFFF"/><stop offset="1" stop-color="#9E9EA8"/></linearGradient>
<linearGradient id="sheen" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="240" y2="0">
<stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".6"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>
<animateTransform attributeName="gradientTransform" type="translate" values="-300 0;1300 0;1300 0" keyTimes="0;.35;1" dur="7s" begin="1.6s" repeatCount="indefinite"/>
</linearGradient>
<radialGradient id="vig" cx="50%" cy="50%" r="72%"><stop offset=".55" stop-color="{BG}" stop-opacity="0"/><stop offset="1" stop-color="{BG}" stop-opacity=".92"/></radialGradient>
</defs>
<g clip-path="url(#c)">
<rect width="{W}" height="{H}" fill="{BG}"/>
<rect width="{W}" height="{H}" fill="url(#dots)" mask="url(#gm)"/>
<g filter="url(#blur)">{orbs}</g>
<rect width="{W}" height="{H}" fill="url(#vig)"/>
{''.join(routes)}{''.join(packets)}{''.join(labels)}
<text class="mono fade" x="600" y="206" text-anchor="middle" font-size="12.5" letter-spacing="4.5" fill="{MUTED}" style="animation-delay:.2s">FOUNDER <tspan fill="{ACC['qavironel']}">·</tspan> QAVIRONEL TECHNOLOGIES</text>
<g clip-path="url(#nameclip)"><g class="name">
<text x="600" y="322" text-anchor="middle" font-size="104" font-weight="700" letter-spacing="-4" fill="url(#ink)">Maher Bhatt</text>
<text x="600" y="322" text-anchor="middle" font-size="104" font-weight="700" letter-spacing="-4" fill="url(#sheen)">Maher Bhatt</text>
</g></g>
<text class="fade" x="600" y="374" text-anchor="middle" font-size="20" fill="{MUTED}" style="animation-delay:1s">Systems engineer  ·  Applied AI  ·  Full-stack  ·  Security</text>
<g class="fade" style="animation-delay:1.4s">{''.join(pill_el)}</g>
<line class="rule" pathLength="1" x1="48" y1="572" x2="1152" y2="572" stroke="{LINE}"/>
{''.join(st_el)}
<rect width="{W}" height="{H}" filter="url(#g)"/>
</g>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="23.5" fill="none" stroke="#FFFFFF" stroke-opacity=".08"/>"""
    names = ", ".join(n for _, n, _, _ in PROJECTS)
    return svg(W, H, f"Maher Bhatt, founder of Qavironel Technologies. Systems engineer: applied AI, full-stack, security. Projects: {names}.", body, css)


# ================================================================== QAVIRONEL
def qavironel():
    W, H = 1200, 480
    a = ACC["qavironel"]
    services = ["Web Design & Development", "Product & Software Engineering", "Applied AI & Automation",
                "Digital Product Design & Systems", "Technical Optimisation & SEO"]
    s, qx, qy = 1.3, 640, 96
    ex, ey = qx + 108 * s, qy + 110 * s  # tip of the Q's exit stroke
    traces, labels, packets = [], [], []
    for i, t in enumerate(services):
        ty = 128 + i * 62
        pts = [(ex, ey)] + route(ex + 18, ey, 900, ty, tail=40)[1:]
        pts.insert(1, (ex + 18, ey))
        pid = f"s{i}"
        d = 1.9 + i * .14
        traces.append(f'<path id="{pid}" class="draw" pathLength="1" d="{d_of(pts)}" fill="none" stroke="{a if i == 2 else "#FFFFFF"}" stroke-opacity="{.9 if i == 2 else .22}" stroke-width="{1.5 if i == 2 else 1.1}" style="animation-delay:{d:.2f}s"/>')
        labels.append(f'<g class="fade" style="animation-delay:{d + 1:.2f}s"><circle cx="900" cy="{ty}" r="3.4" fill="{a}"/>'
                      f'<text class="mono" x="918" y="{ty - 3}" font-size="10" letter-spacing="1.4" fill="{a}">0{i + 1}</text>'
                      f'<text x="918" y="{ty + 15}" font-size="14" fill="{INK}">{t}</text></g>')
        b = 3.6 + i * .55
        packets.append(f'<circle r="2.4" fill="{a}" opacity="0"><animateMotion dur="3.6s" begin="{b:.2f}s" repeatCount="indefinite" calcMode="spline" keyPoints="0;1;1" keyTimes="0;.6;1" keySplines=".5 0 .5 1;0 0 1 1"><mpath xlink:href="#{pid}"/></animateMotion>'
                       f'<animate attributeName="opacity" values="0;1;1;0;0" keyTimes="0;.05;.56;.62;1" dur="3.6s" begin="{b:.2f}s" repeatCount="indefinite"/></circle>')
    desc = ["An independent design and engineering studio in Vadodara.",
            "We build websites, digital products and practical AI tools",
            "for founders and teams in India, the US and Europe, and",
            "clients work directly with the people who build."]
    desc_el = "".join(f'<text x="56" y="{226 + i * 25}" font-size="16.5" fill="{MUTED}">{l}</text>' for i, l in enumerate(desc))
    inner = f"""<rect width="{W}" height="{H}" fill="url(#dots)" opacity=".6"/>
<text class="mono" x="56" y="72" font-size="12" letter-spacing="2.4" fill="{a}">00  /  THE STUDIO · FOUNDER &amp; SYSTEMS ENGINEER</text>
<text x="56" y="134" font-size="50" font-weight="700" letter-spacing="-1.8" fill="{INK}">Qavironel Technologies</text>
<text x="56" y="178" font-size="25" font-weight="600" letter-spacing="-.6" fill="{INK}">Ideas. <tspan fill="{a}">Engineered.</tspan></text>
{desc_el}
<text class="mono" x="56" y="358" font-size="10" letter-spacing="1.6" fill="{DIM}">TEAM</text>
<text x="56" y="380" font-size="14" fill="{INK}">Maher Bhatt <tspan fill="{MUTED}">· Anurag Pandey · Jaydev Gohil · Dhyani Parikh · Aayushi Jasani</tspan></text>
{chips(["Next.js 16", "React 19", "GSAP", "three.js", "Tailwind v4"], 414, x=56)}
<g transform="translate({qx},{qy}) scale({s})" fill="none" stroke-linecap="round" stroke-linejoin="round" stroke-width="10">
<path d="{Q_LOOP}" stroke="#FFFFFF" stroke-opacity=".06" stroke-width="10"/>
<path class="draw" pathLength="1" d="{Q_LOOP}" stroke="{INK}" style="animation-duration:1.6s;animation-delay:.3s"/>
<path class="draw" pathLength="1" d="{Q_EXIT}" stroke="{a}" style="animation-duration:.6s;animation-delay:1.5s"/>
</g>
{''.join(traces)}{''.join(packets)}{''.join(labels)}"""
    return svg(W, H, "Qavironel Technologies, a design and engineering studio founded by Maher Bhatt. Ideas. Engineered.",
               frame(W, H, a, inner, glow_at=("62%", "40%", "50%"), glow_op=.14))


# ====================================================================== KALKI
def kalki():
    W, H = 1200, 520
    a = ACC["kalki"]
    CY = 15  # seconds per full cycle through the five destinations
    dests = ["Ask", "Today", "Memory", "Workbench", "Security"]
    wx, wy, ww, wh = 610, 56, 540, 410
    sx = wx + 16  # sidebar x
    css = [f"""
.hl{{animation:hl {CY}s {EASE} infinite}}
@keyframes hl{{{' '.join(f'{i * 20}%,{i * 20 + 18}%{{transform:translateY({i * 38}px)}}' for i in range(5))} 100%{{transform:translateY(0)}}}}
.p1,.p2,.p3,.p4{{opacity:0}}
.wave{{transform-box:fill-box;transform-origin:center;animation:wave 1s ease-in-out infinite alternate}}
@keyframes wave{{from{{transform:scaleY(.3)}}to{{transform:scaleY(1)}}}}
"""]
    for i in range(5):
        s0, s1 = i * 20, i * 20 + 20
        if i == 0:
            kf = f"0%,18%{{opacity:1}}20%,98%{{opacity:0}}100%{{opacity:1}}"
        else:
            kf = f"0%,{s0 - 1}%{{opacity:0}}{s0 + 1}%,{s1 - 2}%{{opacity:1}}{s1}%,100%{{opacity:0}}"
        css.append(f".p{i}{{animation:p{i} {CY}s linear infinite}}@keyframes p{i}{{{kf}}}")

    side = "".join(
        f'<text x="{sx + 30}" y="{wy + 86 + i * 38}" font-size="13.5" fill="{INK if i == 0 else MUTED}">{t}</text>'
        f'<circle cx="{sx + 16}" cy="{wy + 81 + i * 38}" r="3" fill="{MUTED}" fill-opacity=".6"/>'
        for i, t in enumerate(dests))
    models = ["Groq · LLaMA 3.3", "Ollama · offline", "Gemini", "Claude", "OpenAI"]
    mcss = []
    for i, m in enumerate(models):
        s0, s1 = i * 20, i * 20 + 20
        kf = (f"0%,18%{{opacity:1}}20%,98%{{opacity:0}}100%{{opacity:1}}" if i == 0
              else f"0%,{s0 - 1}%{{opacity:0}}{s0 + 1}%,{s1 - 2}%{{opacity:1}}{s1}%,100%{{opacity:0}}")
        mcss.append(f".m{i}{{animation:m{i} {CY}s linear infinite}}@keyframes m{i}{{{kf}}}" + ("" if i == 0 else f".m{i}{{opacity:0}}"))
    css += mcss
    model_el = "".join(f'<text class="mono m{i}" x="{wx + ww - 84}" y="{wy + 27}" text-anchor="middle" font-size="10.5" fill="{INK}">{m}</text>' for i, m in enumerate(models))

    cx0 = wx + 168  # content x
    cw = wx + ww - 20 - cx0

    def bar(x, y, w, op=.09):
        return f'<rect x="{x}" y="{y}" width="{w}" height="7" rx="3.5" fill="#FFFFFF" fill-opacity="{op}"/>'

    p_ask = f"""<g class="p0">
<rect x="{cx0 + cw - 250}" y="{wy + 66}" width="250" height="34" rx="12" fill="{a}" fill-opacity=".14"/>
<text x="{cx0 + cw - 238}" y="{wy + 88}" font-size="12.5" fill="{INK}">Plan my day around the 3 pm review</text>
<circle cx="{cx0 + 10}" cy="{wy + 128}" r="9" fill="{a}" fill-opacity=".25"/><text class="mono" x="{cx0 + 10}" y="{wy + 132}" text-anchor="middle" font-size="9" fill="{a}">K</text>
{bar(cx0 + 28, wy + 122, 300)}{bar(cx0 + 28, wy + 138, 260)}{bar(cx0 + 28, wy + 154, 220)}
<g transform="translate({cx0 + 28},{wy + 176})">{''.join(f'<rect x="{i * 34}" y="0" width="30" height="42" rx="6" fill="#FFFFFF" fill-opacity=".04" stroke="#FFFFFF" stroke-opacity=".08"/>' for i in range(3))}</g>
<rect x="{cx0}" y="{wy + wh - 70}" width="{cw}" height="40" rx="12" fill="#FFFFFF" fill-opacity=".03" stroke="#FFFFFF" stroke-opacity=".1"/>
<text x="{cx0 + 16}" y="{wy + wh - 45}" font-size="12.5" fill="{DIM}">Ask KALKI anything…</text>
<g transform="translate({cx0 + cw - 66},{wy + wh - 58})">{''.join(f'<rect class="wave" x="{i * 6}" y="{8 - h / 2}" width="2.5" height="{h}" rx="1.2" fill="{a}" style="animation-delay:-{i * .12:.2f}s"/>' for i, h in enumerate([6, 12, 18, 10, 16, 8, 12]))}</g>
</g>"""
    agenda = [("09:30", "Deep work: thesis draft", False), ("13:00", "Lunch", False), ("15:00", "Design review", True), ("17:30", "Gym", False)]
    p_today = f"""<g class="p1"><text x="{cx0}" y="{wy + 84}" font-size="15" font-weight="600" fill="{INK}">Today</text>
{''.join(f'<rect x="{cx0}" y="{wy + 100 + i * 48}" width="{cw}" height="40" rx="10" fill="{a if hi else "#FFFFFF"}" fill-opacity="{.12 if hi else .03}" stroke="{a if hi else "#FFFFFF"}" stroke-opacity="{.5 if hi else .08}"/><text class="mono" x="{cx0 + 14}" y="{wy + 125 + i * 48}" font-size="11" fill="{a if hi else MUTED}">{t}</text><text x="{cx0 + 74}" y="{wy + 125 + i * 48}" font-size="13" fill="{INK}">{n}</text>' for i, (t, n, hi) in enumerate(agenda))}
<text class="mono" x="{cx0}" y="{wy + 316}" font-size="10" letter-spacing="1.2" fill="{DIM}">FOCUS SESSION · 50 MIN</text>
<rect x="{cx0}" y="{wy + 326}" width="{cw}" height="5" rx="2.5" fill="#FFFFFF" fill-opacity=".07"/><rect x="{cx0}" y="{wy + 326}" width="{cw * .62:.0f}" height="5" rx="2.5" fill="{a}"/></g>"""
    mems = ["Prefers concise answers", "Exam: DBMS on Dec 12", "Uses VS Code + PowerShell", "Studio: Qavironel"]
    p_mem = f"""<g class="p2"><text x="{cx0}" y="{wy + 84}" font-size="15" font-weight="600" fill="{INK}">Memory</text>
{''.join(f'<rect x="{cx0 + (i % 2) * (cw / 2 + 5):.0f}" y="{wy + 100 + (i // 2) * 74}" width="{cw / 2 - 5:.0f}" height="64" rx="10" fill="#FFFFFF" fill-opacity=".03" stroke="#FFFFFF" stroke-opacity=".08"/><text x="{cx0 + 12 + (i % 2) * (cw / 2 + 5):.0f}" y="{wy + 126 + (i // 2) * 74}" font-size="12" fill="{INK}">{m}</text>{bar(cx0 + 12 + (i % 2) * (cw / 2 + 5), wy + 140 + (i // 2) * 74, 90, .07)}' for i, m in enumerate(mems))}
<rect x="{cx0}" y="{wy + 262}" width="{cw}" height="38" rx="10" fill="{a}" fill-opacity=".08" stroke="{a}" stroke-opacity=".3"/>
<path d="M{cx0 + 16},{wy + 279} h10 v9 h-10 z M{cx0 + 18},{wy + 279} v-3 a3,3 0 0 1 6,0 v3" fill="none" stroke="{a}" stroke-width="1.4"/>
<text class="mono" x="{cx0 + 36}" y="{wy + 286}" font-size="10.5" fill="{a}">Encrypted on this PC with Windows DPAPI</text></g>"""
    p_work = f"""<g class="p3"><text x="{cx0}" y="{wy + 84}" font-size="15" font-weight="600" fill="{INK}">Workbench</text>
<rect x="{cx0}" y="{wy + 100}" width="{cw}" height="92" rx="10" fill="#000" fill-opacity=".35" stroke="#FFFFFF" stroke-opacity=".08"/>
<text class="mono" x="{cx0 + 14}" y="{wy + 126}" font-size="11" fill="{MUTED}">$ <tspan fill="{INK}">winget upgrade --all</tspan></text>
<text class="mono" x="{cx0 + 14}" y="{wy + 148}" font-size="11" fill="{DIM}">12 packages can be upgraded</text>
<text class="mono" x="{cx0 + 14}" y="{wy + 170}" font-size="11" fill="{DIM}">waiting for approval…</text>
<rect x="{cx0}" y="{wy + 210}" width="{cw}" height="104" rx="12" fill="{PANEL}" stroke="{a}" stroke-opacity=".55"/>
<text class="mono" x="{cx0 + 16}" y="{wy + 236}" font-size="10" letter-spacing="1.4" fill="{a}">APPROVAL NEEDED</text>
<text x="{cx0 + 16}" y="{wy + 258}" font-size="13" fill="{INK}">Run a command that changes installed apps?</text>
<rect x="{cx0 + cw - 196}" y="{wy + 274}" width="84" height="28" rx="8" fill="#FFFFFF" fill-opacity=".05" stroke="#FFFFFF" stroke-opacity=".12"/><text x="{cx0 + cw - 154}" y="{wy + 292}" text-anchor="middle" font-size="12" fill="{MUTED}">Deny</text>
<rect x="{cx0 + cw - 102}" y="{wy + 274}" width="86" height="28" rx="8" fill="{a}"/><text x="{cx0 + cw - 59}" y="{wy + 292}" text-anchor="middle" font-size="12" font-weight="600" fill="{BG}">Approve</text></g>"""
    scans = [("Webscan · headers & TLS", .86), ("CVE intel · 3 matches", .64), ("Shodan OSINT · exposure", .48)]
    css.append(f"@keyframes fill{{0%,80%{{transform:scaleX(0)}}88%,99%{{transform:scaleX(1)}}100%{{transform:scaleX(0)}}}}.fill{{transform-box:fill-box;transform-origin:left;animation:fill {CY}s {EASE} infinite}}")
    p_sec = f"""<g class="p4"><text x="{cx0}" y="{wy + 84}" font-size="15" font-weight="600" fill="{INK}">Security</text>
{''.join(f'<text x="{cx0}" y="{wy + 122 + i * 56}" font-size="12.5" fill="{INK}">{t}</text><rect x="{cx0}" y="{wy + 132 + i * 56}" width="{cw}" height="6" rx="3" fill="#FFFFFF" fill-opacity=".07"/><rect class="fill" x="{cx0}" y="{wy + 132 + i * 56}" width="{cw * v:.0f}" height="6" rx="3" fill="{a}" style="animation-delay:{i * .25:.2f}s"/>' for i, (t, v) in enumerate(scans))}
<text class="mono" x="{cx0}" y="{wy + 312}" font-size="10" letter-spacing="1.2" fill="{DIM}">ONLY ON SYSTEMS YOU OWN OR ARE AUTHORISED TO TEST</text></g>"""

    window = f"""<rect x="{wx}" y="{wy}" width="{ww}" height="{wh}" rx="16" fill="{PANEL}" stroke="#FFFFFF" stroke-opacity=".1"/>
<line x1="{wx}" y1="{wy + 44}" x2="{wx + ww}" y2="{wy + 44}" stroke="#FFFFFF" stroke-opacity=".07"/>
<circle cx="{wx + 20}" cy="{wy + 22}" r="5" fill="#FFFFFF" fill-opacity=".12"/><circle cx="{wx + 38}" cy="{wy + 22}" r="5" fill="#FFFFFF" fill-opacity=".12"/><circle cx="{wx + 56}" cy="{wy + 22}" r="5" fill="#FFFFFF" fill-opacity=".12"/>
<text class="mono" x="{wx + 84}" y="{wy + 27}" font-size="11" letter-spacing="2" fill="{MUTED}">KALKI</text>
<rect x="{wx + ww - 160}" y="{wy + 11}" width="152" height="23" rx="11.5" fill="#FFFFFF" fill-opacity=".04" stroke="{a}" stroke-opacity=".4"/>
<circle cx="{wx + ww - 148}" cy="{wy + 22.5}" r="3" fill="{GO}"/>{model_el}
<line x1="{wx + 152}" y1="{wy + 44}" x2="{wx + 152}" y2="{wy + wh}" stroke="#FFFFFF" stroke-opacity=".07"/>
<rect class="hl" x="{sx}" y="{wy + 66}" width="122" height="30" rx="8" fill="{a}" fill-opacity=".12" stroke="{a}" stroke-opacity=".35"/>
{side}
<rect x="{sx}" y="{wy + wh - 46}" width="122" height="28" rx="8" fill="#FFFFFF" fill-opacity=".03" stroke="#FFFFFF" stroke-opacity=".08"/>
<text class="mono" x="{sx + 61}" y="{wy + wh - 28}" text-anchor="middle" font-size="10.5" fill="{MUTED}">Ctrl K  ·  palette</text>
{p_ask}{p_today}{p_mem}{p_work}{p_sec}"""
    desc = ["A personal AI assistant that lives on your Windows PC.", "Ask, plan your day, remember and automate, with the model",
            "you choose: Groq, Gemini, OpenAI, Claude or fully offline", "Ollama. Memories and keys are DPAPI-encrypted on the PC,",
            "and every consequential action waits for your approval."]
    desc_el = "".join(f'<text x="56" y="{196 + i * 25}" font-size="16.5" fill="{MUTED}">{l}</text>' for i, l in enumerate(desc))
    feats = ["5 destinations", "Voice + PWA HUD", "Telegram control", "Approval queue"]
    inner = f"""<text class="mono" x="56" y="76" font-size="12" letter-spacing="2.4" fill="{a}">01  /  FLAGSHIP · MICROSOFT STORE · OPEN SOURCE</text>
<text x="56" y="146" font-size="58" font-weight="700" letter-spacing="-2" fill="{INK}">K.A.L.K.I.</text>
{desc_el}
{chips(feats, 348, x=56, size=11.5)}
{chips(["Python", "Groq", "Ollama", "DPAPI", "WinUI"], 420, x=56)}
<text class="mono" x="56" y="476" font-size="10" letter-spacing="1.4" fill="{DIM}">2025 – 2026  ·  v1.5.0 ON GITHUB RELEASES</text>
{window}"""
    return svg(W, H, "K.A.L.K.I.: personal AI assistant for Windows with Ask, Today, Memory, Workbench and Security, any model or fully offline, DPAPI-encrypted memory and an approval queue.",
               frame(W, H, a, inner, glow_at=("75%", "45%", "55%"), glow_op=.14), "\n".join(css))


# ====================================================================== CARDS
def card(num, key, kicker, meta, title, desc, stack, illus, css="", W=600, H=440, ih=214, label=None):
    a = ACC[key]
    desc_el = "".join(f'<text x="32" y="{ih + 96 + i * 23}" font-size="15.5" fill="{MUTED}">{line}</text>' for i, line in enumerate(desc))
    live = meta.endswith("LIVE") or "ACTIVE" in meta or "IN USE" in meta
    dot = f'<circle cx="{W - 32}" cy="{ih + 32}" r="3.2" fill="{GO if live else DIM}"/>'
    inner = f"""<clipPath id="ic"><rect width="{W}" height="{ih}"/></clipPath>
<rect width="{W}" height="{ih}" fill="url(#dots)" opacity=".5"/>
<g clip-path="url(#ic)">{illus}</g>
<line x1="0" y1="{ih}" x2="{W}" y2="{ih}" stroke="{LINE}"/>
<text class="mono" x="32" y="{ih + 36}" font-size="11" letter-spacing="2" fill="{a}">{num}  /  {kicker}</text>
{dot}<text class="mono" x="{W - 44}" y="{ih + 36}" text-anchor="end" font-size="10" letter-spacing="1.4" fill="{DIM}">{meta}</text>
<text x="32" y="{ih + 68}" font-size="27" font-weight="650" letter-spacing="-.6" fill="{INK}">{title}</text>
<text x="{W - 32}" y="{ih + 68}" text-anchor="end" font-size="20" fill="{DIM}">↗</text>
{desc_el}
{chips(stack, H - 54)}"""
    return svg(W, H, label or f"{title}: {' '.join(desc)}", frame(W, H, a, inner, rx=20, glow_op=.2), css)


def codedroid():
    a = ACC["codedroid"]
    kw, st, fn = a, "#E8C98A", "#9DB8F5"
    lines = [
        [("def ", kw), ("greet", fn), ("(name):", INK)],
        [("    msg = ", INK), ('f"Hi, {name}"', st)],
        [("    ", INK), ("return ", kw), ("msg", INK)],
        [("", INK)],
        [("print", fn), ("(greet(", INK), ('"Droid"', st), ("))", INK)],
    ]
    css, rows = [], []
    cyc = 9
    for i, segs in enumerate(lines):
        y = 104 + i * 19
        spans = "".join(f'<tspan fill="{c}">{t}</tspan>' for t, c in segs)
        rows.append(f'<text class="mono" x="236" y="{y}" font-size="11.5" xml:space="preserve">{spans}</text>')
        rows.append(f'<text class="mono" x="220" y="{y}" font-size="11.5" fill="{DIM}" text-anchor="end">{i + 1}</text>')
        p0 = 4 + i * 8
        css.append(f"@keyframes t{i}{{0%,{p0}%{{transform:translateX(0)}}{p0 + 6}%,90%{{transform:translateX(220px)}}97%,100%{{transform:translateX(0)}}}}")
        rows.append(f'<rect x="232" y="{y - 13}" width="220" height="18" fill="{PANEL}" style="animation:t{i} {cyc}s steps(18,end) infinite"/>')
    css.append(f"@keyframes out{{0%,52%{{opacity:0}}58%,90%{{opacity:1}}96%,100%{{opacity:0}}}}.out{{animation:out {cyc}s infinite}}")
    css.append("@keyframes blink{50%{opacity:0}}.cur{animation:blink 1s steps(1) infinite}")
    keys = ["TAB", "{", "}", "(", ")", ":", "=", "\""]
    keyrow = "".join(f'<rect x="{206 + i * 23.5:.1f}" y="168" width="20" height="16" rx="3" fill="#FFFFFF" fill-opacity=".05"/><text class="mono" x="{216 + i * 23.5:.1f}" y="180" text-anchor="middle" font-size="8.5" fill="{MUTED}">{k}</text>' for i, k in enumerate(keys))
    illus = f"""
<rect x="190" y="22" width="220" height="270" rx="28" fill="{PANEL}" stroke="#FFFFFF" stroke-opacity=".12"/>
<rect x="270" y="32" width="60" height="6" rx="3" fill="#FFFFFF" fill-opacity=".08"/>
<rect x="204" y="50" width="62" height="20" rx="6" fill="{a}" fill-opacity=".14"/><text class="mono" x="235" y="64" text-anchor="middle" font-size="10" fill="{a}">main.py</text>
<text class="mono" x="296" y="64" text-anchor="middle" font-size="10" fill="{DIM}">app.js</text>
<text class="mono" x="396" y="64" text-anchor="end" font-size="10" fill="{a}">▶ Run</text>
<defs><clipPath id="code"><rect x="200" y="84" width="200" height="80"/></clipPath></defs><g clip-path="url(#code)">{''.join(rows)}</g>
{keyrow}
<g class="out"><rect x="204" y="190" width="192" height="22" rx="6" fill="#000" fill-opacity=".4"/>
<text class="mono" x="212" y="205" font-size="10.5" fill="{a}">$ <tspan fill="{INK}">Hi, Droid</tspan><tspan class="cur">▍</tspan></text></g>
<g class="mono" font-size="10" letter-spacing="1">
<text x="112" y="70" text-anchor="middle" fill="{a}">OFFLINE</text>
<text x="112" y="98" text-anchor="middle" fill="{INK}">Python</text><text x="112" y="116" text-anchor="middle" fill="{INK}">JavaScript</text>
<text x="488" y="70" text-anchor="middle" fill="{DIM}">CLOUD</text>
<text x="488" y="98" text-anchor="middle" fill="{MUTED}">Kotlin · Go</text><text x="488" y="116" text-anchor="middle" fill="{MUTED}">Rust · C++</text><text x="488" y="134" text-anchor="middle" fill="{MUTED}">+10 more</text></g>"""
    return card("02", "codedroid", "ANDROID IDE", "OPEN SOURCE · ACTIVE", "CodeDroid",
                ["A pocket IDE built natively for Android: multi-tab editor,", "on-device Python (Chaquopy) and JavaScript (Rhino), cloud",
                 "compilation for 14+ more, Vim keys, terminal, live preview."],
                ["Kotlin", "Jetpack Compose", "Chaquopy", "Rhino"], illus, "\n".join(css))


def civic():
    a = ACC["civic"]
    random.seed(7)
    centers = [(160, 106, "ROADS", 82), (300, 78, "WATER", 64), (440, 114, "WASTE", 71)]
    dots, css = [], []
    cyc = 8
    n = 0
    for cx, cy, _, _ in centers:
        for _ in range(11):
            sx, sy = random.uniform(50, 550), random.uniform(28, 196)
            tx, ty = cx + random.gauss(0, 13), cy + random.gauss(0, 11)
            dx, dy = sx - tx, sy - ty
            css.append(f"@keyframes d{n}{{0%,18%{{transform:translate({dx:.0f}px,{dy:.0f}px);fill:{DIM}}}45%,80%{{transform:translate(0,0);fill:{a}}}100%{{transform:translate({dx:.0f}px,{dy:.0f}px);fill:{DIM}}}}}")
            dots.append(f'<circle cx="{tx:.1f}" cy="{ty:.1f}" r="3.2" fill="{a}" style="animation:d{n} {cyc}s {EASE} infinite"/>')
            n += 1
    for _ in range(7):
        dots.append(f'<circle cx="{random.uniform(70, 530):.1f}" cy="{random.uniform(160, 198):.1f}" r="2.6" fill="{DIM}" fill-opacity=".7"/>')
    hulls = "".join(
        f'<circle class="hull" cx="{cx}" cy="{cy}" r="36" fill="{a}" fill-opacity=".05" stroke="{a}" stroke-opacity=".45" stroke-dasharray="3 4"/>'
        f'<g class="hull"><text class="mono" x="{cx}" y="{cy + 54}" text-anchor="middle" font-size="10" letter-spacing="1.5" fill="{a}">{lbl}</text>'
        f'<text class="mono" x="{cx}" y="{cy + 68}" text-anchor="middle" font-size="9" fill="{MUTED}">risk {risk}</text></g>'
        for cx, cy, lbl, risk in centers)
    css.append(f"@keyframes hull{{0%,38%{{opacity:0}}50%,80%{{opacity:1}}92%,100%{{opacity:0}}}}.hull{{animation:hull {cyc}s infinite}}")
    langs = "EN · HI · GU · MR · KN"
    illus = f"""{hulls}{''.join(dots)}
<text class="mono" x="568" y="36" text-anchor="end" font-size="10" fill="{DIM}">HDBSCAN · triage → route</text>
<text class="mono" x="32" y="36" font-size="10" letter-spacing="1.2" fill="{DIM}">{langs}</text>"""
    return card("03", "civic", "CIVIC PLATFORM · SIH 2026", "NEXT ROUND", "Civic Sathi",
                ["Four synchronised portals: citizen, municipal command centre,", "contractor and admin. Nearby reports merge into systemic",
                 "issues with a risk score, on a GIS map. Role: Frontend Lead."],
                ["React 19", "FastAPI", "Neon Postgres", "Leaflet"], illus, "\n".join(css))


def portfolio():
    a = ACC["portfolio"]
    cmds = [("help", "work · writeups · research · lab"), ("ls work", "kalki  codedroid  campus-loop  ztees"), ("sudo hire-maher", "Access granted. Opening inbox…")]
    css, rows = [f"@keyframes blink{{50%{{opacity:0}}}}.cur{{animation:blink 1s steps(1) infinite}}"], []
    cyc = 10
    for i, (c, out) in enumerate(cmds):
        y = 80 + i * 40
        p0 = 4 + i * 22
        rows.append(f'<text class="mono" x="66" y="{y}" font-size="11" fill="{a}">~ $ <tspan fill="{INK}">{c}</tspan></text>')
        css.append(f"@keyframes c{i}{{0%,{p0}%{{transform:translateX(0)}}{p0 + 8}%,92%{{transform:translateX(240px)}}98%,100%{{transform:translateX(0)}}}}")
        rows.append(f'<rect x="96" y="{y - 12}" width="240" height="16" fill="{PANEL}" style="animation:c{i} {cyc}s steps({len(c)},end) infinite"/>')
        css.append(f"@keyframes o{i}{{0%,{p0 + 9}%{{opacity:0}}{p0 + 11}%,92%{{opacity:1}}98%,100%{{opacity:0}}}}.o{i}{{animation:o{i} {cyc}s infinite}}")
        rows.append(f'<text class="mono o{i}" x="66" y="{y + 17}" font-size="10.5" fill="{GO if i == 2 else MUTED}">{out}</text>')
    R = 64
    rings = []
    for i in range(5):
        dur = 14
        rings.append(f'<ellipse cx="470" cy="112" rx="{R}" ry="{R * .34:.1f}" fill="none" stroke="{a}" stroke-opacity="{.75 - i * .1:.2f}" transform="rotate({i * 36} 470 112)">'
                     f'<animate attributeName="ry" values="{R * .34:.1f};{R:.1f};{R * .34:.1f}" dur="{dur}s" begin="-{i * dur / 5:.2f}s" repeatCount="indefinite" calcMode="spline" keyTimes="0;.5;1" keySplines=".37 0 .63 1;.37 0 .63 1"/></ellipse>')
    illus = f"""<rect x="48" y="36" width="320" height="160" rx="12" fill="{PANEL}" stroke="#FFFFFF" stroke-opacity=".1"/>
<circle cx="64" cy="52" r="4" fill="#FFFFFF" fill-opacity=".12"/><circle cx="78" cy="52" r="4" fill="#FFFFFF" fill-opacity=".12"/><circle cx="92" cy="52" r="4" fill="#FFFFFF" fill-opacity=".12"/>
<text class="mono" x="352" y="56" text-anchor="end" font-size="9.5" letter-spacing="1.2" fill="{DIM}">PRESS ` FOR TERMINAL</text>
<defs><clipPath id="term"><rect x="52" y="62" width="312" height="130"/></clipPath></defs><g clip-path="url(#term)">{''.join(rows)}</g>
<g transform="rotate(-18 470 112)">{''.join(rings)}</g>
<circle cx="470" cy="112" r="5" fill="{a}"/>
<text class="mono" x="470" y="200" text-anchor="middle" font-size="9.5" letter-spacing="1.2" fill="{DIM}">R3F · CUSTOM GLSL</text>"""
    return card("04", "portfolio", "CINEMATIC PORTFOLIO", "LIVE", "maherbhatt.me",
                ["A cinematic personal site: a 3D sculpture with custom shaders,", "a working terminal, generative Web Audio, CTF writeups,",
                 "and its own Payload CMS with scheduled publishing."],
                ["Next.js 16", "React Three Fiber", "GSAP", "Payload CMS"], illus, "\n".join(css))


def campus():
    a = ACC["campus"]
    posts = [("Unit 3 notes · DBMS", .9), ("Practical 14 solved", .7), ("Hackathon this Friday", .8), ("DSA mock · 30 MCQs", .6)]

    def post(y, t, w):
        return (f'<rect x="86" y="{y}" width="260" height="46" rx="10" fill="{PANEL}" stroke="#FFFFFF" stroke-opacity=".08"/>'
                f'<circle cx="108" cy="{y + 23}" r="9" fill="{a}" fill-opacity=".3"/>'
                f'<text x="126" y="{y + 21}" font-size="12" fill="{INK}">{t}</text>'
                f'<rect x="126" y="{y + 29}" width="{180 * w:.0f}" height="5" rx="2.5" fill="#FFFFFF" fill-opacity=".08"/>')
    feed = "".join(post(i * 56, t, w) for i, (t, w) in enumerate(posts + posts))
    circ = 2 * math.pi * 44
    css = f"""
@keyframes feed{{0%,18%{{transform:translateY(0)}}25%,43%{{transform:translateY(-56px)}}50%,68%{{transform:translateY(-112px)}}75%,93%{{transform:translateY(-168px)}}100%{{transform:translateY(-224px)}}}}
.feed{{animation:feed 10s {EASE} infinite}}
.ring{{stroke-dasharray:{circ:.1f};stroke-dashoffset:{circ * .22:.1f};animation:ring 10s {EASE} infinite}}
@keyframes ring{{0%{{stroke-dashoffset:{circ:.1f}}}60%,92%{{stroke-dashoffset:{circ * .22:.1f}}}100%{{stroke-dashoffset:{circ:.1f}}}}}
"""
    days = "".join(f'<rect x="{404 + i * 16}" y="176" width="12" height="12" rx="3" fill="{a}" fill-opacity="{.85 if i < 5 else .12}"/>' for i in range(7))
    illus = f"""<defs><clipPath id="feedclip"><rect x="80" y="26" width="272" height="172"/></clipPath>
<linearGradient id="fadeY" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{BG}"/><stop offset=".18" stop-color="{BG}" stop-opacity="0"/><stop offset=".82" stop-color="{BG}" stop-opacity="0"/><stop offset="1" stop-color="{BG}"/></linearGradient></defs>
<g clip-path="url(#feedclip)"><g transform="translate(0,34)"><g class="feed">{feed}</g></g></g>
<rect x="80" y="26" width="272" height="172" fill="url(#fadeY)"/>
<circle cx="460" cy="96" r="44" fill="none" stroke="#FFFFFF" stroke-opacity=".07" stroke-width="7"/>
<circle class="ring" cx="460" cy="96" r="44" fill="none" stroke="{a}" stroke-width="7" stroke-linecap="round" transform="rotate(-90 460 96)"/>
<text x="460" y="100" text-anchor="middle" font-size="21" font-weight="650" fill="{INK}">3,027</text>
<text class="mono" x="460" y="116" text-anchor="middle" font-size="9" letter-spacing="1.2" fill="{MUTED}">MCQS</text>
<text class="mono" x="460" y="166" text-anchor="middle" font-size="9" letter-spacing="1.2" fill="{DIM}">STUDY STREAK</text>{days}"""
    return card("05", "campus", "CAMPUS PLATFORM", "MULTI-CAMPUS · LIVE", "CampusLoop",
                ["A multi-university academic platform and community: verified", "syllabus notes, 1,180+ runnable lab practicals, a 3,027+",
                 "question bank, timed mocks and gamified study streaks."],
                ["React", "TypeScript", "Supabase", "Capacitor"], illus, css)


def ztees():
    a = ACC["ztees"]
    shirt = "M262,46 L232,56 L196,80 L214,114 L238,104 L238,196 L362,196 L362,104 L386,114 L404,80 L368,56 L338,46 Q300,72 262,46 Z"
    ways = [a, "#1B1B1F", "#EDE6DA", "#7F8F72"]
    stops = " ".join(f"{i * 25}%,{i * 25 + 20}%{{fill:{c}}}" for i, c in enumerate(ways))
    sizes = ["S", "M", "L", "XL", "2XL", "3XL"]
    css = f"""
@keyframes way{{{stops} 100%{{fill:{ways[0]}}}}}
.shirt{{animation:way 10s {EASE} infinite}}
@keyframes sw{{0%,20%{{transform:translateX(0)}}25%,45%{{transform:translateX(22px)}}50%,70%{{transform:translateX(44px)}}75%,95%{{transform:translateX(66px)}}100%{{transform:translateX(0)}}}}
.sel{{animation:sw 10s {EASE} infinite}}
@keyframes sz{{0%,30%{{transform:translateX(0)}}36%,63%{{transform:translateX(30px)}}69%,96%{{transform:translateX(60px)}}100%{{transform:translateX(0)}}}}
.szsel{{animation:sz 7s {EASE} infinite}}
@keyframes ok{{0%,60%{{opacity:0;transform:translateY(6px)}}68%,92%{{opacity:1;transform:translateY(0)}}100%{{opacity:0}}}}
.ok{{animation:ok 5s ease infinite}}
"""
    sw = "".join(f'<circle cx="{63 + i * 22}" cy="92" r="7" fill="{c}" stroke="#FFFFFF" stroke-opacity=".15"/>' for i, c in enumerate(ways))
    sz = "".join(f'<rect x="{48 + i * 30}" y="132" width="26" height="20" rx="5" fill="#FFFFFF" fill-opacity=".04" stroke="#FFFFFF" stroke-opacity=".1"/><text class="mono" x="{61 + i * 30}" y="146" text-anchor="middle" font-size="8.5" fill="{MUTED}">{s}</text>' for i, s in enumerate(sizes[:4]))
    illus = f"""
<path class="shirt" d="{shirt}" fill="{a}" stroke="#FFFFFF" stroke-opacity=".18" stroke-linejoin="round"/>
<path d="M238,104 L238,196 M362,104 L362,196" stroke="#000" stroke-opacity=".15"/>
<text class="mono" x="48" y="70" font-size="9.5" letter-spacing="1.2" fill="{DIM}">COLORWAY</text>
{sw}<circle class="sel" cx="63" cy="92" r="11" fill="none" stroke="{INK}" stroke-opacity=".8"/>
<text class="mono" x="48" y="124" font-size="9.5" letter-spacing="1.2" fill="{DIM}">SIZE · S–3XL</text>{sz}
<rect class="szsel" x="48" y="132" width="26" height="20" rx="5" fill="none" stroke="{a}"/>
<text class="mono" x="48" y="180" font-size="9.5" letter-spacing="1.2" fill="{DIM}">240 GSM</text>
<g transform="translate(432,76)"><rect width="128" height="30" rx="15" fill="#FFFFFF" fill-opacity=".04" stroke="#FFFFFF" stroke-opacity=".12"/>
<text class="mono" x="64" y="19" text-anchor="middle" font-size="10.5" fill="{INK}">UPI · WhatsApp</text></g>
<g class="ok"><rect x="432" y="120" width="128" height="30" rx="15" fill="{a}" fill-opacity=".14"/><path d="M452,135 l4,4 l7,-8" fill="none" stroke="{a}" stroke-width="1.8" stroke-linecap="round"/>
<text class="mono" x="472" y="139.5" font-size="10.5" fill="{a}">Order placed</text></g>"""
    return card("06", "ztees", "CLIENT · D2C STREETWEAR", "IN PRODUCTION · LIVE", "Z Tees",
                ["A drop-based streetwear store: 61 designs, instant filters,", "two-tap WhatsApp ordering with UPI guidance, and a private",
                 "owner console for stock, orders and media. Built in ~2 days."],
                ["React", "TypeScript", "Supabase", "Framer Motion"], illus, css)


def cip():
    a = ACC["cip"]
    disc = ["PIPELINES", "STORMWATER", "STRUCTURAL", "ROADS", "PIPING"]
    paths, css = [], [f".flow{{stroke-dasharray:3 9;animation:flow 1.6s linear infinite}}@keyframes flow{{to{{stroke-dashoffset:-12}}}}"]
    for i, t in enumerate(disc):
        y = 48 + i * 32
        pts = route(150, y, 430, 112, tail=20)
        d = d_of(pts)
        paths.append(f'<text class="mono" x="138" y="{y + 3.5}" text-anchor="end" font-size="9.5" letter-spacing="1.2" fill="{MUTED}">{t}</text>'
                     f'<circle cx="150" cy="{y}" r="3" fill="{a}"/>'
                     f'<path d="{d}" fill="none" stroke="#FFFFFF" stroke-opacity=".1" stroke-width="5" stroke-linejoin="round"/>'
                     f'<path class="flow" d="{d}" fill="none" stroke="{a}" stroke-width="1.6" stroke-linejoin="round" style="animation-delay:-{i * .3:.1f}s"/>')
    illus = f"""{''.join(paths)}
<rect x="430" y="92" width="134" height="40" rx="10" fill="{PANEL}" stroke="{a}" stroke-opacity=".6"/>
<text class="mono" x="497" y="109" text-anchor="middle" font-size="9.5" letter-spacing="1.2" fill="{a}">TENDER ENQUIRY</text>
<text class="mono" x="497" y="123" text-anchor="middle" font-size="9" fill="{MUTED}">→ directors</text>
<text class="mono" x="564" y="36" text-anchor="end" font-size="9.5" letter-spacing="1.2" fill="{DIM}">EST. 2008 · 51 SITE PHOTOS</text>
<text class="mono" x="564" y="190" text-anchor="end" font-size="9.5" letter-spacing="1.2" fill="{DIM}">VADODARA · AHMEDABAD · SURAT</text>"""
    return card("07", "cip", "CLIENT · CIVIL INFRASTRUCTURE", "IN USE", "Classic Infrastructure",
                ["A corporate platform for a civil contractor: fifteen years", "of field work in real site photography across five",
                 "disciplines, with a structured tender enquiry flow."],
                ["React", "TypeScript", "Vite", "Image pipeline"], illus, "\n".join(css))


# ==================================================================== JOURNEY
def journey():
    W, H = 1200, 330
    ms = [("2025", "B.Tech CSE begins", "ITM SLS BARODA"),
          ("APR 2026", "Python Dev Intern", "QSKILL · LETTER OF REC."),
          ("2026", "K.A.L.K.I. ships", "MICROSOFT STORE"),
          ("2026", "BSides Vadodara", "2ND BUG BOUNTY · 4TH CTF"),
          ("2026", "Founded Qavironel", "DESIGN & ENGINEERING STUDIO"),
          ("NOW", "SIH 2026 · v1.5", "+ MULTI-AGENT LLM RESEARCH")]
    cols = [ACC[k] for k in ("campus", "codedroid", "kalki", "civic", "qavironel", "portfolio")]
    xs = [100 + i * 200 for i in range(6)]
    ys = [180 if i % 2 == 0 else 150 for i in range(6)]
    pts = [(48, ys[0])]
    for i in range(6):
        pts.append((xs[i] - 15, ys[i]))
        pts.append((xs[i] + 15, ys[i]))
        if i < 5:
            dy = abs(ys[i + 1] - ys[i])
            mid = (xs[i] + xs[i + 1]) / 2
            pts.append((mid - dy / 2, ys[i]))
            pts.append((mid + dy / 2, ys[i + 1]))
    pts.append((1152, ys[-1]))
    d = d_of(pts)
    stops = "".join(f'<stop offset="{i / 5:.2f}" stop-color="{c}"/>' for i, c in enumerate(cols))
    nodes = []
    for i, ((date, t, sub), x, y, c) in enumerate(zip(ms, xs, ys, cols)):
        dl = .4 + 2.6 * (x - 48) / 1104
        up = i % 2 == 0
        ty = y - 70 if up else y + 50
        nodes.append(
            f'<g class="pop" style="animation-delay:{dl:.2f}s"><circle cx="{x}" cy="{y}" r="11" fill="{BG}" stroke="{c}" stroke-opacity=".45"/><circle cx="{x}" cy="{y}" r="4.2" fill="{c}"/></g>'
            f'<g class="rise" style="animation-delay:{dl + .15:.2f}s">'
            f'<line x1="{x}" y1="{y - 14 if up else y + 14}" x2="{x}" y2="{ty + 22 if up else ty - 14}" stroke="{c}" stroke-opacity=".35" stroke-dasharray="2 3"/>'
            f'<text class="mono" x="{x}" y="{ty - 22 if up else ty + 4}" text-anchor="middle" font-size="10.5" letter-spacing="1.6" fill="{c}">{date}</text>'
            f'<text x="{x}" y="{ty - 2 if up else ty + 24}" text-anchor="middle" font-size="15" font-weight="600" fill="{INK}">{t}</text>'
            f'<text class="mono" x="{x}" y="{ty + 15 if up else ty + 41}" text-anchor="middle" font-size="9" letter-spacing="1.1" fill="{DIM}">{sub}</text></g>')
    css = f""".pop{{transform-box:fill-box;transform-origin:center;animation:pop .6s {OUTE} backwards}}
@keyframes pop{{from{{opacity:0;transform:scale(.2)}}}}
.trail{{stroke-dasharray:1;animation:draw 3s {EASE} .3s backwards}}"""
    inner = f"""<rect width="{W}" height="{H}" fill="url(#dots)" opacity=".5"/>
<linearGradient id="rg" x1="0" y1="0" x2="1" y2="0">{stops}</linearGradient>
<path d="{d}" fill="none" stroke="#FFFFFF" stroke-opacity=".06" stroke-width="6" stroke-linejoin="round"/>
<path id="trail" class="trail" pathLength="1" d="{d}" fill="none" stroke="url(#rg)" stroke-width="1.6" stroke-linejoin="round"/>
<circle r="3" fill="#FFFFFF" opacity="0"><animateMotion dur="7s" begin="3.4s" repeatCount="indefinite"><mpath xlink:href="#trail"/></animateMotion>
<animate attributeName="opacity" values="0;.9;.9;0" keyTimes="0;.05;.95;1" dur="7s" begin="3.4s" repeatCount="indefinite"/></circle>
{''.join(nodes)}"""
    return svg(W, H, "Journey: 2025 B.Tech CSE; April 2026 Python intern at QSkill; K.A.L.K.I. on the Microsoft Store; BSides Vadodara 2nd bug bounty and 4th CTF; founded Qavironel Technologies; now SIH 2026 and multi-agent LLM research.",
               frame(W, H, ACC["qavironel"], inner, glow_op=.08), css)


def footer():
    W, H = 1200, 150
    dots = "".join(f'<circle cx="{600 - 63 + i * 18}" cy="104" r="3.5" fill="{c}" class="pulse" style="animation-delay:{.12 * i:.2f}s"/>' for i, (_, _, _, c) in enumerate(PROJECTS))
    css = ".pulse{animation:pulse 2.8s ease-in-out infinite}@keyframes pulse{0%,100%{opacity:.3}50%{opacity:1}}"
    body = f"""<g transform="translate(582,18) scale(.28)" fill="none" stroke-linecap="round" stroke-linejoin="round" stroke-width="10">
<path d="{Q_LOOP}" stroke="{MUTED}"/><path d="{Q_EXIT}" stroke="{ACC['qavironel']}"/></g>
<text x="600" y="82" text-anchor="middle" font-size="21" font-weight="600" letter-spacing="-.4" fill="{INK}">Engineering honestly. <tspan fill="{MUTED}">Shipping consistently.</tspan></text>{dots}"""
    return svg(W, H, "Engineering honestly. Shipping consistently.", body, css)


files = {
    "hero.svg": hero(),
    "qavironel.svg": qavironel(),
    "kalki.svg": kalki(),
    "codedroid.svg": codedroid(),
    "civic-sathi.svg": civic(),
    "portfolio.svg": portfolio(),
    "campusloop.svg": campus(),
    "ztees.svg": ztees(),
    "classic-infrastructure.svg": cip(),
    "journey.svg": journey(),
    "footer.svg": footer(),
}
for stale in ("velocity.svg", "statskill.svg"):
    if (OUT / stale).exists():
        (OUT / stale).unlink()
for name, content in files.items():
    (OUT / name).write_text(content, encoding="utf-8")
    print(f"{name:28} {len(content.encode()) / 1024:5.1f} KB")
