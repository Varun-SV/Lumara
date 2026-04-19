"""
test_basic_processors.py — Unit tests for the basic, whitebalance, hsl,
detail, geometry, and portrait processors.
"""

import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

# Allow importing from the python/ directory
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "python"))

from processors.basic import apply_basic
from processors.whitebalance import apply_white_balance
from processors.hsl import apply_hsl
from processors.detail import apply_detail
from processors.geometry import apply_geometry
from processors.portrait import apply_portrait


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_test_image(width: int = 100, height: int = 100, colour: tuple = (128, 128, 128)) -> Image.Image:
    """Create a solid-colour RGB test image."""
    return Image.new("RGB", (width, height), colour)


def mean_brightness(image: Image.Image) -> float:
    """Return the mean pixel value across all channels."""
    return float(np.array(image).mean())


# ---------------------------------------------------------------------------
# Basic processor
# ---------------------------------------------------------------------------

class TestBasicProcessor:
    def test_exposure_increases_brightness(self):
        img = make_test_image(colour=(100, 100, 100))
        result = apply_basic(img, {"exposure": 1.0})
        assert mean_brightness(result) > mean_brightness(img)

    def test_exposure_decreases_brightness(self):
        img = make_test_image(colour=(200, 200, 200))
        result = apply_basic(img, {"exposure": -1.0})
        assert mean_brightness(result) < mean_brightness(img)

    def test_zero_exposure_no_change(self):
        img = make_test_image(colour=(128, 128, 128))
        result = apply_basic(img, {"exposure": 0})
        assert abs(mean_brightness(result) - mean_brightness(img)) < 1.0

    def test_positive_vibrance_increases_saturation(self):
        # Saturated input: red channel dominant
        img = make_test_image(colour=(200, 50, 50))
        result = apply_basic(img, {"vibrance": 50})
        arr_in = np.array(img, dtype=np.float32)
        arr_out = np.array(result, dtype=np.float32)
        # Red-green spread should increase
        assert float(arr_out[:, :, 0].mean()) != pytest.approx(float(arr_in[:, :, 0].mean()), abs=0.5)

    def test_vignette_darkens_corners(self):
        img = make_test_image(width=200, height=200, colour=(200, 200, 200))
        result = apply_basic(img, {"vignette_amount": -80})
        arr = np.array(result, dtype=np.float32)
        centre_brightness = arr[95:105, 95:105].mean()
        corner_brightness = arr[:10, :10].mean()
        assert centre_brightness > corner_brightness

    def test_returns_rgb_image(self):
        img = make_test_image()
        result = apply_basic(img, {"contrast": 30, "saturation": 20})
        assert result.mode == "RGB"


# ---------------------------------------------------------------------------
# White balance processor
# ---------------------------------------------------------------------------

class TestWhiteBalanceProcessor:
    def test_warm_shift_increases_red(self):
        img = make_test_image(colour=(150, 150, 150))
        result = apply_white_balance(img, {"temperature": 50})
        arr = np.array(result)
        assert arr[:, :, 0].mean() > arr[:, :, 2].mean()

    def test_cool_shift_increases_blue(self):
        img = make_test_image(colour=(150, 150, 150))
        result = apply_white_balance(img, {"temperature": -50})
        arr = np.array(result)
        assert arr[:, :, 2].mean() > arr[:, :, 0].mean()

    def test_zero_temperature_no_change(self):
        img = make_test_image(colour=(150, 150, 150))
        result = apply_white_balance(img, {"temperature": 0})
        assert abs(mean_brightness(result) - mean_brightness(img)) < 1.0

    def test_tone_curve_luma_identity(self):
        img = make_test_image(colour=(100, 150, 200))
        identity_pts = [[0, 0], [255, 255]]
        result = apply_white_balance(img, {"tone_curve": {"luma": identity_pts}})
        assert abs(mean_brightness(result) - mean_brightness(img)) < 2.0


# ---------------------------------------------------------------------------
# HSL processor
# ---------------------------------------------------------------------------

class TestHSLProcessor:
    def test_no_hsl_params_returns_unchanged(self):
        img = make_test_image(colour=(255, 50, 50))
        result = apply_hsl(img, {})
        assert np.array_equal(np.array(img), np.array(result))

    def test_red_desaturation(self):
        img = make_test_image(colour=(255, 0, 0))
        result = apply_hsl(img, {"hsl": {"red": {"saturation": -100}}})
        arr = np.array(result, dtype=np.float32)
        # Desaturated red should have similar R, G, B values
        r_mean, g_mean = arr[:, :, 0].mean(), arr[:, :, 1].mean()
        assert abs(r_mean - g_mean) < 30.0

    def test_returns_rgb(self):
        img = make_test_image()
        result = apply_hsl(img, {"hsl": {"blue": {"luminance": 20}}})
        assert result.mode == "RGB"


# ---------------------------------------------------------------------------
# Detail processor
# ---------------------------------------------------------------------------

class TestDetailProcessor:
    def test_sharpening_does_not_change_size(self):
        img = make_test_image(width=150, height=150)
        result = apply_detail(img, {"sharpening_amount": 80, "sharpening_radius": 1.0})
        assert result.size == img.size

    def test_noise_reduction_does_not_change_size(self):
        img = make_test_image(width=150, height=150)
        result = apply_detail(img, {"noise_luminance": 50})
        assert result.size == img.size

    def test_zero_params_returns_image(self):
        img = make_test_image()
        result = apply_detail(img, {})
        assert result.size == img.size


# ---------------------------------------------------------------------------
# Geometry processor
# ---------------------------------------------------------------------------

class TestGeometryProcessor:
    def test_straighten_zero_no_size_change(self):
        img = make_test_image(width=200, height=150)
        result = apply_geometry(img, {"straighten_angle": 0})
        assert result.size == img.size

    def test_crop_16_9_correct_aspect(self):
        img = make_test_image(width=400, height=300)
        result = apply_geometry(img, {"crop_aspect": "16:9"})
        w, h = result.size
        ratio = w / h
        assert abs(ratio - 16 / 9) < 0.05

    def test_crop_1_1_square(self):
        img = make_test_image(width=300, height=200)
        result = apply_geometry(img, {"crop_aspect": "1:1"})
        w, h = result.size
        assert abs(w - h) <= 1

    def test_straighten_small_angle(self):
        img = make_test_image(width=300, height=200)
        result = apply_geometry(img, {"straighten_angle": 2.0})
        # Straightened image should be slightly smaller than original
        assert result.size[0] <= img.size[0]
        assert result.size[1] <= img.size[1]


# ---------------------------------------------------------------------------
# Portrait processor
# ---------------------------------------------------------------------------

class TestPortraitProcessor:
    def test_empty_portrait_params_no_change(self):
        img = make_test_image(colour=(180, 140, 130))
        result = apply_portrait(img, {})
        assert np.array_equal(np.array(img), np.array(result))

    def test_skin_smoothing_returns_rgb(self):
        img = make_test_image(colour=(220, 160, 140))
        result = apply_portrait(img, {"portrait": {"skin_smoothing": 50}})
        assert result.mode == "RGB"

    def test_face_brightness_positive_increases_brightness(self):
        img = make_test_image(colour=(100, 80, 70))
        result = apply_portrait(img, {"portrait": {"face_brightness": 30}})
        assert mean_brightness(result) > mean_brightness(img)
