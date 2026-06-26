#!/usr/bin/env python3
"""Render the actual periodic table as monochrome house-style HTML.

When an explainer touches chemistry/materials (critical minerals, rare earths,
battery metals, semiconductors...), show the REAL table with the relevant cells
highlighted — not a metaphor. Emits a self-contained <figure> (CSS grid, square
cells, ink-on-white, highlighted cells inverted to white-on-black). Paste the
output into your explainer HTML; it inherits theme.css tokens.

Usage:
    python3 periodic-table.py "Nd,Dy,Pr,Sm,Tb,Eu" "The 17 rare-earth elements" > re.html
    python3 periodic-table.py --list-groups            # show preset symbol sets

Args:
    1: comma-separated element symbols to highlight (or a preset name, see below)
    2: optional caption
Presets: rare-earths, critical-minerals, battery-metals, platinum-group
"""
import sys

# (Z, symbol, group 1-18, period 1-7). f-block placed in rows 8 (La) and 9 (Ac).
E = [
 (1,"H",1,1),(2,"He",18,1),
 (3,"Li",1,2),(4,"Be",2,2),(5,"B",13,2),(6,"C",14,2),(7,"N",15,2),(8,"O",16,2),(9,"F",17,2),(10,"Ne",18,2),
 (11,"Na",1,3),(12,"Mg",2,3),(13,"Al",13,3),(14,"Si",14,3),(15,"P",15,3),(16,"S",16,3),(17,"Cl",17,3),(18,"Ar",18,3),
 (19,"K",1,4),(20,"Ca",2,4),(21,"Sc",3,4),(22,"Ti",4,4),(23,"V",5,4),(24,"Cr",6,4),(25,"Mn",7,4),(26,"Fe",8,4),
 (27,"Co",9,4),(28,"Ni",10,4),(29,"Cu",11,4),(30,"Zn",12,4),(31,"Ga",13,4),(32,"Ge",14,4),(33,"As",15,4),
 (34,"Se",16,4),(35,"Br",17,4),(36,"Kr",18,4),
 (37,"Rb",1,5),(38,"Sr",2,5),(39,"Y",3,5),(40,"Zr",4,5),(41,"Nb",5,5),(42,"Mo",6,5),(43,"Tc",7,5),(44,"Ru",8,5),
 (45,"Rh",9,5),(46,"Pd",10,5),(47,"Ag",11,5),(48,"Cd",12,5),(49,"In",13,5),(50,"Sn",14,5),(51,"Sb",15,5),
 (52,"Te",16,5),(53,"I",17,5),(54,"Xe",18,5),
 (55,"Cs",1,6),(56,"Ba",2,6),(72,"Hf",4,6),(73,"Ta",5,6),(74,"W",6,6),(75,"Re",7,6),(76,"Os",8,6),(77,"Ir",9,6),
 (78,"Pt",10,6),(79,"Au",11,6),(80,"Hg",12,6),(81,"Tl",13,6),(82,"Pb",14,6),(83,"Bi",15,6),(84,"Po",16,6),
 (85,"At",17,6),(86,"Rn",18,6),
 (87,"Fr",1,7),(88,"Ra",2,7),(104,"Rf",4,7),(105,"Db",5,7),(106,"Sg",6,7),(107,"Bh",7,7),(108,"Hs",8,7),
 (109,"Mt",9,7),(110,"Ds",10,7),(111,"Rg",11,7),(112,"Cn",12,7),(113,"Nh",13,7),(114,"Fl",14,7),(115,"Mc",15,7),
 (116,"Lv",16,7),(117,"Ts",17,7),(118,"Og",18,7),
 # Lanthanides (period shown as row 8, cols 3..17) and actinides (row 9)
 (57,"La",3,8),(58,"Ce",4,8),(59,"Pr",5,8),(60,"Nd",6,8),(61,"Pm",7,8),(62,"Sm",8,8),(63,"Eu",9,8),(64,"Gd",10,8),
 (65,"Tb",11,8),(66,"Dy",12,8),(67,"Ho",13,8),(68,"Er",14,8),(69,"Tm",15,8),(70,"Yb",16,8),(71,"Lu",17,8),
 (89,"Ac",3,9),(90,"Th",4,9),(91,"Pa",5,9),(92,"U",6,9),(93,"Np",7,9),(94,"Pu",8,9),(95,"Am",9,9),(96,"Cm",10,9),
 (97,"Bk",11,9),(98,"Cf",12,9),(99,"Es",13,9),(100,"Fm",14,9),(101,"Md",15,9),(102,"No",16,9),(103,"Lr",17,9),
]

PRESETS = {
 "rare-earths": "Sc,Y,La,Ce,Pr,Nd,Pm,Sm,Eu,Gd,Tb,Dy,Ho,Er,Tm,Yb,Lu",
 "critical-minerals": "Li,Co,Ni,Cu,Mn,Nd,Dy,Pr,Ga,Ge,Si,U,Pt,Pd",
 "battery-metals": "Li,Co,Ni,Mn,Fe,P,Na",
 "platinum-group": "Ru,Rh,Pd,Os,Ir,Pt",
}

CSS = """
<style>
.ptable{display:grid;grid-template-columns:repeat(18,1fr);gap:3px;
  font-family:var(--font-mono,monospace);width:100%}
.ptable .cell{aspect-ratio:1/1;border:1px solid var(--c-line,rgba(0,0,0,.12));
  display:flex;flex-direction:column;justify-content:center;align-items:center;
  font-size:9pt;line-height:1;color:var(--c-ink,#000)}
.ptable .cell .z{font-size:6pt;color:var(--c-dim,rgba(0,0,0,.55))}
.ptable .cell.on{background:var(--c-ink,#000);color:var(--c-surface,#fff);
  border-color:var(--c-ink,#000)}
.ptable .cell.on .z{color:var(--c-surface,#fff)}
.ptable .fgap{grid-column:1/3}
</style>
"""


def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "--list-groups":
        for k, v in PRESETS.items():
            print(f"{k}: {v}")
        return
    raw = sys.argv[1] if len(sys.argv) > 1 else ""
    syms = PRESETS.get(raw, raw)
    on = {s.strip() for s in syms.split(",") if s.strip()}
    cap = sys.argv[2] if len(sys.argv) > 2 else ""

    cells = []
    for z, sym, g, p in E:
        row = p if p <= 7 else p + 1   # one blank row between main table and f-block
        cls = "cell on" if sym in on else "cell"
        cells.append(
            f'<div class="{cls}" style="grid-column:{g};grid-row:{row}">'
            f'<span class="z">{z}</span>{sym}</div>'
        )
    grid = CSS + '<div class="ptable">' + "".join(cells) + "</div>"
    fig = f'<figure class="diagram">{grid}'
    if cap:
        fig += f"<figcaption>{cap}</figcaption>"
    fig += "</figure>"
    print(fig)


if __name__ == "__main__":
    main()
