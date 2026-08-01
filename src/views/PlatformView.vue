<script setup>
import { computed, ref, watch } from "vue";
import { ArrowLeft, RefreshCw, Search } from "lucide-vue-next";
import { useRouter } from "vue-router";
import FaceModal from "../components/FaceModal.vue";
import { findPlatform, platforms } from "../config/platforms";
import { publicUrl } from "../utils/assets";

const props = defineProps({
  platformId: { type: String, required: true },
  faceId: { type: String, default: "" },
});

const router = useRouter();
const searchQuery = ref("");
const faces = ref({});
const loading = ref(false);
const errorMessage = ref("");
const cache = new Map();

const platform = computed(() => findPlatform(props.platformId));
const entries = computed(() => {
  const query = searchQuery.value.toLocaleLowerCase().trim();
  return Object.entries(faces.value).filter(([id, face]) => {
    if (!query) return true;
    return id.toLocaleLowerCase().includes(query) || face.desc?.toLocaleLowerCase().includes(query);
  });
});
const resourceCount = computed(() => Object.values(faces.value).filter((face) => face.url).length);
const selectedFace = computed(() => (props.faceId ? faces.value[props.faceId] : null));

async function loadFaces(force = false) {
  if (!platform.value) {
    router.replace({ name: "not-found" });
    return;
  }
  searchQuery.value = "";
  errorMessage.value = "";
  if (!force && cache.has(props.platformId)) {
    faces.value = cache.get(props.platformId);
    return;
  }
  loading.value = true;
  try {
    const response = await fetch(publicUrl(`/data/${props.platformId}.json`));
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    cache.set(props.platformId, data);
    faces.value = data;
  } catch (error) {
    console.error(error);
    faces.value = {};
    errorMessage.value = "资源加载失败，请稍后重试。";
  } finally {
    loading.value = false;
  }
}

function openFace(id) {
  router.push({ name: "platform", params: { platformId: props.platformId, faceId: id } });
}

watch(() => props.platformId, () => loadFaces(), { immediate: true });
</script>

<template>
  <main v-if="platform" class="preview-page">
    <header class="preview-header">
      <div class="preview-title">
        <RouterLink class="back-link" :to="{ name: 'home' }"><ArrowLeft :size="16" />返回首页</RouterLink>
        <h1>{{ platform.name }}</h1>
      </div>
      <label class="search-box">
        <Search :size="18" />
        <input v-model="searchQuery" type="search" placeholder="搜索 ID 或描述" aria-label="搜索表情" />
      </label>
    </header>

    <nav class="platform-tabs" aria-label="切换平台">
      <RouterLink v-for="item in platforms" :key="item.id" :to="{ name: 'platform', params: { platformId: item.id } }">
        {{ item.name }}
      </RouterLink>
    </nav>

    <section v-if="!loading && !errorMessage" class="stats" aria-label="资源统计">
      <div><span>Total</span><strong>{{ Object.keys(faces).length }}</strong></div>
      <div><span>Resources</span><strong>{{ resourceCount }}</strong></div>
    </section>

    <section v-if="loading" class="face-grid" aria-label="正在加载">
      <div v-for="item in 15" :key="item" class="face-card skeleton"><div></div><span></span></div>
    </section>

    <section v-else-if="errorMessage" class="empty-state">
      <p>{{ errorMessage }}</p>
      <button class="secondary-button" type="button" @click="loadFaces(true)"><RefreshCw :size="17" />重新加载</button>
    </section>

    <section v-else-if="entries.length" class="face-grid" aria-label="表情列表">
      <button v-for="([id, face]) in entries" :key="id" class="face-card" type="button" @click="openFace(id)">
        <span class="face-image">
          <img v-if="face.url" :src="publicUrl(face.url)" :alt="face.desc || id" loading="lazy" />
          <small v-else>暂无资源</small>
          <code>#{{ id }}</code>
        </span>
        <strong>{{ face.desc || "待标注" }}</strong>
      </button>
    </section>

    <section v-else class="empty-state"><p>没有找到匹配的表情。</p></section>

    <FaceModal v-if="selectedFace" :face="selectedFace" :face-id="faceId" :platform-id="platformId" />
  </main>
</template>
