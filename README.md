Retopology Tool
Author: posthuman
Version: 3.2
Blender Compatibility: 4.3.2

A Blender add-on that automates Quadriflow remeshing with a 0–1 intensity slider, optionally generating multiple LOD levels for game-ready assets, environment props, and quick decimation fallback.

Features
Retopo Intensity Slider
Map a 0–1 value to a rough triangle count (~500 to ~30k).
Quadriflow creates a new topology for each selected mesh based on this approximate goal.
Automatic LOD Generation
Create multiple LOD levels in one click, using preset or custom reduction factors.
Moves each LOD to a dedicated collection and parents them to the original object.
UV Transfer
Optionally copy UVs from the original mesh (or from the previous LOD) to each newly retopologized mesh.
Non-manifold Auto-Fix
Attempts to repair or remove non-manifold edges prior to remeshing.
Fallback Decimation
If Quadriflow overshoots the desired face count or barely reduces the mesh, the add-on automatically applies a Decimate modifier to bring the geometry closer to the target.
Installation
Download/Clone this repository or get the .py file.
In Blender, go to Edit → Preferences → Add-ons → Install...
Select the retopology_tool.py file (or the .zip if you zipped up the repo).
Enable the Retopology Tool add-on in the preferences.
Usage
Select one or more Mesh objects in your scene.
Open View3D → Sidebar (N) → Retopo.
Retopo Intensity (0.0 → ~500 triangles, 1.0 → ~30k triangles).
LOD Levels: Number of LODs to generate (LOD0 is always created).
LOD Preset: Choose “Game,” “Cinema,” or “Custom” for reduction factors.
Transfer UVs: If enabled, the add-on will copy the UV map from the source mesh (LOD0 from the original, and LOD1+ from their respective previous LOD).
Click Process Retopo & LODs. The add-on will:
Duplicate the mesh as MyObject_LOD0
Retopologize it via Quadriflow
Create subsequent LODs with further reductions
Transfer UVs (if requested)
Move new objects into a [MyObject]_LODs collection
Example
Test on a Subdivided Suzanne
Start with the default Monkey mesh, add 3 subdivisions, reaching ~63,000 triangles.
Set Retopo Intensity to 0.70, choose LOD Levels = 3, and LOD Preset = Game.
The tool generated 3 LODs with approximately 2,500, 9,000, and 19,800 triangles respectively, covering a broad range of detail automatically.
Known Limitations
Extremely Dense Meshes

On very high-poly models (200k+ triangles), Quadriflow can fail to reduce effectively or might return a nearly identical result (e.g., 280k → 278k).
In such cases, consider pre-decimating the mesh to a lower poly count (e.g. under ~100k) before running this add-on, or disable preserve_sharp so the remesher can more aggressively simplify.
Approximate Face Count

Quadriflow does not guarantee hitting your target exactly. It may undershoot or overshoot.
The fallback decimate only triggers if the result is well above the target or if it barely reduces the mesh (90% threshold). You can adjust these checks in the script if needed.
UV Distortion

Transferring UVs from a drastically different topology often yields a jumbled layout.
For more precise or aesthetic UV mapping, re-unwrap the retopologized LOD in Blender’s UV Editor.
Not for Rigged Characters

This add-on is great for static meshes, environment props, or scanned assets. For animation-friendly topology, manual retopology or specialized tools (e.g. RetopoFlow) give better control over loops and poles.
Contributing
Issues / Bugs: Please open an issue on GitHub.
Pull Requests: Contributions welcome; if you have improvements for the fallback logic, UI, or performance, please submit a PR.
License
(Example placeholder) Licensed under the GPL (Version 3) to align with Blender’s licensing. See the LICENSE file in this repository for details.

Additional Notes
If you frequently see minimal changes on dense meshes, consider:
Manually decimating large inputs first.
Disabling “Preserve Sharp Edges” for more drastic reductions.
This add-on is a quick auto-retopology solution and not a manual retopo suite. For detailed, animation-ready meshes, a manual or hybrid approach may be best.
With these clarifications, new users will understand the workflow, be aware of pitfalls on high-poly meshes, and see an example usage scenario. You can adapt any part of this documentation as needed before publishing.
