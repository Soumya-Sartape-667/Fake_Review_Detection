import os
import re
import io

import pytesseract
from PIL import Image, ImageEnhance, ImageFilter, ImageOps


# ============================================================
# TESSERACT OCR CONFIGURATION
# ============================================================

TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

if os.path.exists(TESSERACT_PATH):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
else:
    print("WARNING: Tesseract not found at:")
    print(TESSERACT_PATH)


# ============================================================
# OCR SETTINGS
# ============================================================

# Characters that are generally useful in normal review text.
ALLOWED_PUNCTUATION = r"[^a-zA-Z0-9\s.,!?'\-():;%/&]"

# Common OCR garbage patterns.
GARBAGE_PATTERNS = [
    r"\|{2,}",
    r"_{2,}",
    r"-{3,}",
    r"={2,}",
    r"~{2,}",
    r"`{2,}",
    r"\\{2,}",
    r"/{3,}",
]


# ============================================================
# IMAGE PREPROCESSING
# ============================================================

def preprocess_image(img: Image.Image) -> Image.Image:
    """
    Prepare the image for OCR.

    Steps:
    - Convert to RGB
    - Convert to grayscale
    - Upscale small images
    - Improve contrast
    - Sharpen
    - Apply light thresholding
    """

    img = img.convert("RGB")

    # Convert to grayscale
    img = ImageOps.grayscale(img)

    width, height = img.size

    # Upscale small images.
    # OCR generally performs better when text is sufficiently large.
    if width < 1200:
        scale = 1200 / width
        img = img.resize(
            (
                int(width * scale),
                int(height * scale)
            ),
            Image.Resampling.LANCZOS
        )

    # Increase contrast
    contrast = ImageEnhance.Contrast(img)
    img = contrast.enhance(1.7)

    # Slight sharpening
    img = img.filter(ImageFilter.SHARPEN)

    # Autocontrast
    img = ImageOps.autocontrast(img)

    return img


# ============================================================
# TEXT CLEANING
# ============================================================

def clean_ocr_text(text: str) -> str:
    """
    Clean raw Tesseract output so users receive readable text.

    Removes:
    - OCR symbols
    - random Unicode characters
    - repeated punctuation
    - excessive spaces
    - common OCR garbage
    """

    if not text:
        return ""

    # Normalize line endings
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # Remove obvious non-text characters while keeping
    # normal review punctuation.
    text = re.sub(ALLOWED_PUNCTUATION, " ", text)

    # Remove common OCR garbage.
    for pattern in GARBAGE_PATTERNS:
        text = re.sub(pattern, " ", text)

    # Fix spaces around punctuation.
    text = re.sub(r"\s+([,.!?;:%)])", r"\1", text)
    text = re.sub(r"([(\-/])\s+", r"\1", text)

    # Remove repeated punctuation.
    text = re.sub(r"([.!?,;:])\1{1,}", r"\1", text)

    # Remove isolated symbols.
    text = re.sub(
        r"(?<!\w)[|_=~`\\]+(?!\w)",
        " ",
        text
    )

    # Remove extremely short garbage tokens.
    words = text.split()

    cleaned_words = []

    for word in words:

        # Remove tokens that are only punctuation.
        if not re.search(r"[A-Za-z0-9]", word):
            continue

        # Remove tokens containing too many symbols.
        letters_numbers = len(
            re.findall(r"[A-Za-z0-9]", word)
        )

        symbols = len(
            re.findall(r"[^A-Za-z0-9]", word)
        )

        if letters_numbers == 0:
            continue

        if symbols > letters_numbers * 2:
            continue

        cleaned_words.append(word)

    text = " ".join(cleaned_words)

    # Remove excessive whitespace.
    text = re.sub(r"\s{2,}", " ", text).strip()

    return text


# ============================================================
# CONFIDENCE-BASED OCR
# ============================================================

