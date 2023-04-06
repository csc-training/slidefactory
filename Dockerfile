FROM docker.io/alpine:3.17.3

LABEL org.opencontainers.image.source=https://github.com/csc-training/slidefactory

RUN apk update && \
    apk add --no-cache \
      ca-certificates \
      chromium \
      pandoc \
      font-freefont \
      python3 \
      py3-pandocfilters \
      && \
    rm -rf /var/cache/apk/*

ENV SLIDEFACTORY_ROOT=/slidefactory

RUN wget https://github.com/hakimel/reveal.js/archive/refs/tags/4.4.0.zip -O tmp.zip && \
    unzip tmp.zip 'reveal.js-4.4.0/LICENSE' -d $SLIDEFACTORY_ROOT && \
    unzip tmp.zip 'reveal.js-4.4.0/dist/*' -d $SLIDEFACTORY_ROOT && \
    unzip tmp.zip 'reveal.js-4.4.0/plugin/*' -d $SLIDEFACTORY_ROOT && \
    rm -f tmp.zip

RUN wget https://github.com/mathjax/MathJax/archive/refs/tags/3.2.2.zip -O tmp.zip && \
    unzip tmp.zip 'MathJax-3.2.2/LICENSE' -d $SLIDEFACTORY_ROOT && \
    unzip tmp.zip 'MathJax-3.2.2/es5/tex-chtml-full.js' -d $SLIDEFACTORY_ROOT && \
    unzip tmp.zip 'MathJax-3.2.2/es5/input/tex/extensions/*' -d $SLIDEFACTORY_ROOT && \
    unzip tmp.zip 'MathJax-3.2.2/es5/output/chtml/fonts/woff-v2/*' -d $SLIDEFACTORY_ROOT && \
    unzip tmp.zip 'MathJax-3.2.2/es5/adaptors/*' -d $SLIDEFACTORY_ROOT && \
    rm -f tmp.zip

# Fonts
RUN for FONT in 'Noto Sans' 'Noto Sans Mono' 'Inconsolata'; do \
      FONT_URL=$(echo "$FONT" | tr ' ' +) && \
      FONT_DIR=$(echo "$FONT" | tr -d ' ') && \
      wget "https://fonts.google.com/download?family=$FONT_URL" -O tmp.zip && \
      mkdir -p $SLIDEFACTORY_ROOT/fonts/$FONT_DIR && \
      if unzip -l tmp.zip | grep -q 'static'; then \
        unzip tmp.zip "static/$FONT_DIR/*" -d $SLIDEFACTORY_ROOT/fonts/ && \
        mv $SLIDEFACTORY_ROOT/fonts/static/$FONT_DIR $SLIDEFACTORY_ROOT/fonts/ && \
        rmdir $SLIDEFACTORY_ROOT/fonts/static && \
        unzip tmp.zip 'OFL.txt' -d $SLIDEFACTORY_ROOT/fonts/$FONT_DIR && \
        :; \
      else \
        unzip tmp.zip -d $SLIDEFACTORY_ROOT/fonts/$FONT_DIR && \
        :; \
      fi && \
      rm -f tmp.zip && \
      :; \
    done

ADD css/fonts.css $SLIDEFACTORY_ROOT/fonts

ENV SLIDEFACTORY_THEME_ROOT=$SLIDEFACTORY_ROOT/theme \
    PATH=$SLIDEFACTORY_ROOT/bin:$PATH

ADD theme/ $SLIDEFACTORY_THEME_ROOT/
ADD convert.py $SLIDEFACTORY_ROOT/bin/

RUN mkdir /work

WORKDIR /work

ENTRYPOINT ["convert.py"]
CMD ["-h"]
