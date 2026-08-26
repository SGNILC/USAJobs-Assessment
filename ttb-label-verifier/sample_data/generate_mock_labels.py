"""Generate synthetic labels and their expected verification results.

Run this script to regenerate images/, manifests/, dataset_index.json, and the
legacy manifest.json index.  The index is the canonical fixture contract.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
IMAGE_DIR = ROOT / "images"
MANIFEST_DIR = ROOT / "manifests"

MANDATORY_WARNING = (
    "GOVERNMENT WARNING: (1) ACCORDING TO THE SURGEON GENERAL, WOMEN SHOULD "
    "NOT DRINK ALCOHOLIC BEVERAGES DURING PREGNANCY BECAUSE OF THE RISK OF "
    "BIRTH DEFECTS. (2) CONSUMPTION OF ALCOHOLIC BEVERAGES IMPAIRS YOUR ABILITY "
    "TO DRIVE A CAR OR OPERATE MACHINERY, AND MAY CAUSE HEALTH PROBLEMS."
)
ALTERED_WARNING = MANDATORY_WARNING.replace(
    "MAY CAUSE HEALTH PROBLEMS.", "MAY CAUSE MINOR HEALTH PROBLEMS."
)


def application(case_id: str, brand: str, kind: str, abv: str, volume: str) -> dict[str, str]:
    return {
        "application_id": case_id,
        "brand_name": brand,
        "class_type": kind,
        "alcohol_by_volume": abv,
        "net_contents": volume,
    }


def text(brand: str, kind: str, abv: str | None, volume: str, warning: str | None = MANDATORY_WARNING) -> dict[str, str | None]:
    return {"brand": brand, "type": kind, "abv": abv, "volume": volume, "warning": warning}


def case(
    number: int,
    scenario: str,
    app_brand: str,
    kind: str,
    app_abv: str,
    volume: str,
    *,
    label_brand: str | None = None,
    label_abv: str | None = None,
    warning: str | None = MANDATORY_WARNING,
    expected: str = "PASS",
    artifact: dict[str, Any] | None = None,
    invalid_file: bool = False,
    reason: str | None = None,
) -> dict[str, Any]:
    case_id = f"COLA-2026-{number:03d}"
    expected_result: dict[str, str | int] = {"overall_status": expected}
    if invalid_file:
        expected_result["http_status"] = 400
    if reason:
        expected_result["reason"] = reason
    return {
        "id": case_id,
        "scenario": scenario,
        "app_data": application(case_id, app_brand, kind, app_abv, volume),
        "label_text": text(label_brand or app_brand, kind, label_abv if label_abv is not None else f"{app_abv} ALC/VOL", volume, warning),
        "artifact": artifact or {},
        "invalid_file": invalid_file,
        "expected_result": expected_result,
    }


# The current backend has granular statuses such as FAIL_CASING.  The two
# warning-content cases deliberately define the desired Phase 5 contract,
# FAIL_WARNING_TEXT, so the revised rule/test layer can enforce verbatim text.
TEST_CASES = [
    case(1, "passing_bourbon", "OLD TOM DISTILLERY", "Kentucky Straight Bourbon Whiskey", "45%", "750 mL"),
    case(2, "passing_craft_beer", "BLUE RIDGE BREWING", "Craft IPA", "6.5%", "12 fl oz"),
    case(3, "passing_wine", "VALLEY VINEYARDS", "Pinot Noir", "13.5%", "750 mL"),
    case(4, "passing_canned_cocktail", "HARBOR & HEARTH", "Sparkling Cocktail", "8%", "355 mL"),
    case(5, "warning_title_case", "BLUE RIDGE BREWING", "Craft IPA", "6.5%", "12 fl oz", warning=MANDATORY_WARNING.replace("GOVERNMENT WARNING:", "Government Warning:"), expected="FAIL_CASING"),
    case(6, "warning_text_altered", "COPPER FIELD", "American Whiskey", "42%", "750 mL", warning=ALTERED_WARNING, expected="FAIL_WARNING_TEXT"),
    case(7, "warning_missing", "PINE & PEAR", "Pear Cider", "5%", "500 mL", warning=None, expected="FAIL_MISSING_WARNING"),
    case(8, "brand_case_variance", "STONE'S THROW", "Dry Gin", "40%", "750 mL", label_brand="Stone's Throw", expected="NEEDS_REVIEW_CASE"),
    case(9, "brand_mismatch", "NORTH STAR DISTILLERY", "Vodka", "40%", "1 L", label_brand="SOUTH STAR DISTILLERY", expected="FAIL_BRAND_MISMATCH"),
    case(10, "abv_mismatch", "VALLEY VINEYARDS", "Pinot Noir", "13.5%", "750 mL", label_abv="12.0% ALC/VOL", expected="FAIL_ABV_MISMATCH"),
    case(11, "abv_missing", "MEADOWLARK MEAD", "Honey Wine", "11%", "375 mL", label_abv="", expected="FAIL_ABV_MISMATCH"),
    case(12, "rotation_90_degrees", "HIGH PLAINS RYE", "Straight Rye Whiskey", "46%", "750 mL", artifact={"rotation_degrees": 90}),
    case(13, "minor_rotation", "CEDAR CREEK", "London Dry Gin", "41%", "750 mL", artifact={"rotation_degrees": -8}),
    case(14, "synthetic_glare", "RIVERBEND BREWING", "Amber Ale", "5.8%", "12 fl oz", artifact={"glare": True}),
    case(15, "low_contrast", "GOLDEN HOUR", "Sauvignon Blanc", "12.5%", "750 mL", artifact={"low_contrast": True}),
    case(16, "glare_and_low_contrast", "SUMMIT SPRINGS", "Hard Seltzer", "4.5%", "355 mL", artifact={"glare": True, "low_contrast": True}, expected="NEEDS_REVIEW", reason="Combined glare and low contrast may require manual review."),
    case(17, "warning_lowercase", "MORNING TIDE", "Rum", "40%", "750 mL", warning=MANDATORY_WARNING.replace("GOVERNMENT WARNING:", "government warning:"), expected="FAIL_CASING"),
    case(18, "warning_omits_sentence", "ORCHARD LINE", "Apple Brandy", "38%", "750 mL", warning="GOVERNMENT WARNING: (1) ACCORDING TO THE SURGEON GENERAL, WOMEN SHOULD NOT DRINK ALCOHOLIC BEVERAGES DURING PREGNANCY.", expected="FAIL_WARNING_TEXT"),
    case(19, "rotation_and_glare", "FAR HORIZON", "Wheat Beer", "5.2%", "16 fl oz", artifact={"rotation_degrees": 6, "glare": True}),
    case(20, "corrupt_image_file", "BROKEN BOTTLE", "Test Spirit", "40%", "750 mL", invalid_file=True, expected="INVALID_FILE", reason="Image bytes are intentionally corrupt."),
]


def load_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    names = ("C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/DejaVuSans-Bold.ttf") if bold else ("C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/DejaVuSans.ttf")
    for name in names:
        if Path(name).exists():
            return ImageFont.truetype(name, size)
    return ImageFont.load_default(size=size)


def wrap(draw: ImageDraw.ImageDraw, value: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    lines, current = [], ""
    for word in value.split():
        candidate = f"{current} {word}".strip()
        if current and draw.textlength(candidate, font=font) > max_width:
            lines.append(current)
            current = word
        else:
            current = candidate
    return lines + ([current] if current else [])


def render_label(label_data: dict[str, str | None], output_path: Path, artifact: dict[str, Any]) -> None:
    low_contrast = artifact.get("low_contrast", False)
    background = (238, 232, 215) if not low_contrast else (218, 214, 204)
    foreground = (24, 24, 24) if not low_contrast else (137, 134, 127)
    secondary = (70, 65, 55) if not low_contrast else (150, 147, 140)
    width, height = 1600, 2200
    image = Image.new("RGB", (width, height), background)
    draw = ImageDraw.Draw(image)

    draw.rectangle((55, 55, width - 55, height - 55), outline=foreground, width=7)
    draw.text((120, 180), label_data["brand"] or "", fill=foreground, font=load_font(72, bold=True))
    draw.text((120, 320), label_data["type"] or "", fill=secondary, font=load_font(42))
    details = " | ".join(item for item in (label_data["abv"], label_data["volume"]) if item)
    draw.text((120, 410), details, fill=foreground, font=load_font(42))

    if warning := label_data["warning"]:
        warning_font = load_font(28)
        draw.rectangle((110, 1330, width - 110, height - 130), outline=foreground, width=3)
        for index, line in enumerate(wrap(draw, warning, warning_font, width - 300)):
            draw.text((150, 1375 + index * 43), line, fill=foreground, font=warning_font)

    if artifact.get("glare"):
        overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
        glare = ImageDraw.Draw(overlay)
        glare.ellipse((900, 150, 1700, 1450), fill=(255, 255, 255, 115))
        glare.ellipse((1040, 280, 1580, 1180), fill=(255, 255, 255, 75))
        image = Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")

    if degrees := artifact.get("rotation_degrees"):
        image = image.rotate(degrees, expand=True, fillcolor=background)
    image.save(output_path, format="PNG")


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def generate_dataset() -> None:
    IMAGE_DIR.mkdir(exist_ok=True)
    MANIFEST_DIR.mkdir(exist_ok=True)
    index = []
    for fixture in TEST_CASES:
        image_file = f"{fixture['id']}.png"
        manifest_file = f"{fixture['id']}.json"
        write_json(MANIFEST_DIR / manifest_file, fixture["app_data"])
        if fixture["invalid_file"]:
            (IMAGE_DIR / image_file).write_bytes(b"This is deliberately not a valid PNG file.\n")
        else:
            render_label(fixture["label_text"], IMAGE_DIR / image_file, fixture["artifact"])
        index.append({
            "id": fixture["id"],
            "scenario": fixture["scenario"],
            "image_file": image_file,
            "manifest_file": manifest_file,
            "input_kind": "invalid_file" if fixture["invalid_file"] else "image",
            "artifact": fixture["artifact"],
            "expected_result": fixture["expected_result"],
            "expected_status": fixture["expected_result"]["overall_status"],
        })

    write_json(ROOT / "dataset_index.json", index)
    write_json(ROOT / "manifest.json", index)
    print(f"Generated {len(index)} synthetic label fixtures in '{ROOT}'.")


if __name__ == "__main__":
    generate_dataset()
