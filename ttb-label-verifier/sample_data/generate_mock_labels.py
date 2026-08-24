# import necessary modules
import os 
import json
from PIL import Image, ImageDraw, ImageFont

# Set Up Directory
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_DIR = os.path.join(OUTPUT_DIR, "images")
JSON_DIR = os.path.join(OUTPUT_DIR, "manifests")
os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(JSON_DIR, exist_ok=True)

# Standard, mandatory TTB warning content

# The verbatim TTB Health Warning text required on all alcohol containers
MANDATORY_WARNING = (
    "GOVERNMENT WARNING: (1) ACCORDING TO THE SURGEON GENERAL, WOMEN SHOULD "
    "NOT DRINK ALCOHOLIC BEVERAGES DURING PREGNANCY BECAUSE OF THE RISK OF "
    "BIRTH DEFECTS. (2) CONSUMPTION OF ALCOHOLIC BEVERAGES IMPAIRS YOUR ABILITY "
    "TO DRIVE A CAR OR OPERATE MACHINERY, AND MAY CAUSE HEALTH PROBLEMS."
)

# Standard mandatory TTB warning text
MANDATORY_WARNING = (
    "GOVERNMENT WARNING: (1) ACCORDING TO THE SURGEON GENERAL, WOMEN SHOULD "
    "NOT DRINK ALCOHOLIC BEVERAGES DURING PREGNANCY BECAUSE OF THE RISK OF "
    "BIRTH DEFECTS. (2) CONSUMPTION OF ALCOHOLIC BEVERAGES IMPAIRS YOUR ABILITY "
    "TO DRIVE A CAR OR OPERATE MACHINERY, AND MAY CAUSE HEALTH PROBLEMS."
)

TEST_CASES = [
    # Case 1: Baseline Pass: There is no issue with meta-data and all formatting and contents are correct
    {
        "id": "COLA-2026-001",
        "expected_status": "PASS",
        "app_data": {
            "application_id": "COLA-2026-001",
            "brand_name": "OLD TOM DISTILLERY",
            "class_type": "Kentucky Straight Bourbon Whiskey",
            "alcohol_by_volume": "45%",
            "net_contents": "750 mL"
        },
        "label_text": {
            "brand": "OLD TOM DISTILLERY",
            "type": "Kentucky Straight Bourbon Whiskey",
            "abv": "45% ALC/VOL",
            "volume": "750 mL",
            "warning": MANDATORY_WARNING
        }
    },
        # Case 2: The Warning Header Failure: tests that the government warning is presented in ALL CAPS (GOVERNMENT WARNING) and not Title Case (Government Warning)
    {
        "id": "COLA-2026-002",
        "expected_status": "FAIL_CASING",
        "app_data": {
            "application_id": "COLA-2026-002",
            "brand_name": "BLUE RIDGE BREWING",
            "class_type": "Craft IPA",
            "alcohol_by_volume": "6.5%",
            "net_contents": "12 fl oz"
        },
        "label_text": {
            "brand": "BLUE RIDGE BREWING",
            "type": "Craft IPA",
            "abv": "6.5% ALC/VOL",
            "volume": "12 fl oz",
            # Incorrect lowercase warning header
            "warning": MANDATORY_WARNING.replace("GOVERNMENT WARNING:", "Government Warning:")
        }
    },
    {
        # Case 3: Brand Name Case Descrepency: Flags case descreppency in brand name (all caps vs title case) for human judgement
        "id": "COLA-2026-003",
        "expected_status": "NEEDS_REVIEW_CASE",
        "app_data": {
            "application_id": "COLA-2026-003",
            "brand_name": "STONE'S THROW",
            "class_type": "Dry Gin",
            "alcohol_by_volume": "40%",
            "net_contents": "750 mL"
        },
        "label_text": {
            "brand": "Stone's Throw",  # Mixed case vs ALL CAPS in application
            "type": "Dry Gin",
            "abv": "40% ALC/VOL",
            "volume": "750 mL",
            "warning": MANDATORY_WARNING
        }
    },
    {
        # Case 3: Mismatch is ABV content: the application says that the ABV is 12.5% but the lable says its 10.3%

        "id": "COLA-2026-004",
        "expected_status": "FAIL_ABV_MISMATCH",
        "app_data": {
            "application_id": "COLA-2026-004",
            "brand_name": "VALLEY VINEYARDS",
            "class_type": "Pinot Noir",
            "alcohol_by_volume": "13.5%",
            "net_contents": "750 mL"
        },
        "label_text": {
            "brand": "VALLEY VINEYARDS",
            "type": "Pinot Noir",
            "abv": "12.0% ALC/VOL",  # Mismatched ABV on label
            "volume": "750 mL",
            "warning": MANDATORY_WARNING
        }
    }
]

"""
    Programmatically renders a synthetic alcohol label image using PIL (Pillow).

    Args:
        label_data (dict): Dictionary containing text elements to print on the label.
        output_path (str): Destination file path to write the PNG image.
"""
def render_label_image(label_data, output_path):
    # Creates background of canvas
    width, height = 600, 800
    img = Image.new("RGB", (width, height), color=(250, 248, 242))
    draw = ImageDraw.Draw(img)
    
    # Draws the border
    draw.rectangle([20, 20, width - 20, height - 20], outline=(40, 40, 40), width=3)
    
    # Loads basic system fonts
    font_large = ImageFont.load_default()
    
    # Render data (brand, type, abv, etc)
    draw.text((30, 60), label_data["brand"], fill=(0, 0, 0), font=font_large)
    draw.text((30, 110), label_data["type"], fill=(60, 60, 60), font=font_large)
    draw.text((30, 160), f"{label_data['abv']} | {label_data['volume']}", fill=(0, 0, 0), font=font_large)
    
    # Render Government Warning Box
    draw.rectangle([30, 500, width - 30, height - 40], outline=(100, 100, 100), width=1)
    
    # Word wrap for warning text
    warning_text = label_data["warning"]
    words = warning_text.split()
    lines, current_line = [], ""
    for word in words:
        if len(current_line + " " + word) <= 48:
            current_line += (" " if current_line else "") + word
        else:
            lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)

    # Render line-wrapped warning text line by line
    y_text = 510
    for line in lines:
        draw.text((40, y_text), line, fill=(0, 0, 0), font=font_large)
        y_text += 18

    # Write image to PNG file
    img.save(output_path)


"""
    Iterates through configured test scenarios to generate paired label images,
    JSON manifests, and a consolidated index file.
"""
def generate_dataset():
    manifest_summary = []

    for test in TEST_CASES:
        img_filename = f"{test['id']}.png"
        img_path = os.path.join(IMAGE_DIR, img_filename)
        json_path = os.path.join(JSON_DIR, f"{test['id']}.json")
        
        # 1. Generate PNG image file
        render_label_image(test["label_text"], img_path)
        
        # 2. Save application manifest JSON
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(test["app_data"], f, indent=2)

        # 3. Append metadata to master index collection
        manifest_summary.append({
            "id": test["id"],
            "expected_status": test["expected_status"],
            "image_file": img_filename,
            "manifest_file": f"{test['id']}.json"
        })

    # Write master dataset summary file for testing suites
    with open(os.path.join(OUTPUT_DIR, "dataset_index.json"), "w", encoding="utf-8") as f:
        json.dump(manifest_summary, f, indent=2)
        
    print(f"✅ Generated {len(TEST_CASES)} mock label images & metadata in 'sample_data/'")

# execution
if __name__ == "__main__":
    generate_dataset()