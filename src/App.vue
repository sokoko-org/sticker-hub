<script setup>
import { RouterView } from "vue-router";
import { CheckCircle2 } from "lucide-vue-next";
import { useToast } from "./composables/useToast";

const { message } = useToast();
</script>

<template>
  <div class="site-shell">
    <RouterView />

    <footer class="site-footer">
      <span>© 2026 STICKER-HUB SERVICE</span>
      <nav aria-label="页脚导航">
        <a href="mailto:contact@sokoko.org">Contact</a>
        <a href="https://github.com/sokoko-org/sticker-hub" target="_blank" rel="noreferrer">GitHub</a>
      </nav>
    </footer>
  </div>

  <Transition name="toast">
    <div v-if="message" class="toast" role="status">
      <CheckCircle2 :size="16" />
      {{ message }}
    </div>
  </Transition>
</template>
