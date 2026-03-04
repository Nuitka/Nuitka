FROM mcr.microsoft.com/devcontainers/python:1-3.12

RUN mkdir -p /usr/share/keyrings \
 && curl -fsSL https://dl.yarnpkg.com/debian/pubkey.gpg \
    | gpg --dearmor -o /usr/share/keyrings/yarn.gpg \
 && echo "deb [signed-by=/usr/share/keyrings/yarn.gpg] https://dl.yarnpkg.com/debian stable main" \
    > /etc/apt/sources.list.d/yarn.list
