from PIL import Image
import numpy as np
import cv2

def _resize_for_analysis(img: Image.Image, max_side=512) -> Image.Image:
    w, h = img.size
    scale = min(max_side / float(max(w, h)), 1.0)
    if scale < 1.0:
        img = img.resize((int(w * scale), int(h * scale)))
    return img

def estimate_green_fraction(img: Image.Image) -> float:
    img = _resize_for_analysis(img)
    arr = np.asarray(img).astype(np.float32) / 255.0
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    maxc = arr.max(axis=-1)
    minc = arr.min(axis=-1)
    v = maxc
    s = np.where(maxc == 0, 0, (maxc - minc) / (maxc + 1e-6))
    green_mask = (g > r * 1.05) & (g > b * 1.05) & (s > 0.15) & (v > 0.2)
    return round(float(green_mask.mean()), 3)

def estimate_yellow_brown_fraction(img: Image.Image) -> float:
    img = _resize_for_analysis(img)
    arr = np.asarray(img).astype(np.float32) / 255.0
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    v = arr.max(axis=-1)
    yellow_mask = (r > 0.3) & (g > 0.3) & (b < 0.25) & (r > b * 1.3) & (g > b * 1.3)
    brown_mask  = (r > 0.2) & (g > 0.15) & (b < 0.2) & (v < 0.5)
    mask = yellow_mask | brown_mask
    return round(float(mask.mean()), 3)

def estimate_edge_density(img: Image.Image) -> float:
    """Edge density via Sobel gradients (OpenCV)."""
    img = _resize_for_analysis(img)
    gray = np.asarray(img.convert("L"), dtype=np.uint8)
    gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    mag = cv2.magnitude(gx, gy)
    # normalize 0..1 to pick a simple threshold
    mmin, mmax = float(mag.min()), float(mag.max())
    mag_norm = (mag - mmin) / (mmax - mmin + 1e-6)
    edges = (mag_norm > 0.25).astype(np.float32)
    return round(float(edges.mean()), 3)

def guess_crop_family(green_frac: float, edge_density: float, img: Image.Image) -> str:
    if green_frac > 0.5 and edge_density < 0.23:
        return "Gourds (pumpkin/bottle/ash)"
    if 0.25 <= edge_density <= 0.38:
        return "Solanaceae (brinjal/tomato/chili)"
    if edge_density > 0.38 and green_frac > 0.45:
        return "Leafy Greens (spinach/amaranth/methi)"
    return "Unknown"

def guess_stage(green_frac: float, edge_density: float, yellow_brown_frac: float, img: Image.Image) -> str:
    if green_frac < 0.25 or edge_density < 0.18:
        return "Seedling"
    if green_frac >= 0.25 and edge_density >= 0.18 and yellow_brown_frac < 0.3:
        return "Vegetative"
    return "Vegetative"
