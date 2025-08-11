# Simple Next.js production image
FROM node:20-alpine AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci

FROM node:20-alpine AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:20-alpine AS runner
ENV NODE_ENV=production
WORKDIR /app
# Copy full app (keeps .next and node_modules from build)
COPY --from=build /app ./
EXPOSE 3000
CMD ["npm","run","start"]
