ARG REGISTRY=""
FROM ${REGISTRY}node:24.13-alpine AS base
WORKDIR /app
ENV NPM_CONFIG_LOGLEVEL=warn
COPY package*.json ./
RUN npm install --no-audit --no-fund --loglevel=error

FROM base AS dev
COPY . .
CMD ["npm", "run", "dev"]

FROM base AS build
COPY . .
RUN npm run build

# Stage 2: Production environment
FROM ${REGISTRY}nginx:1.29.5-alpine
RUN rm -rf /usr/share/nginx/html/*
COPY --from=build /app/dist /usr/share/nginx/html
RUN sed -i 's/index  index.html index.htm;/try_files $uri $uri\/ \/index.html;/g' /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]