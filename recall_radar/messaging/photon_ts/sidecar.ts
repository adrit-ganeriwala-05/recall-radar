// Photon Spectrum sidecar (Stable docs): the only TypeScript in F9. Photon's runtime send is SDK-only, so the
// Python service calls this over HTTP on loopback. NOT installed or run until D's Gate P (needs PROJECT_ID,
// PROJECT_SECRET and a provisioned iMessage line). POST /send {space, text, idempotencyKey} → {messageId}.
import { createServer } from "node:http";
import { Spectrum } from "spectrum-ts";
import { imessage } from "spectrum-ts/providers/imessage";

const app = await Spectrum({
  projectId: process.env.PROJECT_ID!,
  projectSecret: process.env.PROJECT_SECRET!,
  providers: [imessage.config()],
});
const im = imessage(app);
const done = new Map<string, string>(); // idempotencyKey → messageId (no duplicate sends after a retry)

createServer(async (req, res) => {
  if (req.method !== "POST" || req.url !== "/send") return void res.writeHead(404).end();
  let raw = "";
  for await (const chunk of req) raw += chunk;
  try {
    const { space: spaceId, text, idempotencyKey } = JSON.parse(raw);
    if (done.has(idempotencyKey)) return void res.writeHead(200).end(JSON.stringify({ messageId: done.get(idempotencyKey) }));
    const space = await im.space.get(spaceId);
    const sent = await space.send(String(text));
    const messageId = String((sent as { id?: string })?.id ?? "");
    done.set(idempotencyKey, messageId);
    res.writeHead(200, { "content-type": "application/json" }).end(JSON.stringify({ messageId }));
  } catch (e) {
    res.writeHead(502, { "content-type": "application/json" }).end(JSON.stringify({ error: String(e).slice(0, 200) }));
  }
}).listen(Number(process.env.SIDECAR_PORT ?? 8790), "127.0.0.1");
