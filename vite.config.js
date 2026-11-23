import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

import { stickerProxy } from "./dev-sticker-proxy.js";
// 本地调试模拟 vercel 环境
export default defineConfig({
  plugins: [vue(), stickerProxy()],
});
