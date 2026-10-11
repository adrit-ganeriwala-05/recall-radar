// Owner: C. Best-effort software-WebGL detection from the renderer string (browser only). Chrome and
// Safari mask gl.RENDERER ("WebKit WebGL") and expose the real name through WEBGL_debug_renderer_info;
// Firefox reports a sanitized real name in gl.RENDERER and warns when the extension is requested, so
// the extension is asked for only when the plain value is masked. An unrecognised name counts as
// hardware: the only cost of a miss is the pre-Phase-4 behaviour (choreography on).
const SOFTWARE = /swiftshader|llvmpipe|softpipe|software|basic render|\bwarp\b/i;

export function rendererName(gl: WebGLRenderingContext | WebGL2RenderingContext): string {
  const plain = String(gl.getParameter(gl.RENDERER) ?? "");
  if (!/webkit webgl/i.test(plain)) return plain;
  const ext = gl.getExtension("WEBGL_debug_renderer_info");
  return ext ? String(gl.getParameter(ext.UNMASKED_RENDERER_WEBGL) ?? plain) : plain;
}

export function isSoftwareRenderer(name: string): boolean {
  return SOFTWARE.test(name);
}
