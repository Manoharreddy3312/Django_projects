"""Generate simple branded PNG placeholders (Pillow) for seed data and demos."""
from io import BytesIO

from django.core.files.base import ContentFile
from PIL import Image, ImageDraw, ImageFont


def _font(size: int):
    for path in (
        'C:\\Windows\\Fonts\\arial.ttf',
        'C:\\Windows\\Fonts\\segoeui.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
    ):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _text_width(draw, text, font):
    if hasattr(draw, 'textlength'):
        return draw.textlength(text, font=font)
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0]


def _wrap_title(draw, text, font, max_width):
    words = text.split()
    lines = []
    line = []
    for w in words:
        test = ' '.join(line + [w])
        if _text_width(draw, test, font) <= max_width:
            line.append(w)
        else:
            if line:
                lines.append(' '.join(line))
            line = [w]
    if line:
        lines.append(' '.join(line))
    return lines[:3]


def category_banner(name: str, slug: str, rgb: tuple[int, int, int]) -> ContentFile:
    w, h = 900, 360
    img = Image.new('RGB', (w, h), (248, 249, 250))
    draw = ImageDraw.Draw(img)
    m = 16
    draw.rounded_rectangle([m, m, w - m, h - m], radius=28, fill=rgb)
    # subtle highlight
    draw.rounded_rectangle([m + 6, m + 6, w - m - 6, int(h * 0.45)], radius=22, fill=tuple(min(255, c + 35) for c in rgb))
    font = _font(42)
    font_sm = _font(20)
    for i, line in enumerate(_wrap_title(draw, name, font, w - 2 * m - 48)):
        draw.text((m + 32, m + 36 + i * 48), line, fill=(255, 255, 255), font=font)
    draw.text((m + 32, h - m - 52), 'FlipMart category', fill=(255, 255, 255), font=font_sm)
    buf = BytesIO()
    img.save(buf, format='PNG', optimize=True)
    buf.seek(0)
    return ContentFile(buf.read(), name=f'cat-{slug}.png')


def product_card(name: str, slug: str, rgb: tuple[int, int, int]) -> ContentFile:
    w, h = 720, 720
    img = Image.new('RGB', (w, h), (233, 236, 239))
    draw = ImageDraw.Draw(img)
    m = 20
    draw.rounded_rectangle([m, m, w - m, h - m], radius=32, fill=rgb)
    inner = [m + 24, m + 24, w - m - 24, int(h * 0.62)]
    draw.rounded_rectangle(inner, radius=24, fill=tuple(max(0, c - 25) for c in rgb))
    font = _font(32)
    y = int(h * 0.68)
    for i, line in enumerate(_wrap_title(draw, name, font, w - 2 * m - 48)):
        draw.text((m + 36, y + i * 40), line, fill=(255, 255, 255), font=font)
    draw.text((m + 36, h - m - 44), 'FlipMart', fill=(255, 255, 255), font=_font(18))
    buf = BytesIO()
    img.save(buf, format='PNG', optimize=True)
    buf.seek(0)
    return ContentFile(buf.read(), name=f'prd-{slug}.png')


def product_extra(slug: str, rgb: tuple[int, int, int], variant: int = 0) -> ContentFile:
    w, h = 640, 640
    img = Image.new('RGB', (w, h), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    shift = variant * 28
    rgb2 = tuple(max(0, min(255, c - shift)) for c in rgb)
    draw.ellipse([40, 40, w - 40, h - 40], fill=rgb2, outline=tuple(min(255, c + 40) for c in rgb2), width=6)
    fnt = _font(24)
    text = f'Gallery {variant + 1}'
    bbox = draw.textbbox((0, 0), text, font=fnt)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((w - tw) // 2, (h - th) // 2), text, fill=(255, 255, 255), font=fnt)
    buf = BytesIO()
    img.save(buf, format='PNG', optimize=True)
    buf.seek(0)
    return ContentFile(buf.read(), name=f'prd-{slug}-x{variant}.png')
