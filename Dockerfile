FROM docker.io/alpine:3.17.3

LABEL org.opencontainers.image.source=https://github.com/csc-training/slidefactory

RUN apk update && \
    apk add --no-cache \
      ca-certificates \
      chromium~=111.0 \
      pandoc~=2.19 \
      # Fonts required by the CSC style \
      font-noto \
      font-inconsolata \
      # Common fonts \
      font-freefont \
      font-dejavu \
      && \
    # Remove Noto Display fonts; \
    # those get wrongly picked to the pdf \
    rm -f /usr/share/fonts/noto/*Display*.ttf && \
    rm -rf /var/cache/apk/*

ENV SLIDEFACTORY_ROOT=/slidefactory

ENV SLIDEFACTORY_THEME_ROOT=$SLIDEFACTORY_ROOT/theme \
    PATH=$SLIDEFACTORY_ROOT/bin:$PATH

ADD theme/ $SLIDEFACTORY_THEME_ROOT/
ADD convert.sh $SLIDEFACTORY_ROOT/bin/

RUN mkdir /work

WORKDIR /work

ENTRYPOINT ["convert.sh"]
CMD ["-h"]