def extract_high_confidence_text(
    processed_image: Image.Image
) -> str:
    """
    Extract OCR words using Tesseract's confidence scores.

    Low-confidence OCR tokens are ignored because they are
    frequently caused by icons, images, logos and UI elements.
    """

    config = "--oem 3 --psm 6 -l eng"

    try:
        data = pytesseract.image_to_data(
            processed_image,
            config=config,
            output_type=pytesseract.Output.DICT
        )

        words = []

        total_items = len(data["text"])

        for i in range(total_items):

            raw_word = data["text"][i].strip()

            if not raw_word:
                continue

            # Tesseract confidence
            try:
                confidence = float(data["conf"][i])
            except (ValueError, TypeError):
                confidence = 0

            # Ignore very low confidence text.
            if confidence < 45:
                continue

            # Clean individual word.
            word = clean_ocr_text(raw_word)

            if not word:
                continue

            # Ignore obvious garbage.
            if len(word) == 1:
                if not re.match(r"[A-Za-z0-9]", word):
                    continue

            # Ignore tokens containing excessive symbols.
            alphanumeric_count = len(
                re.findall(r"[A-Za-z0-9]", word)
            )

            symbol_count = len(
                re.findall(r"[^A-Za-z0-9]", word)
            )

            if alphanumeric_count == 0:
                continue

            if symbol_count > alphanumeric_count * 2:
                continue

            words.append(word)

        return " ".join(words)

    except Exception:
        # Fall back to normal OCR if image_to_data fails.
        return ""


# ============================================================
# NORMAL OCR FALLBACK
# ============================================================

def normal_ocr(processed_image: Image.Image) -> str:
    """
    Standard Tesseract OCR fallback.
    """

    config = "--oem 3 --psm 6 -l eng"

    return pytesseract.image_to_string(
        processed_image,
        config=config
    )


# ============================================================
# MAIN OCR FUNCTION
# ============================================================

def extract_text_from_image(image_bytes: bytes) -> dict:
    """
    Extract readable review text from an uploaded image.

    Returns:

    {
        'success': bool,
        'text': str,
        'word_count': int,
        'error': str | None
    }
    """

    try:

        # ----------------------------------------------------
        # Check Tesseract installation
        # ----------------------------------------------------

        if not os.path.exists(TESSERACT_PATH):

            return {
                "success": False,
                "text": "",
                "word_count": 0,
                "error": (
                    "Tesseract OCR is not installed. "
                    "Please install Tesseract at "
                    "C:\\Program Files\\Tesseract-OCR\\"
                )
            }

        # ----------------------------------------------------
        # Open image
        # ----------------------------------------------------

        img = Image.open(
            io.BytesIO(image_bytes)
        )

        # Verify image
        img.verify()

        # Re-open after verify
        img = Image.open(
            io.BytesIO(image_bytes)
        )

        # ----------------------------------------------------
        # Preprocess
        # ----------------------------------------------------

        processed = preprocess_image(img)

        # ----------------------------------------------------
        # First OCR attempt:
        # confidence-based extraction
        # ----------------------------------------------------

        cleaned = extract_high_confidence_text(
            processed
        )

        cleaned = clean_ocr_text(cleaned)

        # ----------------------------------------------------
        # Fallback if confidence OCR gives too little text
        # ----------------------------------------------------

        if len(cleaned.split()) < 3:

            raw_text = normal_ocr(processed)

            fallback_text = clean_ocr_text(
                raw_text
            )

            if len(fallback_text.split()) > len(
                cleaned.split()
            ):
                cleaned = fallback_text

        # ----------------------------------------------------
        # Final cleanup
        # ----------------------------------------------------

        cleaned = clean_ocr_text(cleaned)

        # ----------------------------------------------------
        # No readable text
        # ----------------------------------------------------

        if not cleaned:

            return {
                "success": False,
                "text": "",
                "word_count": 0,
                "error": (
                    "No readable review text was found. "
                    "Please upload a clearer image containing "
                    "the review text."
                )
            }

        # ----------------------------------------------------
        # Word count
        # ----------------------------------------------------

        word_count = len(
            re.findall(
                r"\b[A-Za-z0-9]+(?:['-][A-Za-z0-9]+)*\b",
                cleaned
            )
        )

        # ----------------------------------------------------
        # Minimum useful text check
        # ----------------------------------------------------

        if word_count < 2:

            return {
                "success": False,
                "text": "",
                "word_count": 0,
                "error": (
                    "The image contains too little readable "
                    "text. Please upload a clearer review image."
                )
            }

        # ----------------------------------------------------
        # SUCCESS
        # ----------------------------------------------------

        return {
            "success": True,
            "text": cleaned,
            "word_count": word_count,
            "error": None
        }

    # ========================================================
    # TESSERACT ERRORS
    # ========================================================

    except pytesseract.TesseractNotFoundError:

        return {
            "success": False,
            "text": "",
            "word_count": 0,
            "error": (
                "Tesseract OCR binary not found. "
                "Please install Tesseract OCR."
            )
        }

    # ========================================================
    # INVALID IMAGE
    # ========================================================

    except Exception as e:

        return {
            "success": False,
            "text": "",
            "word_count": 0,
            "error": (
                f"OCR processing failed: {str(e)}"
            )
        }