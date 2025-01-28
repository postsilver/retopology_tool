# Retopology Tool

**Author:** posthuman  
**Version:** 3.2  
**Blender Compatibility:** 4.3.2  

**Retopology Tool** is a Blender add-on that automates **Quadriflow remeshing** with a **0–1 intensity slider**, allowing users to generate multiple **LOD (Level of Detail) levels** for game-ready assets, environment props, and quick decimation fallback.

---

## ✨ Features

### 🛠️ **Retopo Intensity Slider**
- Map a **0–1 value** to a rough triangle count (**~500 to ~30k**).
- Quadriflow generates a new topology based on this approximate goal.

### 🔥 **Automatic LOD Generation**
- Generate multiple **LOD levels** in one click using preset or custom reduction factors.
- Moves each **LOD** to a dedicated collection and parents them to the original object.

### 🎨 **UV Transfer**
- Optionally **copy UVs** from the original mesh (or from the previous LOD) to the new retopologized mesh.

### ⚡ **Non-manifold Auto-Fix**
- Attempts to **repair or remove non-manifold edges** before remeshing.

### ⚙️ **Fallback Decimation**
- If Quadriflow **overshoots the desired face count** or **barely reduces** the mesh, the add-on applies a **Decimate** modifier to adjust the poly count.

---

## 📥 Installation

1. **Download/Clone** this repository or get the `.py` file.
2. Open **Blender** and go to **Edit → Preferences → Add-ons → Install...**.
3. Select the `retopology_tool.py` file (or a `.zip` if you zipped up the repo).
4. Enable the **Retopology Tool** add-on in the **Add-ons** tab.

---

## 🚀 Usage

1. **Select** one or more **Mesh** objects in your scene.
2. Open **View3D → Sidebar (N) → Retopo**.
3. Adjust the **Retopo Intensity** slider (**0.0 → ~500 tris, 1.0 → ~30k tris**).
4. Choose the number of **LOD Levels** (LOD0 is always created).
5. Select a **LOD Preset**:  
   - **Game:** (50%, 30%, 15%, 10%, 5%)  
   - **Cinema:** (80%, 60%, 40%, 25%, 15%)  
   - **Custom:** Manually set reduction factors.  
6. Enable **Transfer UVs** (optional) to copy the UV map from the source mesh.
7. Click **Process Retopo & LODs** to generate optimized meshes.

The add-on will:
- Duplicate the mesh as **`MyObject_LOD0`**.
- Retopologize it using **Quadriflow**.
- Generate **additional LODs** with progressive reduction.
- Transfer **UVs** (if requested).
- Move new objects into a **`[MyObject]_LODs`** collection.

---

## 📌 Example: Subdivided Suzanne

1. Add a **Monkey Head** and apply **3 Subdivision Surface** modifiers (resulting in **~63,000 triangles**).
2. Set **Retopo Intensity** to **0.70**, choose **LOD Levels = 3**, and **LOD Preset = Game**.
3. The tool generates **3 LODs** with approximate triangle counts:
   - **LOD2:** ~19,800 tris  
   - **LOD1:** ~9,000 tris  
   - **LOD0:** ~2,500 tris  

✅ This method works well for **game assets** and **environment props**.

---

## ⚠️ Known Limitations

### 🟠 **Extremely Dense Meshes**
- On **very high-poly models** (**200k+ triangles**), Quadriflow may fail to significantly reduce topology (e.g., **280k → 278k** tris).
- Workarounds:
  - **Pre-decimate** the mesh manually (**reduce to <100k** tris before retopology).
  - Disable **Preserve Sharp Edges** to allow a more aggressive simplification.

### 🟡 **Approximate Face Count**
- Quadriflow does **not guarantee** exact triangle counts.
- The fallback **Decimate Modifier** only applies if:
  - The **result is much higher than expected**.
  - The **mesh barely changes** (less than **10% reduction**).

### 🔵 **UV Distortion**
- Transferring UVs from a **high-poly** to a **newly retopologized** mesh may **scramble the UV layout**.
- Workarounds:
  - **Re-unwrap the LOD manually** in Blender's **UV Editor** for better results.

### 🔴 **Not Recommended for Rigged Characters**
- This add-on is designed for **static meshes**, **environment props**, and **scanned assets**.
- For animation-friendly retopology, consider **manual workflows** or specialized tools like **RetopoFlow**.

---

## 🤝 Contributing

🔹 **Issues / Bugs:** Please open an issue on GitHub.  
🔹 **Pull Requests:** Contributions are welcome! If you have improvements for the **fallback logic, UI, or performance**, feel free to submit a PR.  

---

## 📜 License

📄 **GPL v3** – This add-on is licensed under the **GNU General Public License v3.0** to align with Blender’s open-source licensing.

See the full **LICENSE** file in this repository for details.

---

## 📝 Additional Notes

💡 If you see **minimal changes** on very dense meshes, consider:
- **Manually decimating** the model first.
- **Disabling "Preserve Sharp Edges"** for better reduction.

🎯 **This tool is a quick auto-retopology solution, not a manual retopo suite.**  
For **animation-ready** models, use a **manual** or **hybrid** approach.

---
