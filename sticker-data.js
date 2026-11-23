import { existsSync, readFileSync, readdirSync } from "node:fs";

const sourceDir = new URL("./api/src/", import.meta.url);
const descriptionsFile = new URL("_descriptions.json", sourceDir);
const PLATFORM_RE = /^[a-z0-9-]+$/;

function generateData(platform) {
  const mapping = JSON.parse(
    readFileSync(new URL(`${platform}.json`, sourceDir), "utf8")
  );
  const descriptions = JSON.parse(readFileSync(descriptionsFile, "utf8"));
  const names = descriptions[platform] ?? {};
  return JSON.stringify(
    Object.fromEntries(
      Object.keys(mapping).map((id) => [
        id,
        {
          desc: Object.prototype.hasOwnProperty.call(names, id) ? names[id] : id,
          url: `/assets/${platform}/${id}`,
        },
      ])
    ),
    null,
    2
  ) + "\n";
}

export function stickerData() {
  return {
    name: "sticker-data",

    generateBundle() {
      for (const filename of readdirSync(sourceDir)) {
        if (!filename.endsWith(".json")) continue;
        const platform = filename.slice(0, -5);
        if (!PLATFORM_RE.test(platform)) continue;
        this.emitFile({
          type: "asset",
          fileName: `data/${filename}`,
          source: generateData(platform),
        });
      }
    },

    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        if (req.method !== "GET" && req.method !== "HEAD") return next();
        const pathname = new URL(req.url, "http://localhost").pathname;
        const match = /^\/data\/([a-z0-9-]+)\.json$/.exec(pathname);
        if (!match || !existsSync(new URL(`${match[1]}.json`, sourceDir))) {
          return next();
        }
        try {
          const data = generateData(match[1]);
          res.setHeader("Content-Type", "application/json; charset=utf-8");
          res.setHeader("Content-Length", Buffer.byteLength(data));
          res.setHeader("Cache-Control", "no-cache");
          res.end(req.method === "HEAD" ? undefined : data);
        } catch (error) {
          next(error);
        }
      });
    },
  };
}
