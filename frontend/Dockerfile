# Imatge de desenvolupament del frontend (Vue 3 + Vite).
# Vite 8 necessita Node 20.19+ o 22.12+.
FROM node:22-alpine

WORKDIR /app

# Primer només les dependències, perquè Docker en reaprofiti la capa si el codi canvia.
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

EXPOSE 5173

# Servidor de desenvolupament de Vite escoltant fora del contenidor.
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
