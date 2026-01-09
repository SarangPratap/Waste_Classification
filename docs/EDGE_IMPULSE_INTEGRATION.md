# Edge Impulse Model Integration Guide

## ⚠️ CRITICAL: Install Your Edge Impulse Library

The ESP32-CAM code requires your **actual Edge Impulse library** to perform real ML inference. Without it, the code will not compile.

## 📦 Step 1: Download Your Edge Impulse Library

1. Go to your Edge Impulse project: https://studio.edgeimpulse.com
2. Navigate to **Deployment** tab
3. Select **Arduino library**
4. Select optimization: **Quantized (int8)** for ESP32
5. Enable **EON Compiler** (optional, for better performance)
6. Click **Build**
7. Download the `.zip` file (e.g., `Waste_classification_inferencing.zip`)

## 📁 Step 2: Install the Library in PlatformIO

### Method A: Via PlatformIO Library Manager (Recommended)

1. Extract the downloaded `.zip` file
2. Copy the entire extracted folder to your project's `lib/` directory:
   ```
   Waste_Classification/
   ├── lib/
   │   └── Waste_classification_inferencing/  ← Your Edge Impulse library
   │       ├── src/
   │       ├── edge-impulse-sdk/
   │       ├── model-parameters/
   │       ├── tflite-model/
   │       └── library.json
   ├── src/
   │   └── main.cpp
   └── platformio.ini
   ```

### Method B: Manual Installation

1. Extract the `.zip` file to a temporary location
2. Copy the folder to: `<project>/lib/Waste_classification_inferencing/`
3. Verify the structure matches the example above

## 🔧 Step 3: Verify Integration

After installing the library, your code should compile successfully with these includes:

```cpp
#include <Waste_classification_inferencing.h>
#include "edge-impulse-sdk/dsp/image/image.hpp"
```

## 🧪 Step 4: Test Compilation

```bash
# Clean build
pio run --target clean

# Compile
pio run

# Should compile successfully without errors
```

## 📊 Step 5: Verify Your Model Categories

Check that your Edge Impulse model has these 9 categories:
- battery
- biological
- cardboard
- clothes
- glass
- metal
- paper
- plastic
- shoe

If your categories are different, update the web dashboard colors in `server/static/js/app.js`.

## ❗ Common Issues

### Issue 1: "Waste_classification_inferencing.h: No such file or directory"

**Solution:** The Edge Impulse library is not installed. Follow Step 2 above.

### Issue 2: Library name mismatch

If your Edge Impulse project has a different name, update the include in `src/main.cpp`:

```cpp
// Change this line to match your library name
#include <YOUR_PROJECT_NAME_inferencing.h>
```

### Issue 3: Compilation errors in Edge Impulse SDK

**Solution:** Make sure you downloaded the **Arduino library** (not C++ library) from Edge Impulse deployment.

### Issue 4: Memory issues

If you get heap/memory errors:
1. Ensure `board_build.partitions = huge_app.csv` is in `platformio.ini`
2. Use quantized (int8) model, not float32
3. Reduce image resolution if needed

## 📝 Model Information

Your Edge Impulse model should have:
- **Input:** 96x96 or 160x160 pixels (RGB)
- **Output:** 9 classes (waste categories)
- **Format:** Quantized (int8) for ESP32
- **Inference time:** < 500ms recommended

## 🔄 Updating Your Model

When you retrain your model:
1. Download the new Arduino library from Edge Impulse
2. Delete the old library folder from `lib/`
3. Install the new library following Step 2
4. Recompile and upload to ESP32

## 📚 Additional Resources

- [Edge Impulse Arduino Library Documentation](https://docs.edgeimpulse.com/docs/deployment/running-your-impulse-arduino)
- [ESP32-CAM with Edge Impulse Tutorial](https://docs.edgeimpulse.com/docs/development-platforms/officially-supported-mcu-targets/espressif-esp32)
- [PlatformIO Library Management](https://docs.platformio.org/en/latest/librarymanager/)

## ✅ Checklist

Before running the system:
- [ ] Edge Impulse library downloaded from your project
- [ ] Library installed in `lib/` directory
- [ ] Code compiles without errors
- [ ] WiFi credentials configured in `include/config.h`
- [ ] Flask backend running
- [ ] ESP32-CAM uploaded and connected

---

**Need Help?** Check the [troubleshooting guide](SETUP.md#troubleshooting) or open an issue on GitHub.
