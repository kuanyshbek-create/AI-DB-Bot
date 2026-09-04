"""
Конфигурация макета баннера "I'M ATTENDING".

Все координаты — в пикселях считая от левого верхнего угла шаблона (0, 0).
Шаблон: assets/template.png, размер 1620 x 2160.

Макет — вертикальный стек по центру, сразу под логотипом "AI & DIGITAL BRIDGE"
(который заканчивается примерно на y=1010) и до плашек даты/локации (начинаются
примерно на y=1930): фото → имя (SemiBold, крупнее) → регалии (Light, мельче).
"""

import os

TEMPLATE_PATH = os.path.join("assets", "template.png")

# Переменный шрифт Inter (открытая лицензия OFL) — используется как замена
# SF Pro, т.к. лицензия Apple не разрешает использовать SF Pro за пределами
# интерфейсов/контента для платформ Apple.
FONT_VARIABLE = os.path.join("assets", "fonts", "Inter-Variable.ttf")

FONT_WEIGHT_SEMIBOLD = "SemiBold"
FONT_WEIGHT_LIGHT = "Light"

# Отрицательный трекинг (letter-spacing) как доля от размера шрифта.
# -0.05 = -5%, как в фирменной типографике Apple/SF Pro.
LETTER_SPACING = -0.05

# --- Зона под фото пользователя ---
PHOTO_BOX = {
    "center": True,   # центрировать по горизонтали относительно ширины баннера
    "y": 1140,        # чуть ниже логотипа AI & DIGITAL BRIDGE (было 1080)
    "width": 420,
    "height": 420,
    "shape": "circle",
}

# --- Имя и фамилия (крупнее, SemiBold), сразу под фото ---
NAME_BLOCK = {
    "align": "center",
    "y": 1600,
    "font": FONT_VARIABLE,
    "weight": FONT_WEIGHT_SEMIBOLD,
    "size": 92,
    "color": (255, 255, 255),
    "max_width": 1480,
    "line_spacing": 16,
    "letter_spacing": LETTER_SPACING,
    "gap_after": 26,  # отступ до блока регалий
}

# --- Регалии (мельче, Light), сразу под именем ---
CREDENTIALS_BLOCK = {
    "align": "center",
    "font": FONT_VARIABLE,
    "weight": FONT_WEIGHT_LIGHT,
    "size": 52,
    "color": (225, 225, 230),
    "max_width": 1380,
    "line_spacing": 12,
    "letter_spacing": LETTER_SPACING,
}

OUTPUT_SIZE = None
