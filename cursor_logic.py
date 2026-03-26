import winreg
import ctypes
import os

# Registry path for cursors
REG_PATH = r"Control Panel\Cursors"

# Map of cursor names to registry keys
CURSOR_MAPPING = {
    "Normal Select": "Arrow",
    "Help Select": "AppStarting", # Wait is Busy, AppStarting is Working in Background
    "Working In Background": "AppStarting",
    "Busy": "Wait",
    "Precision Select": "Crosshair",
    "Text Select": "IBeam",
    "Handwriting": "NWPen",
    "Unavailable": "No",
    "Vertical Resize": "SizeNS",
    "Horizontal Resize": "SizeWE",
    "Diagonal Resize 1": "SizeNWSE",
    "Diagonal Resize 2": "SizeNESW",
    "Move": "SizeAll",
    "Alternate Select": "UpArrow",
    "Link Select": "Hand"
}

# Keywords to identify cursor roles in filenames
ROLE_KEYWORDS = {
    "Arrow": ["normal", "cursor", "arrow", "select", "pointer"],
    "Help": ["help"],
    "AppStarting": ["working", "background", "loading", "loading-ring"],
    "Wait": ["busy", "wait", "loading..."],
    "Crosshair": ["precision", "cross"],
    "IBeam": ["text", "ibeam"],
    "NWPen": ["pen", "handwriting"],
    "No": ["unavailable", "no", "denied"],
    "SizeNS": ["vertical", "ns"],
    "SizeWE": ["horizontal", "we"],
    "SizeNWSE": ["nwse", "diagonal-1"],
    "SizeNESW": ["nesw", "diagonal-2"],
    "SizeAll": ["move", "grab"],
    "UpArrow": ["alternate", "up"],
    "Hand": ["link", "hand", "pointer-blue", "pointer-reverse"]
}

def get_role_from_filename(filename):
    """
    Attempts to identify the Windows cursor role for a given filename.
    Returns the role name (e.g., 'Arrow') or None.
    """
    fn = filename.lower()
    
    # 1. Try exact Minecraft-style mapping first
    base_name = os.path.splitext(filename)[0]
    if base_name in FILE_TO_REG:
        return FILE_TO_REG[base_name]

    # 2. Try the .crs file role or keyword matching
    # Keyword matching is much more flexible for packs without strict naming
    best_role = None
    max_priority = -1
    
    for role, keywords in ROLE_KEYWORDS.items():
        for i, kw in enumerate(keywords):
            if kw in fn:
                # Lower index in keywords list means higher priority
                priority = 100 - i
                if priority > max_priority:
                    max_priority = priority
                    best_role = role
    
    return best_role

SPI_SETCURSORS = 0x0057
IMAGE_CURSOR = 2
LR_LOADFROMFILE = 0x0010

def get_cursor_preview(file_path, size=32):
    """
    Extracts a static preview of the cursor using Windows API.
    Returns a PIL Image or None.
    """
    try:
        import win32gui
        import win32con
        from PIL import Image
        import ctypes
        import struct

        # Load the cursor
        hcursor = win32gui.LoadImage(0, str(file_path), win32con.IMAGE_CURSOR, size, size, win32con.LR_LOADFROMFILE)
        if not hcursor:
            return None

        # Create a device context
        hdc_screen = win32gui.GetDC(0)
        hdc_mem = win32gui.CreateCompatibleDC(hdc_screen)
        hbm = win32gui.CreateCompatibleBitmap(hdc_screen, size, size)
        old_hbm = win32gui.SelectObject(hdc_mem, hbm)

        # Draw a white background
        brush = win32gui.CreateSolidBrush(win32gui.GetSysColor(win32con.COLOR_WINDOW))
        win32gui.FillRect(hdc_mem, (0, 0, size, size), brush)
        win32gui.DeleteObject(brush)

        # Draw the cursor
        win32gui.DrawIconEx(hdc_mem, 0, 0, hcursor, size, size, 0, 0, win32con.DI_NORMAL)

        # Convert bitmap to PIL image using ctypes
        # We'll use GetDIBits for reliability
        gdi32 = ctypes.windll.gdi32
        gdi32.GetDIBits.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint, ctypes.c_uint, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint]
        gdi32.GetDIBits.restype = ctypes.c_int

        header = struct.pack('LllHHLLllLL', 40, size, -size, 1, 32, 0, size*size*4, 0, 0, 0, 0)
        bmi = ctypes.create_string_buffer(header)
        bits = ctypes.create_string_buffer(size * size * 4)
        
        res = gdi32.GetDIBits(int(hdc_mem), int(hbm), 0, size, bits, bmi, 0)
        
        if res:
            img = Image.frombuffer('RGBA', (size, size), bits.raw, 'raw', 'BGRA', 0, 1)
            img = img.convert("RGB")
        else:
            img = None

        # Cleanup
        win32gui.SelectObject(hdc_mem, old_hbm)
        win32gui.DeleteObject(hbm)
        win32gui.DeleteDC(hdc_mem)
        win32gui.ReleaseDC(0, hdc_screen)
        win32gui.DestroyIcon(hcursor)
        
        return img
    except Exception as e:
        print(f"Preview error for {file_path}: {e}")
        return None

def set_cursor(cursor_key, file_path):
    """Sets a specific cursor in the registry and applies it."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, cursor_key, 0, winreg.REG_EXPAND_SZ, file_path)
        return True
    except Exception as e:
        print(f"Error setting cursor {cursor_key}: {e}")
        return False

def apply_cursors():
    """Tells Windows to reload cursors from the registry."""
    ctypes.windll.user32.SystemParametersInfoW(SPI_SETCURSORS, 0, None, 0x01 | 0x02)

def reset_to_default():
    """Resets all cursors to Windows defaults."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_SET_VALUE) as key:
            for key_name in CURSOR_MAPPING.values():
                winreg.SetValueEx(key, key_name, 0, winreg.REG_EXPAND_SZ, "")
            # Also reset 'Scheme Name'
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "Windows Default")
            
        apply_cursors()
        return True
    except Exception as e:
        print(f"Error resetting cursors: {e}")
        return False

def set_theme(directory):
    """Sets all cursors from a directory (theme) using smart mapping."""
    files = os.listdir(directory)
    for filename in files:
        if filename.endswith((".ani", ".cur")):
            reg_key = get_role_from_filename(filename)
            if reg_key:
                file_path = os.path.abspath(os.path.join(directory, filename))
                set_cursor(reg_key, file_path)
    
    apply_cursors()
