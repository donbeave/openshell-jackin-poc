FROM nginx:1.29.3-alpine
COPY . /workspace/ojp-project
CMD ["find", "/workspace/ojp-project", "-maxdepth", "2", "-type", "f"]
