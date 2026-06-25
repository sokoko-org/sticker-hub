const { createApp, ref, onMounted, computed, reactive } = Vue;

document.addEventListener("DOMContentLoaded", () => {
  const appRoot = document.querySelector("#app");
  if (!appRoot) return;

  const platforms = window.EMOJI_PLATFORMS || [];

  const getPlatformFromHash = () => {
    const hash = window.location.hash || "";
    // 无 hash：不从 hash 推导平台/表情
    if (!hash || hash === "#") {
      return { platformId: null, faceId: null };
    }

    // 支持 "#/platform" 或 "#/platform/faceId"
    const match = hash.match(/^#\/([^/?#]+)(?:\/([^/?#]+))?/);
    if (!match) {
      return { platformId: null, faceId: null };
    }
    const platformId = match[1];
    const faceRaw = match[2] || null;
    const exists = platforms.find((p) => p.id === platformId);
    let faceId = null;
    if (faceRaw) {
      try {
        faceId = decodeURIComponent(faceRaw);
      } catch {
        faceId = faceRaw;
      }
    }

    return {
      platformId: exists ? platformId : null,
      faceId,
    };
  };

  let isInternalHashUpdate = false;

  createApp({
    setup() {
      const hashInfo = getPlatformFromHash();
      const currentPlatform = ref(
        hashInfo.platformId || (platforms[0]?.id ?? null),
      );
      const initialFaceId = ref(hashInfo.faceId);
      // 视图模式：hub = 首页卡片视图，preview = 预览视图
      const viewMode = ref(window.location.hash ? "preview" : "hub");

      // 计算当前站的基础 URL，用于拼完整 endpoint
      const { origin, pathname } = window.location;
      // 假设 index.html 在项目根目录或子目录的根，比如 / 或 /tools/emoji-hub/index.html
      // 我们取 pathname 去掉最后一段文件名，得到 basePath
      const basePath = pathname.replace(/\/[^/]*$/, "") || "/";
      const baseUrl = origin + basePath; // 例如 https://example.com 或 https://example.com/tools/emoji-hub

      const searchQuery = ref("");
      const rawData = ref({});
      const loading = ref(true);
      const errorMsg = ref("");
      const preview = reactive({ visible: false, url: "", desc: "", id: "" });

      const toast = reactive({
        visible: false,
        message: "",
      });

      const showToast = (message) => {
        toast.message = message;
        toast.visible = true;
        setTimeout(() => {
          toast.visible = false;
        }, 1600);
      };
      const loadData = async () => {
        if (!currentPlatform.value) return;
        loading.value = true;
        errorMsg.value = "";
        try {
          const dataUrl =
            baseUrl.replace(/\/$/, "") + `/data/${currentPlatform.value}.json`;
          const res = await fetch(dataUrl);
          if (!res.ok) throw new Error(`HTTP ${res.status}`);
          rawData.value = await res.json();
        } catch (err) {
          console.error(err);
          rawData.value = {};
          errorMsg.value = "资源加载失败，请稍后重试或检查网络。";
        }
        loading.value = false;
      };

      const stats = computed(() => {
        const vals = Object.values(rawData.value || {});
        return {
          total: vals.length,
          hasResource: vals.filter((v) => v.url).length,
        };
      });

      const filteredFaces = computed(() => {
        const q = searchQuery.value.toLowerCase().trim();
        if (!q) return rawData.value;
        return Object.fromEntries(
          Object.entries(rawData.value).filter(
            ([id, info]) =>
              id.toLowerCase().includes(q) ||
              (info.desc && info.desc.toLowerCase().includes(q)),
          ),
        );
      });

      // 仅设置预览状态，不操作 hash
      const openPreview = (info, id) => {
        preview.url = encodeURIComponent(info.url || "");
        preview.desc = info.desc;
        preview.id = id;
        preview.visible = true;
      };

      // 点击某个表情卡片：根据当前平台写入 hash，交给 handleHashChange 打开详情
      const goPreviewFace = (id) => {
        if (!currentPlatform.value || !id) return;
        // 表情 id 可能是中文，这里用 encodeURIComponent
        window.location.hash = `#/${currentPlatform.value}/${encodeURIComponent(id)}`;
      };

      const closePreview = () => {
        preview.visible = false;
        if (currentPlatform.value) {
          // 内部更新 hash：#/platform
          isInternalHashUpdate = true;
          window.location.hash = `#/${currentPlatform.value}`;
        }
      };

      const reloadCurrent = () => {
        loadData();
      };

      const copy = (text, type) => {
        if (!text) return;

        let value = text;

        // 如果是 URL 或路径，就自动拼接 baseUrl
        if (typeof text === "string") {
          if (
            /^https?:\/\//i.test(text) || // 完整 http(s)
            text.startsWith("//")
          ) {
            value = text;
          } else if (text.startsWith("/")) {
            // 相对站点根的路径
            value = baseUrl.replace(/\/$/, "") + text;
          }
        }

        const el = document.createElement("textarea");
        el.value = value;
        document.body.appendChild(el);
        el.select();
        document.execCommand("copy");
        document.body.removeChild(el);

        showToast(`${type} 已复制`);
      };

      const switchPlatform = (id) => {
        if (id === currentPlatform.value && viewMode.value === "preview")
          return;
        currentPlatform.value = id;
        searchQuery.value = "";
        preview.visible = false;
        window.location.hash = `#/${id}`;
        viewMode.value = "preview";
        loadData();
      };

      const enterPreview = (id) => {
        // 从首页卡片点击进入预览
        currentPlatform.value = id;
        searchQuery.value = "";
        preview.visible = false;
        window.location.hash = `#/${id}`;
        viewMode.value = "preview";
        window.scrollTo(0, 0);
        loadData();
      };

      const backToHub = () => {
        viewMode.value = "hub";
        window.location.hash = "";
      };

      const currentPlatformInfo = computed(
        () => platforms.find((p) => p.id === currentPlatform.value) || null,
      );

      // 展示用：生成完整 endpoint，并高亮其中所有 {xxx} 占位符
      const formatEndpoint = (endpoint) => {
        if (!endpoint) return "";
        // 如果 endpoint 是以 http(s) 开头就直接用，否则拼到 baseUrl 后面
        const full =
          /^https?:\/\//i.test(endpoint) || endpoint.startsWith("//")
            ? endpoint
            : baseUrl.replace(/\/$/, "") + endpoint;
        return full.replace(/\{[^}]+\}/g, (match) => {
          return `<span class="text-blue-500 font-bold">${match}</span>`;
        });
      };

      const copyApi = (endpoint) => {
        // 复制完整地址模板（保留 {xxx} 占位）
        const full =
          /^https?:\/\//i.test(endpoint) || endpoint.startsWith("//")
            ? endpoint
            : baseUrl.replace(/\/$/, "") + endpoint;
        const el = document.createElement("textarea");
        el.value = full;
        document.body.appendChild(el);
        el.select();
        document.execCommand("copy");
        document.body.removeChild(el);

        showToast("接口格式已复制");
      };

      const handleHashChange = () => {
        if (isInternalHashUpdate) {
          // 本次 hash 变更由内部触发（例如关闭弹窗），不重复处理
          isInternalHashUpdate = false;
          return;
        }

        const info = getPlatformFromHash();

        const { platformId, faceId } = info;

        // hash 清空：回到 Hub，不改当前平台
        if (!platformId) {
          viewMode.value = "hub";
          preview.visible = false;
          return;
        }

        // 平台变化：切平台 + 重新加载，再根据 faceId 打开详情
        if (platformId !== currentPlatform.value) {
          currentPlatform.value = platformId;
          searchQuery.value = "";
          preview.visible = false;
          loadData().then(() => {
            if (faceId && rawData.value[faceId]) {
              openPreview(rawData.value[faceId], faceId);
            } else {
              preview.visible = false;
            }
          });
        } else if (faceId && rawData.value[faceId]) {
          openPreview(rawData.value[faceId], faceId);
        } else {
          preview.visible = false;
        }

        viewMode.value = "preview";
      };

      onMounted(() => {
        window.addEventListener("hashchange", handleHashChange);
        loadData().then(() => {
          // 初始 hash 中如果带了标签 id，加载完数据后自动打开详情
          if (initialFaceId.value && rawData.value[initialFaceId.value]) {
            openPreview(
              rawData.value[initialFaceId.value],
              initialFaceId.value,
            );
            viewMode.value = "preview";
          }
        });
      });

      return {
        // 路由 & 平台
        platforms,
        currentPlatform,
        currentPlatformInfo,
        switchPlatform,
        viewMode,
        enterPreview,
        backToHub,

        // 数据 & 搜索
        searchQuery,
        filteredFaces,
        loading,
        errorMsg,
        stats,
        reloadCurrent,

        // 预览
        preview,
        openPreview,
        closePreview,
        goPreviewFace,

        // 工具
        copy,
        formatEndpoint,
        copyApi,

        // Toast
        toast,
      };
    },
  }).mount("#app");
});
