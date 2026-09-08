<script setup lang="ts">
import { RouterLink, RouterView } from "vue-router";
</script>

<template>
  <header class="nav">
    <strong>SanctionsGraph</strong>
    <nav>
      <RouterLink to="/">New Screening</RouterLink>
      <RouterLink to="/cases">Cases</RouterLink>
    </nav>
  </header>

  <main>
    <RouterView />
  </main>
</template>

<style scoped>
.nav {
  display: flex;
  align-items: center;
  gap: 2rem;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #ddd;
}
nav {
  display: flex;
  gap: 1rem;
}
main {
  padding: 1rem;
}
</style>
