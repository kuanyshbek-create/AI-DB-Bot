"""
Логика наложения фото и текста на шаблон баннера.
"""

from PIL import Image, ImageDraw, ImageFont, ImageOps

import config


def _load_font(path: str, size: int, weight: str = None) -> ImageFont.FreeTypeFont:
    try:
        font = ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()
    if weight:
        try:
            font.set_variation_by_name(weight)
        except Exception:
            pass  # шрифт не поддерживает вариации — используем начертание по умолчанию
    return font


def _fit_photo(photo: Image.Image, width: int, height: int) -> Image.Image:
    """object-fit: cover — обрезает и масштабирует фото под width x height без искажений."""
    photo = ImageOps.exif_transpose(photo)
    return ImageOps.fit(photo, (width, height), method=Image.LANCZOS, centering=(0.5, 0.5))


def _make_circle_mask(width: int, height: int) -> Image.Image:
    mask = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, width, height), fill=255)
    return mask


def _char_advance(draw: ImageDraw.ImageDraw, ch: str, font: ImageFont.FreeTypeFont) -> float:
    return draw.textlength(ch, font=font)


def _tracked_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, tracking_px: float) -> float:
    if not text:
        return 0.0
    width = sum(_char_advance(draw, ch, font) for ch in text)
    width += tracking_px * max(len(text) - 1, 0)
    return width


def _wrap_text_tracked(draw, text: str, font, max_width: int, tracking_px: float):
    if not text:
        return []
    words = text.split()
    lines = []
    current = ""
    for word in words:
        trial = f"{current} {word}".strip()
        if _tracked_width(draw, trial, font, tracking_px) <= max_width or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _draw_text_tracked(draw, xy, text: str, font, fill, tracking_px: float):
    """Рисует одну строку с letter-spacing (Pillow не поддерживает tracking нативно)."""
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        x += _char_advance(draw, ch, font) + tracking_px


def _draw_text_block(draw, text: str, block: dict, start_y: int, canvas_width: int) -> int:
    """Рисует блок текста (перенос строк + letter-spacing + опциональное центрирование),
    начиная с start_y. Возвращает y-координату сразу под последней строкой."""
    font = _load_font(block["font"], block["size"], block.get("weight"))
    tracking_px = block.get("letter_spacing", 0) * block["size"]
    lines = _wrap_text_tracked(draw, text, font, block["max_width"], tracking_px)

    align = block.get("align", "left")
    y = start_y
    line_spacing = block.get("line_spacing", 6)
    for line in lines:
        line_width = _tracked_width(draw, line, font, tracking_px)
        if align == "center":
            x = block.get("center_x", canvas_width // 2) - line_width / 2
        else:
            x = block["x"]
        _draw_text_tracked(draw, (x, y), line, font, block["color"], tracking_px)
        bbox = draw.textbbox((0, 0), line, font=font)
        line_height = bbox[3] - bbox[1]
        y += line_height + line_spacing
    return y


def generate_banner(template_path: str, user_photo_path: str, full_name: str, credentials: str, output_path: str) -> str:
    banner = Image.open(template_path).convert("RGBA")

    if config.OUTPUT_SIZE:
        banner = banner.resize(config.OUTPUT_SIZE, Image.LANCZOS)

    canvas_width = banner.width

    # --- Фото ---
    box = config.PHOTO_BOX
    photo = Image.open(user_photo_path).convert("RGBA")
    fitted = _fit_photo(photo, box["width"], box["height"])

    if box.get("center"):
        photo_x = (canvas_width - box["width"]) // 2
    else:
        photo_x = box["x"]

    if box.get("shape") == "circle":
        mask = _make_circle_mask(box["width"], box["height"])
        banner.paste(fitted, (photo_x, box["y"]), mask)
    else:
        banner.paste(fitted, (photo_x, box["y"]))

    # --- Текст: имя (semibold, крупнее), затем регалии (light, мельче) сразу под ним ---
    draw = ImageDraw.Draw(banner)

    name_block = config.NAME_BLOCK
    bottom_y = _draw_text_block(draw, full_name, name_block, name_block["y"], canvas_width)

    credentials_block = config.CREDENTIALS_BLOCK
    credentials_start_y = bottom_y + name_block.get("gap_after", 12)
    _draw_text_block(draw, credentials, credentials_block, credentials_start_y, canvas_width)

    banner = banner.convert("RGB")
    banner.save(output_path, "PNG")
    return output_path
