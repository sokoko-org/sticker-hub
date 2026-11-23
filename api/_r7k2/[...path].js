import { readFileSync } from "node:fs";

import registry from "../src/_registry.json" with { type: "json" };

const maps = new Map();
function loadMap(platform) {
  if (!maps.has(platform)) {
    let data = null;
    try {
      const file = new URL(`../src/${platform}.json`, import.meta.url);
      data = JSON.parse(readFileSync(file, "utf8"));
    } catch {
      data = null;
    }
    maps.set(platform, data);
  }
  return maps.get(platform);
}

const TRANSFORMS = {
  netease: ({ ext, width, options }) => {
    const w = width ?? options.defaultWidth ?? 200;
    return `?fop=imageView/2/w/${w}/f/${ext}`;
  },
};

const EXT_RE = /\.(webp|png|gif|jpe?g)$/i;
const MAX_WIDTH = 512;

export const config = { runtime: "nodejs" };

export default function handler(req, res) {
  if (req.method !== "GET" && req.method !== "HEAD") {
    res.setHeader("Allow", "GET, HEAD");
    return res.status(405).end("Method Not Allowed");
  }

  const parts = []
    .concat(req.query.path ?? [])
    .flatMap((v) => String(v).split("/"))
    .filter(Boolean)
    .map(decodeURIComponent);
  const platform = parts.shift();
  const rest = parts.join("/");

  const conf =
    platform && Object.prototype.hasOwnProperty.call(registry, platform)
      ? registry[platform]
      : null;
  if (!conf || conf.enabled !== true) {
    res.setHeader("Cache-Control", "public, max-age=300");
    return res.status(404).json({ error: "unknown platform", platform });
  }

  const matched = rest.match(EXT_RE);
  const ext = matched ? matched[1].toLowerCase() : null;
  const key = matched ? rest.slice(0, -matched[0].length) : rest;

  const map = loadMap(platform);
  const base =
    map && Object.prototype.hasOwnProperty.call(map, key) ? map[key] : null;
  if (!base) {
    res.setHeader("Cache-Control", "public, max-age=300");
    return res.status(404).json({ error: "unknown sticker", platform, key });
  }

  const rawWidth = Number.parseInt(req.query.w, 10);
  const width =
    Number.isFinite(rawWidth) && rawWidth > 0
      ? Math.min(rawWidth, MAX_WIDTH)
      : null;
  const transform = TRANSFORMS[conf.transform];
  const src =
    base + (transform?.({ ext, width, options: conf.options ?? {} }) ?? "");

  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader(
    "Cache-Control",
    "public, max-age=604800, s-maxage=31536000, stale-while-revalidate=86400",
  );
  res.setHeader("Referrer-Policy", "no-referrer");

  const match = src.match(
    /^data:(image\/(?:png|jpeg|gif|webp));base64,([\s\S]+)$/
  );
  if (match) {
    const image = Buffer.from(match[2], "base64");
    res.setHeader("Content-Type", match[1]);
    res.setHeader("Content-Length", image.length);
    return res.status(200).end(req.method === "HEAD" ? undefined : image);
  }

  res.setHeader("Location", src);
  return res.status(302).end();
}
