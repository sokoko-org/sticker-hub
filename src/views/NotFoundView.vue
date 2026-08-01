<script setup>
import { ArrowLeft } from "lucide-vue-next";
</script>

<template>
  <main class="not-found">
    <span>404</span>
    <h1>页面不存在</h1>
    <p>这个链接没有对应的平台或资源页面。</p>
    <RouterLink class="primary-button" :to="{ name: 'home' }"><ArrowLeft :size="17" />返回首页</RouterLink>
  </main>
</template>
