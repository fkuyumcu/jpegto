# JPG Metadata Rotation Tool (macOS)

This simple macOS-compatible script updates the **Exif orientation metadata** of `.jpg` images to simulate a **90° clockwise rotation** — without modifying the actual image pixels.

### ✅ What it does:
- Edits the `Orientation` tag in the Exif metadata
- Ensures images display correctly in browsers and image viewers
- Works **only on macOS** using `exiftool`

### 📦 Requirements:
- macOS
- `exiftool` installed (`brew install exiftool`)

### 🔧 Usage:
```bash
cd path/to/your/jpg/folder
exiftool -Orientation=6 -n -overwrite_original *.jpg
