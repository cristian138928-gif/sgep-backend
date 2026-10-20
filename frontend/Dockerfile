# EXPLICACIÓN: multi-stage => node solo en build, nginx sirve estáticos en runtime
FROM node:22-alpine AS build

WORKDIR /app

# EXPLICACIÓN: package-lock primero => capa de caché si no cambian deps
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# EXPLICACIÓN: build con typecheck (vue-tsc) incluido en el script
RUN npm run build

FROM nginx:1.27-alpine

# EXPLICACIÓN: SPA fallback + proxy /api al servicio 'api' (DNS interno de compose)
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
