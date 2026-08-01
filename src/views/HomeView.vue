<script setup>
import { ArrowRight, Copy } from "lucide-vue-next";
import { platforms } from "../config/platforms";
import { useToast } from "../composables/useToast";
import { absolutePublicUrl } from "../utils/assets";

const { showToast } = useToast();

function endpointUrl(endpoint) {
  return absolutePublicUrl(endpoint)
    .replace(/%7B/gi, "{")
    .replace(/%7D/gi, "}");
}

async function copyEndpoint(endpoint) {
  await navigator.clipboard.writeText(endpointUrl(endpoint));
  showToast("接口格式已复制");
}

function endpointParts(endpoint) {
  return endpointUrl(endpoint).split(/(\{[^}]+\})/g);
}
</script>

<template>
  <main>
    <header class="hero">
      <span class="eyebrow">Unified Emoji Assets</span>
      <h1>表情资源 <strong>托管中心</strong></h1>
      <p>每个平台提供独立的 API 节点。在线检索、预览资源，或直接调用静态资源接口。</p>
    </header>

    <section class="platform-grid" aria-label="平台列表">
      <article v-for="platform in platforms" :key="platform.id" class="platform-card" :data-tone="platform.tone">
        <div class="platform-card__top">
          <span class="platform-icon" aria-hidden="true">{{ platform.icon }}</span>
          <RouterLink class="enter-link" :to="{ name: 'platform', params: { platformId: platform.id } }">
            进入预览
            <ArrowRight :size="17" :stroke-width="2.5" />
          </RouterLink>
        </div>
        <h2>{{ platform.name }}</h2>
        <p>{{ platform.desc }}</p>
        <div class="endpoint-label">Endpoint</div>
        <div class="endpoint-box">
          <code>
            <template v-for="(part, index) in endpointParts(platform.endpoint)" :key="index">
              <mark v-if="part.startsWith('{')">{{ part }}</mark>
              <template v-else>{{ part }}</template>
            </template>
          </code>
          <button class="icon-button" type="button" title="复制接口地址" aria-label="复制接口地址" @click="copyEndpoint(platform.endpoint)">
            <Copy :size="17" />
          </button>
        </div>
      </article>
    </section>
  </main>
</template>
