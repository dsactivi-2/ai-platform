FROM nginx:1.27-alpine

# Remove default config
RUN rm /etc/nginx/conf.d/default.conf

# Copy template and auth file
COPY nginx.conf /etc/nginx/templates/default.conf.template
COPY .htpasswd /etc/nginx/.htpasswd

# Only substitute OUR variables, not nginx's $host/$remote_addr/etc
ENV NGINX_ENVSUBST_FILTER='^(API_HOST|API_PORT|WEB_HOST|WEB_PORT|PERPLEXITY_BACKEND_HOST|PERPLEXITY_BACKEND_PORT|PERPLEXITY_FRONTEND_HOST|PERPLEXITY_FRONTEND_PORT|GOVERNOR_HOST|GOVERNOR_PORT|CRAWL_HOST|CRAWL_PORT|SIMULATION_HOST|SIMULATION_PORT|SKILLS_HOST|SKILLS_PORT|CREWAI_HOST|CREWAI_PORT)$'

EXPOSE 80

# Default values (overridden by Railway env vars)
ENV API_HOST=api.railway.internal
ENV API_PORT=5001
ENV WEB_HOST=web.railway.internal
ENV WEB_PORT=3000
ENV PERPLEXITY_BACKEND_HOST=perplexity-backend.railway.internal
ENV PERPLEXITY_BACKEND_PORT=8000
ENV PERPLEXITY_FRONTEND_HOST=perplexity-frontend.railway.internal
ENV PERPLEXITY_FRONTEND_PORT=3000
ENV GOVERNOR_HOST=governor.railway.internal
ENV GOVERNOR_PORT=8765
ENV CRAWL_HOST=lyzr-crawl.railway.internal
ENV CRAWL_PORT=8080
ENV SIMULATION_HOST=agent-simulation.railway.internal
ENV SIMULATION_PORT=8000
ENV SKILLS_HOST=lyzr-skills-kit.railway.internal
ENV SKILLS_PORT=8000
ENV CREWAI_HOST=crewai-studio.railway.internal
ENV CREWAI_PORT=8501
