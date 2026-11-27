<script setup>
import { onBeforeUnmount, onMounted, ref } from "vue";
import { RouterView } from "vue-router";
import { CheckCircle2, Github } from "lucide-vue-next";
import { useToast } from "./composables/useToast";
import { publicUrl } from "./utils/assets";

const { message } = useToast();
const scrolled = ref(false);
const onScroll = () => (scrolled.value = window.scrollY > 8);
onMounted(() => window.addEventListener("scroll", onScroll, { passive: true }));
onBeforeUnmount(() => window.removeEventListener("scroll", onScroll));
</script>

<template>
  <header class="topbar" :class="{ 'is-scrolled': scrolled }">
    <div class="container topbar__inner">
      <RouterLink class="brand" :to="{ name: 'home' }">
        <img :src="publicUrl('/favicon.svg')" alt="" width="30" height="30" />
        Sticker Hub
      </RouterLink>
      <nav aria-label="主导航">
        <RouterLink class="nav-link" :to="{ name: 'home', hash: '#platforms' }">平台</RouterLink>
        <a class="nav-link" href="https://github.com/sokoko-org/sticker-hub" target="_blank" rel="noreferrer">
          <Github :size="17" /><span>GitHub</span>
        </a>
      </nav>
    </div>
  </header>

  <RouterView />

  <footer class="site-footer">
    <div class="container">
      <span>© 2026 Sticker Hub · 表情资源托管</span>
      <nav aria-label="页脚导航">
        <a href="mailto:contact@sokoko.org">联系我们</a>
        <a href="https://github.com/sokoko-org/sticker-hub" target="_blank" rel="noreferrer">GitHub</a>
      </nav>
    </div>
  </footer>

  <Transition name="toast">
    <div v-if="message" class="toast" role="status">
      <CheckCircle2 :size="17" />
      {{ message }}
    </div>
  </Transition>
</template>