<script setup>
import { ArrowDown, ArrowUpRight, Copy, Github } from "lucide-vue-next";
import { platformLogo, platforms } from "../config/platforms";
import { useToast } from "../composables/useToast";
import { absolutePublicUrl, publicUrl } from "../utils/assets";

const { showToast } = useToast();

// 首屏贴纸墙：直接用平台 logo，静态资源，无需外链
const heroStickers = ["tieba", "bilibili", "rednote", "douyin", "weibo", "zhihu", "kuaishou", "miyoushe"];

function endpointUrl(endpoint) {
  return absolutePublicUrl(endpoint).replace(/%7B/gi, "{").replace(/%7D/gi, "}");
}

function endpointParts(endpoint) {
  return endpointUrl(endpoint)
    .replace(window.location.origin, "")
    .split(/(\{[^}]+\})/g);
}

async function copyEndpoint(endpoint) {
  await navigator.clipboard.writeText(endpointUrl(endpoint));
  showToast("接口地址已复制");
}
</script>

<template>
  <main class="container">
    <section class="hero">
      <div>
        <p class="kicker"><i></i>{{ platforms.length }} 个平台 · 持续更新</p>
        <h1>各大平台的表情包，<br />一个 <em>链接</em> 就够了</h1>
        <p class="lead">贴吧、小红书、抖音、B 站……统一的 URL 规则，在线搜索预览，复制即用，直接引用到你的项目里。</p>
        <div class="hero__actions">
          <a class="btn btn--primary" href="#platforms">浏览平台<ArrowDown :size="17" /></a>
          <a class="btn btn--ghost" href="https://github.com/sokoko-org/sticker-hub" target="_blank" rel="noreferrer">
            <Github :size="17" />GitHub
          </a>
        </div>
      </div>
      <div class="hero__art" aria-hidden="true">
        <img
          v-for="(id, i) in heroStickers"
          :key="id"
          class="sticker"
          :style="{ '--i': i }"
          :src="publicUrl(`/assets/logo/${id}.webp`)"
          alt=""
          decoding="async"
        />
      </div>
    </section>

    <section id="platforms" aria-labelledby="platforms-title">
      <div class="section-head">
        <h2 id="platforms-title">选择平台</h2>
        <p>点击卡片预览全部表情，<code>{id}</code> 替换为表情 ID 即可调用</p>
      </div>
      <div class="platform-grid">
        <article v-for="platform in platforms" :key="platform.id" class="platform-card">
          <div class="platform-card__head">
            <img class="platform-logo" :src="publicUrl(platformLogo(platform))" alt="" loading="lazy" decoding="async" />
            <div class="platform-card__title">
              <h3>
                <RouterLink :to="{ name: 'platform', params: { platformId: platform.id } }">{{ platform.name }}</RouterLink>
              </h3>
              <p>{{ platform.desc }}</p>
            </div>
            <ArrowUpRight class="platform-card__arrow" :size="20" />
          </div>
          <div class="endpoint">
            <code :title="endpointUrl(platform.endpoint)">
              <template v-for="(part, index) in endpointParts(platform.endpoint)" :key="index">
                <b v-if="part.startsWith('{')">{{ part }}</b>
                <template v-else>{{ part }}</template>
              </template>
            </code>
            <button class="icon-btn" type="button" title="复制接口地址" aria-label="复制接口地址" @click="copyEndpoint(platform.endpoint)">
              <Copy :size="16" />
            </button>
          </div>
        </article>
      </div>
    </section>
  </main>
</template>