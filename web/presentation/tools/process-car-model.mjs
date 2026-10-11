// Asset build step for the presentation (run by hand; not part of npm run build): Khronos "Car Concept" (CC-BY-4.0) ->
// web/presentation/public/models/car-concept-pearl.glb
//  1. remove the License Plate node/mesh and every use of the Khronos logo texture (the CC-BY grant
//     excludes logos and trademarks), then assert no image named Khronos remains;
//  2. bake the "Pearly Swirly" KHR_materials_variants choice into the primitives, drop the variants;
//  3. prune, dedup, quantize + meshopt-compress geometry (decoded by three's bundled MeshoptDecoder).
// Usage (from a folder with @gltf-transform/core|extensions|functions@4 and meshoptimizer installed;
// not a dependency of this app): node process-car-model.mjs <CarConcept.gltf> <out.glb>
import { NodeIO } from "@gltf-transform/core";
import { ALL_EXTENSIONS, EXTMeshoptCompression, KHRMaterialsVariants } from "@gltf-transform/extensions";
import { dedup, meshopt, prune, weld } from "@gltf-transform/functions";
import { MeshoptDecoder, MeshoptEncoder } from "meshoptimizer";

const [input, output] = process.argv.slice(2);
await MeshoptDecoder.ready;
await MeshoptEncoder.ready;
const io = new NodeIO()
  .registerExtensions(ALL_EXTENSIONS)
  .registerDependencies({ "meshopt.decoder": MeshoptDecoder, "meshopt.encoder": MeshoptEncoder });
const doc = await io.read(input);
const root = doc.getRoot();
const log = (...a) => console.log(...a);

// 1. logos
const logoTextures = root.listTextures().filter((t) => /khronos/i.test(t.getURI() || t.getName()));
if (logoTextures.length !== 1) throw new Error(`expected exactly one Khronos texture, found ${logoTextures.length}`);
const logo = logoTextures[0];
for (const node of root.listNodes()) {
  if (node.getName() === "License Plate") {
    const mesh = node.getMesh();
    node.dispose();
    mesh?.dispose();
    log("removed node+mesh: License Plate");
  }
}
for (const mat of root.listMaterials()) {
  if (mat.getEmissiveTexture() === logo) {
    mat.setEmissiveTexture(null);
    mat.setEmissiveFactor([0, 0, 0]);
    log(`stripped logo emission: material "${mat.getName()}"`);
  }
  if (mat.getBaseColorTexture() === logo) {
    mat.setBaseColorTexture(null);
    log(`stripped logo base color: material "${mat.getName()}"`);
  }
}

// 2. bake the Pearly Swirly variant
const variantsExt = root.listExtensionsUsed().find((e) => e.extensionName === KHRMaterialsVariants.EXTENSION_NAME);
if (!variantsExt) throw new Error("KHR_materials_variants not present");
let baked = 0;
for (const mesh of root.listMeshes()) {
  for (const prim of mesh.listPrimitives()) {
    const mappingList = prim.getExtension(KHRMaterialsVariants.EXTENSION_NAME);
    if (!mappingList) continue;
    for (const mapping of mappingList.listMappings()) {
      if (mapping.listVariants().some((v) => v.getName() === "Pearly Swirly")) {
        prim.setMaterial(mapping.getMaterial());
        baked++;
      }
    }
    prim.setExtension(KHRMaterialsVariants.EXTENSION_NAME, null);
  }
}
variantsExt.dispose();
log(`baked Pearly Swirly on ${baked} primitives; variants extension removed`);

// 3. clean + compress
await doc.transform(prune(), dedup(), weld());
const remaining = root.listTextures().map((t) => t.getURI() || t.getName());
if (remaining.some((n) => /khronos/i.test(n))) throw new Error(`logo texture still present: ${remaining}`);
log("textures kept:", remaining.join(", "));
log("materials kept:", root.listMaterials().map((m) => m.getName()).join(", "));
doc.createExtension(EXTMeshoptCompression).setRequired(true);
await doc.transform(meshopt({ encoder: MeshoptEncoder, level: "medium" }));
await io.write(output, doc);
log("wrote", output);
