import cv2
import numpy as np
import json
import os
import keyboard

HOTBAR_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hotbar.json')
CAPTURE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'captured_image.png')

global threshold_value, current_filter
# Global variables to manage threshold
threshold_value = 100
current_filter = 'House'  # Default filter
hotbar = [None] * 9

# Load hotbar from file if it exists
def load_hotbar():
    if os.path.exists(HOTBAR_FILE):
        try:
            with open(HOTBAR_FILE, 'r') as f:
                data = json.load(f)
            return (data + [None] * 9)[:9]
        except (json.JSONDecodeError, ValueError):
            print("Hotbar file was corrupted or empty, resetting.")
            return [None] * 9
    return [None] * 9

# Save hotbar to file
def save_hotbar(hotbar):
    try:
        with open(HOTBAR_FILE, 'w') as f:
            json.dump(hotbar, f)
            f.flush()  # Force write to disk
            os.fsync(f.fileno())  # Ensure OS flushes buffer
        print(f"Save successful, file size: {os.path.getsize(HOTBAR_FILE)} bytes")
    except Exception as e:
        print(f"Save failed: {e}")

def display_hotbar(frame):
    slot_width = frame.shape[1] // 9
    for i, filter_name in enumerate(hotbar):
        x = i * slot_width
        label = f"{i+1}:{filter_name[:6] if filter_name else '--'}"
        # Highlight current filter's slot
        color = (0, 255, 0) if filter_name == current_filter else (255, 255, 255)
        cv2.putText(frame, label, (x + 5, frame.shape[0] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1)

hotbar = load_hotbar()

# Function to simulate X-ray effect
def simulate_xray_effect(frame, threshold_value):
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    _, xray_frame = cv2.threshold(gray_frame, threshold_value, 255, cv2.THRESH_BINARY_INV)
    xray_frame = cv2.GaussianBlur(xray_frame, (5, 5), 0)
    return xray_frame

# Function to apply edge detection
def apply_edge_detection(frame):
    return cv2.Canny(frame, 100, 200)

# Function to apply color inversion
def invert_colors(frame):
    return cv2.bitwise_not(frame)

# Function to apply neon edges effect
def apply_neon_edges_effect(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)

    # Thicken the edges slightly so they glow more
    kernel = np.ones((2, 2), np.uint8)
    edges = cv2.dilate(edges, kernel, iterations=1)

    # Colour the edges based on the original frame's hue at that pixel
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    hue_channel = hsv[:, :, 0]

    neon = np.zeros_like(frame)
    mask = edges > 0
    neon[mask, 0] = hue_channel[mask]           # Hue from original
    neon[mask, 1] = 255                          # Full saturation
    neon[mask, 2] = 255                          # Full brightness
    neon = cv2.cvtColor(neon, cv2.COLOR_HSV2BGR)

    # Apply a slight glow by blending a blurred version over itself
    glow = cv2.GaussianBlur(neon, (7, 7), 0)
    return cv2.addWeighted(neon, 1.0, glow, 0.6, 0)

# Function to apply sepia effect
def apply_sepia(frame):
    sepia_filter = np.array([[0.272, 0.534, 0.131],
                              [0.349, 0.686, 0.168],
                              [0.393, 0.769, 0.189]])
    return cv2.transform(frame, sepia_filter)

# Function to apply fisheye effect
def apply_fisheye_effect(frame):
    height, width = frame.shape[:2]
    K = np.array([[width/2, 0, width / 2], # [width/2, 0, width / 2],
                  [0, width/2, height / 2], # [0, width/2, height / 2] for stronger fisheye
                  [0, 0, 1]], dtype=np.float32)
    D = np.array([4.5, 1.0, 0, 0], dtype=np.float32)  # Distortion coefficients. 0.5, 0.1 very light, 1.0 medium, 2.5 strong
    map1, map2 = cv2.fisheye.initUndistortRectifyMap(K, D, np.eye(3), K, (width, height), cv2.CV_16SC2)
    return cv2.remap(frame, map1, map2, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)

# Function to apply posterize effect
def apply_posterize(frame, levels=4):
    return (frame // (256 // levels)) * (256 // levels)

# Function to apply warm tone
def apply_warm_tone_effect(frame):
    result = frame.copy().astype(np.float32)
    result[:, :, 0] = np.clip(result[:, :, 0] * 0.8, 0, 255)  # Reduce blue
    result[:, :, 1] = np.clip(result[:, :, 1] * 1.1, 0, 255)  # Slight green boost
    result[:, :, 2] = np.clip(result[:, :, 2] * 1.3, 0, 255)  # Boost red
    return result.astype(np.uint8)

# Function to apply cold tone
def apply_cold_tone_effect(frame):
    result = frame.copy().astype(np.float32)
    result[:, :, 0] = np.clip(result[:, :, 0] * 1.3, 0, 255)  # Boost blue
    result[:, :, 1] = np.clip(result[:, :, 1] * 1.05, 0, 255) # Slight green boost
    result[:, :, 2] = np.clip(result[:, :, 2] * 0.8, 0, 255)  # Reduce red
    return result.astype(np.uint8)

# Function to apply motion blur
def apply_motion_blur(frame, size=15):
    kernel = np.zeros((size, size))
    kernel[int((size - 1) / 2), :] = np.ones(size)
    kernel /= size
    return cv2.filter2D(frame, -1, kernel)

# Function to apply duotone effect
def apply_duotone_effect(frame, color1=(20, 20, 180), color2=(240, 180, 20)):
    # color1 = shadow colour (dark areas), color2 = highlight colour (bright areas)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    result = np.zeros_like(frame)
    for i in range(3):
        result[:, :, i] = (gray / 255.0 * color2[i] + (1 - gray / 255.0) * color1[i]).astype(np.uint8)
    return result

# Function to apply night vision effect
def apply_night_vision(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    hsv[:, :, 1] = hsv[:, :, 1] * 2  # Saturation
    hsv[:, :, 2] = hsv[:, :, 2] * 1.5  # Value
    return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

# Function to apply emboss effect
def apply_emboss(frame):
    kernel = np.array([[0, -1, -1],
                       [1, 0, -1],
                       [1, 1, 0]])
    return cv2.filter2D(frame, -1, kernel)

# Function to apply sketch effect
def apply_sketch(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    inverted = cv2.bitwise_not(gray)
    blurred = cv2.GaussianBlur(inverted, (21, 21), 0)
    inverted_blurred = cv2.bitwise_not(blurred)
    return cv2.divide(gray, inverted_blurred, scale=256)

# Function to apply HSV filter
def apply_hsv(frame):
    return cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

# Function to apply oil paint effect
def apply_oil_paint_effect(frame, size=7, dynamic_ratio=1):
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (size, size))
    dilated = cv2.dilate(frame, kernel)
    eroded = cv2.erode(frame, kernel)
    return cv2.addWeighted(dilated, 0.5, eroded, 0.5, 0)

# Function to apply random color filter (Red, Green, Blue)
def apply_color_filter(frame, color='red'):
    frame = frame.copy()
    if color == 'red':
        frame[:, :, 0] = 0  # Zero out blue channel
        frame[:, :, 1] = 0  # Zero out green channel
    elif color == 'green':
        frame[:, :, 0] = 0  # Zero out blue channel
        frame[:, :, 2] = 0  # Zero out red channel
    elif color == 'blue':
        frame[:, :, 1] = 0  # Zero out green channel
        frame[:, :, 2] = 0  # Zero out red channel
    return frame

def apply_house_effect(frame):
    green_tinted = frame.copy()
    green_tinted[:, :, 0] = 0  # Zero out red channel
    green_tinted[:, :, 2] = 0  # Zero out blue channel

    height, width = green_tinted.shape[:2]

    # Add subtle flicker/noise to green channel
    noise = np.random.randint(0, 30, (height, width), dtype=np.uint8)
    green_tinted[:, :, 1] = cv2.add(green_tinted[:, :, 1], noise)

    scanline_mask = np.ones((height, width, 3), dtype=np.float32)
    scanline_mask[::2] = 0.85  # Every 2nd row at 85% brightness for crt feel

    vignette = cv2.getGaussianKernel(height, height / 1.5) * cv2.getGaussianKernel(width, width / 1.5).T
    vignette = (vignette / np.max(vignette)).astype(np.float32)

    result = (green_tinted.astype(np.float32) * scanline_mask * vignette[:, :, np.newaxis])
    return np.clip(result, 0, 255).astype(np.uint8)

# Function to apply erosion effect
def apply_erosion_effect(frame, kernel_size=3, iterations=1):
    kernel = cv2.getStructuringElement(cv2.MORPH_ERODE, (kernel_size, kernel_size))
    # Options: MORPH_RECT, MORPH_ELLIPSE, MORPH_CROSS
    # kernel = np.ones((kernel_size, kernel_size), np.uint8)
    return cv2.erode(frame, kernel, iterations=iterations)

def apply_dilation_effect(frame, kernel_size=3, iterations=1):
    kernel = cv2.getStructuringElement(cv2.MORPH_DILATE, (kernel_size, kernel_size))
    # Options: MORPH_RECT, MORPH_ELLIPSE, MORPH_CROSS
    # kernel = np.ones((kernel_size, kernel_size), np.uint8)
    return cv2.dilate(frame, kernel, iterations=iterations)

def apply_thermal_effect(frame):
    return cv2.applyColorMap(frame, cv2.COLORMAP_JET)

def apply_pixelate_effect(frame, pixel_size=10):
    height, width = frame.shape[:2]
    temp = cv2.resize(frame, (width // pixel_size, height // pixel_size), interpolation=cv2.INTER_LINEAR)
    pixelated_frame = cv2.resize(temp, (width, height), interpolation=cv2.INTER_NEAREST)
    return pixelated_frame

def apply_vintage_effect(frame):
    height, width = frame.shape[:2] # Extract frame dimensions
    noise = np.random.randint(0, 50, (height, width, 3), dtype=np.uint8) # Generate random grain noise across all 3 colour channels
    
    vignette = cv2.getGaussianKernel(height, height / 2) * cv2.getGaussianKernel(width, width / 2).T # height kernel (column) * width kernel (row) = (height, width) matrix
    vignette = (vignette / np.max(vignette)).astype(np.float32) # Normalise to 0.0-1.0 so centre is full brightness
    vintage_frame = cv2.add(frame, noise) # Overlay grain noise onto frame, clamped to 255 by cv2.add
    vintage_frame = (vintage_frame.astype(np.float32) * vignette[:, :, np.newaxis])  # Multiply each pixel by vignette mask, darkening edges. newaxis expands vignette to 3 channels
    vintage_frame = np.clip(vintage_frame + np.array([10, 10, 0]), 0, 255)  # Add warm colour shift (boost red/green slightly) and clamp values to valid range
    return vintage_frame.astype(np.uint8) # Convert back from float32 to uint8 for OpenCV display

def apply_glitch_effect(frame):
    height, width = frame.shape[:2]
    glitched_frame = frame.copy()
    num_slices = 5
    for _ in range(num_slices):
        y = np.random.randint(0, height - 20)
        h = np.random.randint(10, 30)
        offset = np.random.randint(-20, 20)
        glitched_frame[y:y+h] = np.roll(glitched_frame[y:y+h], offset, axis=1)
    return glitched_frame

morph_kernel_size = 3
morph_iterations = 1

pixel_size = 10

# Function to apply the selected filter
FILTER_MAP = {
    'X-ray':          lambda f: simulate_xray_effect(f, threshold_value),
    'Edge Detection': apply_edge_detection,
    'Invert Colors':  invert_colors,
    'Neon Edges':     apply_neon_edges_effect,
    'Sepia':          apply_sepia,
    'Fisheye':        apply_fisheye_effect,
    'Posterize':      apply_posterize,
    'Warm Tone':      apply_warm_tone_effect,
    'Cold Tone':      apply_cold_tone_effect,
    'Motion Blur':    apply_motion_blur,
    'Duotone':        apply_duotone_effect,
    'Night Vision':   apply_night_vision,
    'Emboss':         apply_emboss,
    'Sketch':         apply_sketch,
    'HSV':            apply_hsv,
    'Oil Paint':      apply_oil_paint_effect,
    'Red Filter':     lambda f: apply_color_filter(f, 'red'),
    'Green Filter':   lambda f: apply_color_filter(f, 'green'),
    'Blue Filter':    lambda f: apply_color_filter(f, 'blue'),
    'House':          apply_house_effect,
    'Erode':          lambda f: apply_erosion_effect(f, kernel_size=morph_kernel_size, iterations=morph_iterations),
    'Dilate':         lambda f: apply_dilation_effect(f, kernel_size=morph_kernel_size, iterations=morph_iterations),
    'Thermal':        apply_thermal_effect,
    'Pixelate':       lambda f: apply_pixelate_effect(f, pixel_size=pixel_size),
    'Vintage':        apply_vintage_effect,
    'Glitch':         apply_glitch_effect,
}

filters = list(FILTER_MAP.keys())

def apply_filter(frame):
    return FILTER_MAP.get(current_filter, lambda f: f)(frame)


FILTER_PARAM_LABELS = {
    'Erode':    lambda: f"Kernel Size: {morph_kernel_size}",
    'Dilate':   lambda: f"Kernel Size: {morph_kernel_size}",
    'Pixelate': lambda: f"Pixel Size: {pixel_size}",
}

# Function to show instructions on the frame
def display_instructions(frame):
    cv2.putText(frame, "Press 'c' to capture | UP/DOWN adjust | 'f' next filter | Shift+N assign hotbar | 'q' quit",
                (10, 30), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 1)
    param_label = FILTER_PARAM_LABELS.get(current_filter, lambda: f"Threshold: {threshold_value}")()
    cv2.putText(frame, param_label, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.putText(frame, f"Current Filter: {current_filter}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

# Initialize the webcam
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

if not cap.isOpened():
    print("Error: Could not open webcam.")
    exit()

filters = ['X-ray', 'Edge Detection', 'Invert Colors', 'Neon Edges', 'Sepia', 
           'Fisheye', 'Posterize', 'Warm Tone', 'Cold Tone', 'Motion Blur', 'Duotone',
           'Night Vision', 'Emboss', 'Sketch', 'HSV', 'Oil Paint', 'Red Filter',
           'Green Filter', 'Blue Filter', 'House', 'Erode', 'Dilate',
           'Thermal', 'Pixelate', 'Vintage', 'Glitch'] # 26 filters

while True:
    
    ret, frame = cap.read()
    if not ret:
        print("Error: Could not read frame.")
        break

    # Apply the selected filter
    filtered_frame = apply_filter(frame)

    # Display hotbar
    display_hotbar(frame)
    
    # Display instructions
    display_instructions(frame)

    # Display the original frame and the filtered frame
    cv2.imshow('Original Frame', frame)
    cv2.imshow('Filtered Frame', filtered_frame)

    # Shift+number assign hotbar
    for i in range(1, 10):
        if keyboard.is_pressed(f'shift+{i}'):
            hotbar[i - 1] = current_filter
            save_hotbar(hotbar)
            print(f"Assigned {current_filter} to slot {i}")
            break

    key = key = cv2.waitKeyEx(1)
    
    # Break the loop on 'q' key press
    if key == ord('q'):
        break

    # Capture image on 'c' key press
    elif key == ord('c'):
        cv2.imwrite(CAPTURE_FILE, filtered_frame)
        print(f"Image captured and saved as '{CAPTURE_FILE}'")

    # Adjust threshold using UP and DOWN arrow keys
    elif key == 2490368:  # Up arrow key
        if current_filter in ['Erode', 'Dilate']:
            morph_kernel_size = min(101, morph_kernel_size + 2)
            print(f"Kernel size: {morph_kernel_size}")
        elif current_filter == 'Pixelate':
            pixel_size = min(100, pixel_size + 1)
            print(f"Pixel size: {pixel_size}")
        else:
            threshold_value = min(threshold_value + 5, 255)
            print(f"Threshold increased to: {threshold_value}")
    elif key == 2621440:  # Down arrow key
        if current_filter in ['Erode', 'Dilate']:
            morph_kernel_size = max(1, morph_kernel_size - 2)
            print(f"Kernel size: {morph_kernel_size}")
        elif current_filter == 'Pixelate':
            pixel_size = max(2, pixel_size - 1)
            print(f"Pixel size: {pixel_size}")
        else:
            threshold_value = max(threshold_value - 5, 0)
            print(f"Threshold decreased to: {threshold_value}")
    
    # Change filter
    # Change filter using 'f' key press
    elif key == ord('f'):
        current_filter = filters[(filters.index(current_filter) + 1) % len(filters)]
        print(f"Filter changed to: {current_filter}")

    # Quick-swap using number keys (1-0)
    elif key in [ord(str(i)) for i in range(1, 10)]:
        if not keyboard.is_pressed('shift'):  # guard against shift bleed
            index = key - ord('1')
            if hotbar[index] is not None:
                current_filter = hotbar[index]
            else:
                print(f"Slot {index + 1} is empty — use Shift+{index + 1} to assign")
    

# Release the capture and close windows
print("Exiting and saving hotbar configuration...")
save_hotbar(hotbar)
cap.release()
cv2.destroyAllWindows()
