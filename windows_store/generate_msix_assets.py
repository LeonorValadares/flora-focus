from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent.parent
SOURCE_ICON = ROOT / "FloraFocus.png"
ASSETS_DIR = ROOT / "windows_store" / "msix" / "Assets"
BACKGROUND = "#112F5E"


def square_asset(size: int, name: str, icon_scale: float = 0.76) -> None:
    base = Image.new("RGBA", (size, size), BACKGROUND)
    icon_size = max(1, int(size * icon_scale))
    icon = ICON.resize((icon_size, icon_size), Image.LANCZOS)
    left = (size - icon_size) // 2
    top = (size - icon_size) // 2
    base.alpha_composite(icon, (left, top))
    base.save(ASSETS_DIR / name)


def wide_asset(width: int, height: int, name: str, icon_scale: float = 0.7) -> None:
    base = Image.new("RGBA", (width, height), BACKGROUND)
    icon_size = max(1, int(min(width, height) * icon_scale))
    icon = ICON.resize((icon_size, icon_size), Image.LANCZOS)
    left = (width - icon_size) // 2
    top = (height - icon_size) // 2
    base.alpha_composite(icon, (left, top))
    base.save(ASSETS_DIR / name)


ASSETS_DIR.mkdir(parents=True, exist_ok=True)
ICON = Image.open(SOURCE_ICON).convert("RGBA")

square_asset(44, "Square44x44Logo.png")
square_asset(44, "Square44x44Logo.targetsize-44_altform-unplated.png")
square_asset(50, "StoreLogo.png")
square_asset(150, "Square150x150Logo.png")
square_asset(310, "Square310x310Logo.png")
wide_asset(310, 150, "Wide310x150Logo.png")
wide_asset(620, 300, "SplashScreen.png", icon_scale=0.62)
