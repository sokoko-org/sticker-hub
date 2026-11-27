<script setup>
import { computed, onBeforeUnmount, ref, watch } from "vue";
import { ArrowLeft, RefreshCw, Search, X } from "lucide-vue-next";
import { useRouter } from "vue-router";
import FaceModal from "../components/FaceModal.vue";
import { findPlatform, platformLogo, platforms } from "../config/platforms";
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
let activeRequest;

const platform = computed(() => findPlatform(props.platformId));
const entries = computed(() => {
  const query = searchQuery.value.toLocaleLowerCase().trim();
  return Object.entries(faces.value).filter(([id, face]) => {
    if (!query) return true;
    return id.toLocaleLowerCase().includes(query) || face.desc?.toLocaleLowerCase().includes(query);
  });
});
const resourceCount = computed(() => Object.values(faces.value).filter((face) => face.url).length);

function hasFace(id) {
  return Boolean(id) && Object.prototype.hasOwnProperty.call(faces.value, id);
}

const selectedFace = computed(() => (hasFace(props.faceId) ? faces.value[props.faceId] : null));

function redirectIfMissingFace() {
  if (props.faceId && !hasFace(props.faceId)) router.replace({ name: "not-found" });
}

async function loadFaces(force = false) {
  activeRequest?.abort();
  activeRequest = undefined;
  const platformId = props.platformId;

  faces.value = {};
  if (!platform.value) {
    loading.value = false;
    router.replace({ name: "not-found" });
    return;
  }
  searchQuery.value = "";
  errorMessage.value = "";
  if (!force && cache.has(platformId)) {
    faces.value = cache.get(platformId);
    loading.value = false;
    redirectIfMissingFace();
    return;
  }

  const controller = new AbortController();
  activeRequest = controller;
  loading.value = true;
  try {
    const response = await fetch(publicUrl(`/data/${platformId}.json`), {
      priority: "high",
      signal: controller.signal,
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    if (controller.signal.aborted || activeRequest !== controller) return;
    cache.set(platformId, data);
    faces.value = data;
    redirectIfMissingFace();
  } catch (error) {
    if (controller.signal.aborted || activeRequest !== controller) return;
    console.error(error);
    faces.value = {};
    errorMessage.value = "资源加载失败，请稍后重试。";
  } finally {
    if (activeRequest === controller) {
      activeRequest = undefined;
      loading.value = false;
    }
  }
}

function openFace(id) {
  router.push({ name: "platform", params: { platformId: props.platformId, faceId: id } });
}

watch(() => props.platformId, () => loadFaces(), { immediate: true });
watch(() => props.faceId, () => {
  if (!loading.value && !errorMessage.value) redirectIfMissingFace();
});
onBeforeUnmount(() => {
  activeRequest?.abort();
  activeRequest = undefined;
});
</script>

<template>
  <main v-if="platform" class="container">
    <RouterLink class="back-link" :to="{ name: 'home', hash: '#platforms' }"><ArrowLeft :size="16" />全部平台</RouterLink>
    <header class="page-head">
      <div class="page-title">
        <img class="platform-logo" :src="publicUrl(platformLogo(platform))" alt="" />
        <div>
          <h1>{{ platform.name }}</h1>
          <p v-if="loading">正在加载…</p>
          <p v-else-if="!errorMessage">
            共 <b>{{ Object.keys(faces).length }}</b> 个表情<template v-if="searchQuery.trim()">，匹配 <b>{{ entries.length }}</b> 个</template>
          </p>
        </div>
      </div>
      <label class="search-box">
        <Search :size="18" />
        <input v-model="searchQuery" type="search" placeholder="搜索 ID 或描述" aria-label="搜索表情" />
        <button v-if="searchQuery" class="icon-btn" type="button" aria-label="清空搜索" style="width: 28px; height: 28px" @click="searchQuery = ''">
          <X :size="15" />
        </button>
      </label>
    </header>

    <div class="chip-bar">
      <nav class="chips" aria-label="切换平台">
        <RouterLink v-for="item in platforms" :key="item.id" class="chip" :to="{ name: 'platform', params: { platformId: item.id } }">
          <img :src="publicUrl(platformLogo(item))" alt="" loading="lazy" decoding="async" />{{ item.name }}
        </RouterLink>
      </nav>
    </div>

    <section v-if="loading" class="face-grid" aria-label="正在加载">
      <div v-for="item in 18" :key="item" class="face-card skeleton"><div class="face-image"></div><div class="face-meta"><span></span></div></div>
    </section>

    <section v-else-if="errorMessage" class="empty-state">
      <span class="big">😵</span>
      <p>{{ errorMessage }}</p>
      <button class="btn btn--ghost" type="button" @click="loadFaces(true)"><RefreshCw :size="16" />重新加载</button>
    </section>

    <section v-else-if="entries.length" class="face-grid" aria-label="表情列表">
      <button v-for="([id, face]) in entries" :key="id" class="face-card" type="button" :title="face.desc || id" @click="openFace(id)">
        <span class="face-image">
          <img v-if="face.url" :src="publicUrl(face.url)" :alt="face.desc || id" loading="lazy" decoding="async" fetchpriority="low" />
          <small v-else>暂无资源</small>
        </span>
        <span class="face-meta">
          <strong>{{ face.desc || "待标注" }}</strong>
          <code>{{ id }}</code>
        </span>
      </button>
    </section>

    <section v-else class="empty-state">
      <span class="big">🫥</span>
      <p>没有找到「{{ searchQuery.trim() }}」相关的表情</p>
      <button class="btn btn--ghost" type="button" @click="searchQuery = ''">清空搜索</button>
    </section>

    <FaceModal v-if="selectedFace" :face="selectedFace" :face-id="faceId" :platform-id="platformId" />
  </main>
</template>