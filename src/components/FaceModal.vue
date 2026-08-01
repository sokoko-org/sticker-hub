<script setup>
import { computed, onBeforeUnmount, onMounted } from "vue";
import { Copy, Link, X } from "lucide-vue-next";
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

function close() {
  router.push({ name: "platform", params: { platformId: props.platformId } });
}

async function copy(text, label) {
  await navigator.clipboard.writeText(text);
  showToast(`${label}已复制`);
}

function onKeydown(event) {
  if (event.key === "Escape") close();
}

onMounted(() => window.addEventListener("keydown", onKeydown));
onBeforeUnmount(() => window.removeEventListener("keydown", onKeydown));
</script>

<template>
  <Teleport to="body">
    <div class="modal-backdrop" @click.self="close">
      <section class="face-modal" role="dialog" aria-modal="true" :aria-label="face.desc || faceId">
        <button class="modal-close icon-button" type="button" title="关闭" aria-label="关闭" @click="close">
          <X :size="19" />
        </button>
        <div class="modal-image">
          <img v-if="face.url" :src="imageUrl" :alt="face.desc || faceId" />
          <span v-else>暂无资源</span>
        </div>
        <div class="modal-copy">
          <code>ID: {{ faceId }}</code>
          <h2>{{ face.desc || "待标注" }}</h2>
        </div>
        <div class="modal-actions">
          <button class="primary-button" type="button" @click="copy(faceId, 'ID')">
            <Copy :size="17" />复制 ID
          </button>
          <button class="secondary-button" type="button" :disabled="!face.url" @click="copy(absolutePublicUrl(face.url), '链接')">
            <Link :size="17" />复制链接
          </button>
        </div>
      </section>
    </div>
  </Teleport>
</template>
