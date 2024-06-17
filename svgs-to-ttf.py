#!fontforge -script

from __future__ import annotations
import os.path
import pathlib
import re
import subprocess

import fontforge


FAMILY_NAME = "IconFX"
IMPORT_OPTIONS = ('removeoverlap', 'correctdir')

line_expr = re.compile("([A-Za-z0-9_]+)\s*=\s*0x([A-Fa-f0-9]{4})")

def set_props(font: fontforge.font) -> None:
    font.familyname = FAMILY_NAME
    font.fontname = f"{FAMILY_NAME}-Regular"
    font.fullname = f"{FAMILY_NAME} Regular"

    font.encoding = "UnicodeFull"
    font.em = 1000
    font.ascent = 1000
    font.descent = 0


def createFont(svg_dir: pathlib.Path, build_dir: pathlib.Path,
               codepoints: pathlib.Path, output: pathlib.Path) -> None:
    font = fontforge.font()
    codes: dict[int, str] = {}
    with codepoints.open() as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            m = line_expr.match(line)
            if not m:
                raise Exception(f"Can't parse line: {line}")

            name = m.group(1)
            number = int(m.group(2), 16)
            if number in codes:
                raise Exception(f"Duplicate codepoint: {number}")
            codes[number] = name

    set_props(font)

    for codepoint, name in codes.items():
        path = svg_dir / f"{name}.svg"
        if not path.exists():
            raise FileNotFoundError(path)
        print("Processing", path)

        build_path = build_dir / path.name
        if not build_path.exists() or (os.path.getmtime(path) >
                                       os.path.getmtime(build_path)):
            print("Converting strokes to path")
            subprocess.run(
                [
                    "inkscape", str(path),
                    "--batch-process",
                    "--actions",
                    "select-all:all;object-stroke-to-path;select-all:all;path-union",
                    "-o", str(build_path)
                ],
                check=True
            )

        glyph = font.createChar(codepoint, name)
        glyph.importOutlines(str(build_path), removeoverlap=True, correctdir=True)

    font.generate(str(output))


if __name__ == "__main__":
    createFont(
        svg_dir=pathlib.Path("./svg"),
        build_dir=pathlib.Path("./build"),
        codepoints=pathlib.Path("./iconfx.codepoints"),
        output=pathlib.Path("./iconfx.ttf")
    )

