import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

import { stickerProxy } from "./dev-sticker-proxy.js";
import { stickerData } from "./sticker-data.js";
// 本地调试模拟 vercel 环境
export default defineConfig({
  plugins: [vue(), stickerData(), stickerProxy()],
});
