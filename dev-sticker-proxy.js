import { existsSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { pathToFileURL } from "node:url";

export function stickerProxy() {
  return {
    name: "sticker-proxy",
    apply: (_config, { command }) => command === "serve",

    configureServer(server) {
      server.middlewares.use(
        createMiddleware((id) => server.ssrLoadModule(id), ["public"])
      );
    },

    configurePreviewServer(server) {
      server.middlewares.use(
        createMiddleware(
          (id) => import(pathToFileURL(join(process.cwd(), id)).href),
          ["dist"]
        )
      );
    },
  };
}

/**
 * @param loadHandler 加载 handler 的方式
 * @param staticRoots 静态文件优先时要查的目录
 */
function createMiddleware(loadHandler, staticRoots) {
  const rewrites = JSON.parse(readFileSync("vercel.json", "utf8")).rewrites ?? [];
  const hasAssetRewrite = rewrites.some(
    (r) => r.source === "/assets/:platform/:name"
  );
  const ASSET_RE = /^\/assets\/([^/]+)\/(.+)$/;
  const HANDLER = "/api/_r7k2/[...path].js";

  let handler;
  const load = async () => {
    if (!handler) {
      const mod = await loadHandler(HANDLER);
      handler = mod.default;
    }
    return handler;
  };

  return async (req, res, next) => {
    const url = new URL(req.url, "http://localhost");
    const pathname = decodeURIComponent(url.pathname);

    let parts = null;
    const direct = /^\/api\/_r7k2\/(.+)$/.exec(pathname);
    if (direct) {
      parts = direct[1].split("/");
    } else if (hasAssetRewrite) {
      const m = ASSET_RE.exec(pathname);
      if (m) parts = [m[1], m[2]];
    }
    if (!parts) return next();

    // 静态文件优先于 rewrite
    if (!direct) {
      for (const root of staticRoots) {
        const base = join(process.cwd(), root);
        const file = join(base, pathname);
        if (file.startsWith(base) && existsSync(file) && statSync(file).isFile()) {
          return next();
        }
      }
    }

    try {
      const fn = await load();
      fn(
        {
          method: req.method,
          query: { path: parts, w: url.searchParams.get("w") ?? undefined },
        },
        {
          _code: 200,
          setHeader: (k, v) => res.setHeader(k, v),
          status(code) {
            this._code = code;
            return this;
          },
          end(body) {
            res.statusCode = this._code;
            res.end(body);
            return this;
          },
          json(obj) {
            res.statusCode = this._code;
            res.setHeader("Content-Type", "application/json");
            res.end(JSON.stringify(obj));
            return this;
          },
        }
      );
    } catch (e) {
      res.statusCode = 500;
      res.end(String(e));
    }
  };
}