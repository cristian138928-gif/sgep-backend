// src/main.ts
import { createPinia } from 'pinia'
import { createApp } from 'vue'

import App from './App.vue'
import router from './router'
import './styles/main.css'

// EXPLICACIÓN: pinia ANTES de router => los guards pueden usar los stores
createApp(App).use(createPinia()).use(router).mount('#app')
