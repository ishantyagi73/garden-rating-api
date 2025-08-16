from PIL import Image
import numpy as np

def _resize_for_analysis(img: Image.Image, max_side=512) -> Image.Image:
    w, h = img.size
    scale = min(max_side / float(max(w, h)), 1.0)
    if scale < 1.0:
        img = img.resize((int(w * scale), int(h * scale)))
    return img

def estimate_green_fraction(img: Image.Image) -> float:
    """Approximate green pixel proportion using simple channel heuristics."""
    img = _resize_for_analysis(img)
    arr = np.asarray(img).astype(np.float32) / 255.0
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    maxc = arr.max(axis=-1)
    minc = arr.min(axis=-1)
    v = maxc
    s = np.where(maxc == 0, 0, (maxc - minc) / (maxc + 1e-6))
    green_mask = (g > r * 1.05) & (g > b * 1.05) & (s > 0.15) & (v > 0.2)
    frac = float(green_mask.mean())
    return round(frac, 3)

def estimate_yellow_brown_fraction(img: Image.Image) -> float:
    """Rough proxy for stress: yellow/brown-ish pixels by channel ratios."""
    img = _resize_for_analysis(img)
    arr = np.asarray(img).astype(np.float32) / 255.0
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    v = arr.max(axis=-1)
    yellow_mask = (r > 0.3) & (g > 0.3) & (b < 0.25) & (r > b * 1.3) & (g > b * 1.3)
    brown_mask = (r > 0.2) & (g > 0.15) & (b < 0.2) & (v < 0.5)
    mask = yellow_mask | brown_mask
    return round(float(mask.mean()), 3)

def estimate_edge_density(img: Image.Image) -> float:
    """Edge density as a canopy fullness proxy using Sobel-like gradients."""
    img = _resize_for_analysis(img)
    gray = np.asarray(img.convert("L"), dtype=np.float32) / 255.0
    Kx = np.array([[1,0,-1],[2,0,-2],[1,0,-1]], dtype=np.float32)
    Ky = np.array([[1,2,1],[0,0,0],[-1,-2,-1]], dtype=np.float32)
    from scipy.signal import convolve2d
    gx = convolve2d(gray, Kx, mode="same", boundary="symm")
    gy = convolve2d(gray, Ky, mode="same", boundary="symm")
    mag = np.sqrt(gx * gx + gy * gy)
    threshold = 0.25
    edges = (mag > threshold).astype(np.float32)
    return round(float(edges.mean()), 3)

def guess_crop_family(green_frac: float, edge_density: float, img: Image.Image) -> str:
    """Very rough crop family guess based on texture/leaf size cues."""
    if green_frac > 0.5 and edge_density < 0.23:
        return "Gourds (pumpkin/bottle/ash)"
    if 0.25 <= edge_density <= 0.38:
        return "Solanaceae (brinjal/tomato/chili)"
    if edge_density > 0.38 and green_frac > 0.45:
        return "Leafy Greens (spinach/amaranth/methi)"
    return "Unknown"

def guess_stage(green_frac: float, edge_density: float, yellow_brown_frac: float, img: Image.Image) -> str:
    """Broad stage buckets (MVP heuristics)."""
    if green_frac < 0.25 or edge_density < 0.18:
        return "Seedling"
    if green_frac >= 0.25 and edge_density >= 0.18 and yellow_brown_frac < 0.3:
        return "Vegetative"
    return "Vegetative"
