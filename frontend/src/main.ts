// src/main.ts
import { createPinia } from 'pinia'
import { createApp } from 'vue'

import App from './App.vue'
import router from './router'
// EXPLICACIÓN: orden de capas PRIMERO => main.css (base/components) y tailwind.css
// (theme/utilities) comparten jerarquía y utilities gana sin usar '!'
import './styles/layers.css'
import './styles/main.css'
// EXPLICACIÓN: Tailwind global porque AppLayout (sidebar) también consume utilities;
// importarlo solo en una vista dejaría su CSS en el chunk lazy de esa ruta
import './styles/tailwind.css'

// EXPLICACIÓN: pinia ANTES de router => los guards pueden usar los stores
createApp(App).use(createPinia()).use(router).mount('#app')
