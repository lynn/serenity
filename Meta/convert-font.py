#!/usr/bin/env python3
import struct
import sys

def convert_font(font):
    """Convert a bitmap font in !Fnt format to one in +Fnt format."""

    # Parse the !Fnt format font file.
    header = font[:80]
    body = font[80:]
    (magic, gw, gh, ty, vw, gs, bl, ml, ps, wt, name, fam, un) = \
        struct.unpack('<4sBBBBBBBBH32s32sH', header)
    if magic != b'!Fnt':
        raise Exception(f"Not a valid old format font file: "
            f"magic == {magic} instead of '!Fnt'")
    count = [256, 384, 1280, 1536][ty]
    bpg = 4 * gh
    rows = body[:count * bpg]
    widths = body[count * bpg:]

    # Calculate the range mask saying which glyph ranges are included.
    range_mask = bytearray(0x1100)
    rmsz = 0
    for cp in range(count):
        if widths[cp] > 0:
            i = cp // 256 // 8
            range_mask[i] |= 1 << (cp // 256 % 8)
            if i+1 > rmsz: rmsz = i+1
    if rmsz == 0:
        raise Exception("font is empty?")
    range_mask = range_mask[:rmsz]

    new_rows = b''
    new_widths = b''

    # Copy data for each bit set in the mask.
    for i, byte in enumerate(range_mask):
        for j in range(8):
            if byte & (1 << j):
                k = 8*i + j
                new_rows += rows[k*256*bpg:(k+1)*256*bpg].ljust(256*bpg, b'\0')
                new_widths += widths[k*256:(k+1)*256].ljust(256, b'\0')

    bits_set = sum(bin(b).count('1') for b in range_mask)
    assert len(range_mask) == rmsz
    assert len(new_rows) == 256 * bpg * bits_set
    assert len(new_widths) == 256 * bits_set

    # Reassemble in the new font format.
    new_header = struct.pack('<4sBBHBBBBBH32s32sH', b'+Fnt', gw, gh,
            rmsz, vw, gs, bl, ml, ps, wt, name, fam, un)
    return new_header + range_mask + new_rows + new_widths

if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(f'usage: {sys.argv[0]} in.font > out.font')
    with open(sys.argv[1], 'rb') as f:
        if sys.stdout.isatty():
            sys.exit(f'error: stdout is a tty. Try writing to a file instead.')
        new_font = convert_font(f.read())
        sys.stdout.buffer.write(new_font)

