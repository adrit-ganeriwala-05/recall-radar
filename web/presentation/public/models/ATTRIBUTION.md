# Illustrative vehicle model — provenance and licence

File: `car-concept-pearl.glb` · 2480072 bytes · sha256 `54c0ca341781db9a7765870df6d36057649d514c936c16b74b3ff315dc073b2c`

## Source
- Asset: "Car Concept", Khronos glTF Sample Assets —
  https://github.com/KhronosGroup/glTF-Sample-Assets/tree/main/Models/CarConcept
  (`glTF-WEBP` edition, repository commit `7d4ba189827916452eeadc82d4b712dbc6280a6f`).
- Author: Eric Chadwick. Owner: Darmstadt Graphics Group GmbH (2024).
- Licence (model and textures): Creative Commons Attribution 4.0 International (CC BY 4.0),
  https://creativecommons.org/licenses/by/4.0/legalcode. The upstream licence **excludes the Khronos
  and 3D Commerce logos and trademarks**, so they are removed here (below).

## Changes made (CC BY 4.0 §3(a)(1)(B): indicate modifications)
1. Removed the "License Plate" node and mesh.
2. Removed every use of the Khronos logo texture (`Khronos_C.webp`): emissive texture and emissive
   colour cleared on the materials that used it; the image itself is no longer in the file (asserted
   by the build script).
3. Baked the "Pearly Swirly" material variant into the meshes and removed `KHR_materials_variants`
   and the unused paint/interior variant materials.
4. Pruned unused data, deduplicated, welded, quantized and meshopt-compressed the geometry
   (`EXT_meshopt_compression`, decoded by three.js's bundled decoder).
5. Simplified the geometry with meshoptimizer (target ratio 0.5, error bound 0.05% of the mesh
   extent): 213,313 → 123,118 triangles; bounds unchanged.
6. Resized two textures: the baked occlusion map 2048² → 1024² and the tyre-sidewall normal map
   1024² → 512² (WebP).
7. At render time (not in the file): the two body paints ("Paint 1 Pearl", "Paint 2 Pearl") are set to
   a pearl-silver colour with clearcoat and without iridescence (`src/scene/VehicleModel.tsx`); on
   low-quality devices the transmission glass is replaced by tinted transparency.

Rebuilt by `web/presentation/tools/process-car-model.mjs` (glTF-Transform 4.x + meshoptimizer, run
from a separate tools folder: `node process-car-model.mjs <CarConcept.gltf> <out.glb>`).

## Use in Recall Radar
Shown only as a generic "Illustrative vehicle" in the presentation. It does not represent any make,
model or model year, carries no fault indications, and no endorsement by the author, the owner or the
Khronos Group is implied. The on-page credit is in the presentation footer.
