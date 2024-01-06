def main():

    headUpPixels = [
        "......OOO......",
        ".....O. .O.....",
        "....O.. ..O....",
        "...O... ...O...",
        "..O.... ....O..",
        ".O..... .....O.",
        ".O..... .....O.",
        "O...... ......O",
        "O...... ......O",
        "O...0.0 0.0...O",
        "O....0. .0....O",
        "O...0.0 0.0...O",
        ".O...0.0.0...O.",
        ".O....0 0....O.",
        ".O.....0.....O.",
    ]
    glyph("snakeHeadUp", *headUpPixels)
    glyph("snakeHeadRight", *rotate(headUpPixels))
    glyph("snakeHeadDown", *rotate(rotate(headUpPixels)))
    glyph("snakeHeadLeft", *rotate(rotate(rotate(headUpPixels))))


    bodyVertPixels = [
        ".O. ...O... .O.",
        ".O. ..O O.. .O.",
        "... .O.O.O. .O.",
        ".O. O.O O.O .O.",
        ".O. .O.O.O. .O.",
        ".O. ..O O.. ...",
        ".O. ...O... .O.",
        ".O. ... ... .O.",
        ".O. ...O... .O.",
        "... ..O O.. .O.",
        ".O. .O.O.O. .O.",
        ".O. O.O O.O .O.",
        ".O. .O.O.O. .O.",
        ".O. ..O O.. .O.",
        ".O. ...O... .O.",
    ]
    glyph("snakeBodyVert", *bodyVertPixels)
    glyph("snakeBodyHoriz", *rotate(bodyVertPixels))


    bodyUpRightPixels = [
        ".0. ...O... .0.",
        ".0. ..O O.. ..0",
        ".0. .O.O.O. ...",
        "... ..0 0.. ...",
        "..0 ...0... ...",
        "..0 ... ... 0..",
        "..0 ... ...0.0.",
        "..0 ... ..0 0.0",
        "...0... ...0.0.",
        "...0... ... 0..",
        "... 0.. ... ...",
        "... .0. ... ...",
        "... ..000.. ...",
        "... ... ..00000",
        "... ... ... ...",
    ]
    # bodyUpRightPixels = [
    #     ".0. ...O... 0..",
    #     ".0. ..O O..0...",
    #     "0.. .O.O...0..0",
    #     "0.. ..0 0.. 00.",
    #     "0.. ...0... ...",
    #     "0.. ... ... 0..",
    #     "0.. ... ...0.0.",
    #     ".0. ... ..0 0.0",
    #     ".0. ... ...0.0.",
    #     ".0. ... ... 0..",
    #     "..0 ... ... ...",
    #     "...0... ... ...",
    #     "... 0.. ... ...",
    #     "... .00 ... .00",
    #     "... ... 00000.."]
    glyph("snakeBodyUpRight", *bodyUpRightPixels)
    glyph("snakeBodyRightDown", *rotate(bodyUpRightPixels))
    glyph("snakeBodyDownLeft", *rotate(rotate(bodyUpRightPixels)))
    glyph("snakeBodyLeftUp", *rotate(rotate(rotate(bodyUpRightPixels))))


    tailUpPixels = [
        ".O. ...O... .O.",
        ".O. ..O O.. .O.",
        ".0. .O.O.O. .O.",
        "..0 ..0 0.. 0..",
        "..0 ...0... 0..",
        "...0... ...0...",
        "... 0.. ..0 ...",
        "... .0. .0. ...",
        "... ..O O.. ...",
        "... .0. .0. ...",
        "... .O. .O. ...",
        "... ..O O.. ...",
        "... .O. .O. ...",
        "... .0. .0. ...",
        "... ..0O0.. ...",
    ]
    glyph("snakeTailUp", *tailUpPixels)
    glyph("snakeTailRight", *rotate(tailUpPixels))
    glyph("snakeTailDown", *rotate(rotate(tailUpPixels)))
    glyph("snakeTailLeft", *rotate(rotate(rotate(tailUpPixels))))

    glyph("blank", *(["."*15]*15))


def flipVert(pixels):
    return reversed(pixels)

def flipHoriz(pixels):
    return [list(reversed(ps)) for ps in pixels]

def rotate(pixels):
    """Rotate 90 degrees to the right."""
    size = len(pixels)
    return [
        [pixels[size-1-x][y] for x in range(size)]
        for y in range(size)
    ]

def glyph(name, *pixels):
    """Takes exactly 15 strings, each representing a row of pixels.

    Each space or "." becomes a white pixel. Any other character represents a black pixel. There
    must be exactly 15 pixels in each row.
    """

    assert len(pixels) == 15

    def decode(idx):
        ps = pixels[idx]
        assert len(ps) == 15, f"15 pixels required for row {idx}; found {len(ps)}: {ps}"
        return int("0b" + "".join("0" if p in " ." else "1" for p in reversed(ps)), base=2)

    print(f"        let {name} = Glyph.new("
        + ", ".join(str(decode(i)) for i in range(15))
        + ");")


if __name__ == "__main__":
    main()
