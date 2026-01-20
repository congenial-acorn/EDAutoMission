"""OCR (Optical Character Recognition) service using Tesseract."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from string import ascii_uppercase
from typing import TYPE_CHECKING

import numpy as np
import pytesseract
from PIL import Image, ImageOps

if TYPE_CHECKING:
    from ed_auto_mission.services.screen import ScreenService
    from ed_auto_mission.core.types import ScreenRegion

logger = logging.getLogger(__name__)

# Common Tesseract installation paths
TESSERACT_SEARCH_PATHS = [
    # Windows default
    Path("C:/Program Files/Tesseract-OCR/tesseract.exe"),
    # Linux common paths
    Path("/usr/bin/tesseract"),
    Path("/usr/local/bin/tesseract"),
    # macOS Homebrew
    Path("/opt/homebrew/bin/tesseract"),
    Path("/usr/local/opt/tesseract/bin/tesseract"),
]

# Add Windows drive letter variations
for letter in ascii_uppercase:
    TESSERACT_SEARCH_PATHS.append(Path(f"{letter}:/Tesseract-OCR/tesseract.exe"))


def find_tesseract() -> Path | None:
    """Search for tesseract executable in common locations."""
    for path in TESSERACT_SEARCH_PATHS:
        if path.is_file():
            logger.debug("Found tesseract at: %s", path)
            return path
    return None


def setup_tesseract(path: str | Path | None = None) -> None:
    """
    Configure pytesseract with the tesseract executable path.

    Args:
        path: Explicit path to tesseract, or None to auto-detect.

    Raises:
        FileNotFoundError: If tesseract cannot be found.
    """
    if path:
        tesseract_path = Path(path)
        if not tesseract_path.is_file():
            raise FileNotFoundError(f"Tesseract not found at: {path}")
    else:
        # Check environment variable first
        env_path = os.getenv("TESSERACT_PATH")
        if env_path:
            tesseract_path = Path(env_path)
            if not tesseract_path.is_file():
                raise FileNotFoundError(f"TESSERACT_PATH invalid: {env_path}")
        else:
            tesseract_path = find_tesseract()
            if tesseract_path is None:
                raise FileNotFoundError(
                    "Tesseract not found. Install it or set TESSERACT_PATH environment variable."
                )

    pytesseract.pytesseract.tesseract_cmd = str(tesseract_path)
    logger.info("Tesseract configured: %s", tesseract_path)


class OCRService:
    """Service for performing OCR on screen regions."""

    # OCR configuration presets
    CONFIG_DIGITS_ONLY = "--psm 7 -c tessedit_char_whitelist=0123456789"
    CONFIG_DIGITS_BLOCK = "--psm 6 -c tessedit_char_whitelist=0123456789"
    CONFIG_DEFAULT = ""

    def __init__(self, screen_service: ScreenService, debug_output: bool = False):
        self._screen = screen_service
        self._debug_output = debug_output

    def read_text(
        self,
        region: ScreenRegion | tuple[int, int, int, int],
        config: str = "",
        debug_filename: str | None = None,
    ) -> str:
        """
        Perform OCR on a screen region.

        Args:
            region: Screen region to capture and read
            config: Tesseract configuration string
            debug_filename: If provided, save the captured image

        Returns:
            Extracted text from the region
        """
        filename = debug_filename if self._debug_output else None
        image = self._screen.capture_region(region, filename)
        text = pytesseract.image_to_string(image, config=config)
        logger.debug("OCR result: %s", text.strip())
        return text

    def read_digits(
        self,
        region: ScreenRegion | tuple[int, int, int, int],
        debug_filename: str | None = None,
    ) -> int | None:
        """
        Read digits from a screen region with multiple preprocessing attempts.

        Args:
            region: Screen region to capture and read
            debug_filename: If provided, save the captured image

        Returns:
            Extracted integer value, or None if no digits found
        """
        filename = debug_filename if self._debug_output else None
        image = self._screen.capture_region(region, filename)

        # Try multiple preprocessing variants
        gray = ImageOps.grayscale(image)
        variants = [
            gray,
            ImageOps.autocontrast(gray),
            ImageOps.invert(gray),
            ImageOps.autocontrast(gray).point(lambda p: 255 if p > 140 else 0),
        ]

        configs = [self.CONFIG_DIGITS_ONLY, self.CONFIG_DIGITS_BLOCK]

        for img in variants:
            for cfg in configs:
                candidate = pytesseract.image_to_string(img, config=cfg)
                logger.debug("OCR candidate (%s): %s", cfg, candidate.strip())

                digits = "".join(ch for ch in candidate if ch.isdigit())
                if digits:
                    try:
                        return int(digits)
                    except ValueError:
                        continue

        logger.debug("No digits found in OCR region")
        return None

    def compare_images(
        self,
        image1: Image.Image,
        image2: Image.Image,
    ) -> float:
        """
        Calculate Mean Squared Error between two images.

        Lower values indicate more similar images.

        Args:
            image1: First image
            image2: Second image

        Returns:
            MSE value (0 = identical)
        """
        arr1 = np.array(image1).astype("float")
        arr2 = np.array(image2).astype("float")

        if arr1.shape != arr2.shape:
            # Resize arr2 to match arr1
            from PIL import Image as PILImage
            image2_resized = image2.resize((arr1.shape[1], arr1.shape[0]))
            arr2 = np.array(image2_resized).astype("float")

        mse = np.sum((arr1 - arr2) ** 2) / float(arr1.shape[0] * arr1.shape[1])
        return mse
