# 🎨 Real-time Image Color Palette Extractor

A modern **Streamlit** app that extracts the dominant colors from an uploaded image using **OpenCV + k-means clustering**, then matches them to the closest **Tailwind CSS colors** using LAB color space and ΔE2000 for high-accuracy color matching.

## 📊 Features

* **Real-time image upload** with automatic palette extraction.
* **K-means clustering** for dominant color detection.
* **LAB color space + ΔE2000** for perceptually accurate Tailwind matching.
* **Remote Tailwind palette fetch** (with local fallback) to keep colors up-to-date.
* **WCAG contrast ratio** calculation for accessibility compliance.
* **Copy-to-clipboard buttons** for HEX, RGB, and Tailwind tokens.
* **Modern UI** with responsive grid and glassmorphism styling.

## 🛠️ Installation

```bash
# Clone this repository
git clone https://github.com/yourusername/color-palette-extractor.git
cd color-palette-extractor

# Install dependencies
pip install -r requirements.txt

# Run the Streamlit app
streamlit run main.py
```

## 👁️ Usage

1. **Upload** any image via the sidebar.
2. The app will **extract the top N dominant colors**.
3. See **Tailwind matches**, HEX/RGB values, and accessibility info.
4. Click buttons to **copy values** for use in your projects.

## 📚 How It Works

1. **Image Preprocessing**

   * Image is read via OpenCV, resized, and converted to RGB.
2. **Color Extraction**

   * K-means clustering groups pixels into `k` dominant colors.
3. **Color Matching**

   * Colors are converted to LAB space.
   * Closest Tailwind colors are found using ΔE2000.
4. **UI Rendering**

   * Streamlit renders a card grid with swatches, text colors, and metadata.


## 📝 Tech Stack

* **Python**: core logic
* **OpenCV**: image processing
* **NumPy**: numerical operations
* **Streamlit**: frontend UI
* **json5 + requests**: Tailwind palette fetching
* **ΔE2000 formula**: precise color difference calculation

## 📚 File Structure

```
.
├── main.py            # Streamlit app entry point
├── core
|  ├── extractor.py       # Color extraction logic (OpenCV + K-means)
|  ├── color_ops.py       # Color conversions & ΔE2000
|  ├── tailwind.py        # Tailwind palette fetching & LAB conversion
|  ├── ui.py              # HTML/CSS rendering in Streamlit
├── requirements.txt   # Dependencies

```

## 🔗 Live Demo

**Streamlit Cloud**: [Live-Site](https://real-time-image-color-palette-extractor-apps.streamlit.app)

**Author:** [Ertuğrul Mutlu](https://www.linkedin.com/in/ertugrulmutlu/)

**GitHub:** [https://github.com/Ertugrulmutlu](https://github.com/Ertugrulmutlu)

**for details:** [Blog](https://dev.to/ertugrulmutlu/real-time-image-color-palette-extractor-a-deep-dive-into-k-means-lab-and-de2000-4eoi)
