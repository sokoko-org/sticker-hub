<script setup>
import { ArrowLeft } from "lucide-vue-next";
</script>

<template>
  <main class="container not-found">
    <span class="not-found__code">404</span>
    <h1>这张贴纸被撕掉了</h1>
    <p>没有找到对应的平台或表情页面。</p>
    <RouterLink class="btn btn--primary" :to="{ name: 'home' }"><ArrowLeft :size="17" />返回首页</RouterLink>
  </main>
</template>