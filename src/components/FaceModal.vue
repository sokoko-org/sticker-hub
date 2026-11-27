<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { Check, Copy, Hash, Link, X } from "lucide-vue-next";
import { useRouter } from "vue-router";
import { useToast } from "../composables/useToast";
import { absolutePublicUrl, publicUrl } from "../utils/assets";

const props = defineProps({
  face: { type: Object, required: true },
  faceId: { type: String, required: true },
  platformId: { type: String, required: true },
});

const router = useRouter();
const { showToast } = useToast();
const imageUrl = computed(() => publicUrl(props.face.url));
const fullUrl = computed(() => (props.face.url ? absolutePublicUrl(props.face.url) : ""));
const urlCopied = ref(false);

function close() {
  router.push({ name: "platform", params: { platformId: props.platformId } });
}

async function copy(text, label) {
  await navigator.clipboard.writeText(text);
  showToast(`${label}已复制`);
}

async function copyUrl() {
  await copy(fullUrl.value, "链接");
  urlCopied.value = true;
  window.setTimeout(() => (urlCopied.value = false), 1500);
}

function onKeydown(event) {
  if (event.key === "Escape") close();
}

onMounted(() => {
  window.addEventListener("keydown", onKeydown);
  document.documentElement.style.overflow = "hidden";
});
onBeforeUnmount(() => {
  window.removeEventListener("keydown", onKeydown);
  document.documentElement.style.overflow = "";
});
</script>

<template>
  <Teleport to="body">
    <div class="modal-backdrop" @click.self="close">
      <section class="face-modal" role="dialog" aria-modal="true" :aria-label="face.desc || faceId">
        <button class="modal-close icon-btn" type="button" title="关闭 (Esc)" aria-label="关闭" @click="close">
          <X :size="18" />
        </button>
        <div class="modal-image">
          <img v-if="face.url" :src="imageUrl" :alt="face.desc || faceId" decoding="async" fetchpriority="high" />
          <span v-else>暂无资源</span>
        </div>
        <div class="modal-copy">
          <h2>{{ face.desc || "待标注" }}</h2>
          <code>{{ faceId }}</code>
        </div>
        <div v-if="fullUrl" class="endpoint modal-url">
          <code :title="fullUrl">{{ fullUrl.replace(/^https?:\/\//, "") }}</code>
          <button class="icon-btn" :class="{ 'is-done': urlCopied }" type="button" title="复制链接" aria-label="复制链接" @click="copyUrl">
            <Check v-if="urlCopied" :size="16" /><Copy v-else :size="16" />
          </button>
        </div>
        <div class="modal-actions">
          <button class="btn btn--ghost" type="button" @click="copy(faceId, 'ID')"><Hash :size="16" />复制 ID</button>
          <button class="btn btn--primary" type="button" :disabled="!face.url" @click="copyUrl"><Link :size="16" />复制链接</button>
        </div>
      </section>
    </div>
  </Teleport>
</template>