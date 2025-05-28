FROM docker.io/debian:bookworm-slim AS slidefactory-files

ARG VERSION

ADD LICENSE /slidefactory/
ADD fonts/ /slidefactory/fonts/
ADD theme/ /slidefactory/theme/
ADD slidefactory.py /slidefactory/

# Remove possible temporary files
RUN find /slidefactory -name '*~' -delete
RUN find /slidefactory -name '.*' -delete

# Fix permissions
RUN chmod 755 /slidefactory && \
    find /slidefactory -type d -exec chmod 755 {} \; && \
    find /slidefactory -type f -exec chmod 644 {} \; && \
    chmod 755 /slidefactory/slidefactory.py

# Add checksums
RUN cd /slidefactory && \
    find . -type f -print0 | xargs -0 sha256sum > /tmp/sha256sums_$VERSION && \
    mv /tmp/sha256sums_$VERSION /slidefactory/


FROM docker.io/debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update -qy && \
    apt-get install -qy --no-install-recommends \
      ca-certificates \
      chromium \
      git \
      fonts-freefont-otf \
      fonts-liberation \
      python3 \
      python3-pandocfilters \
      python3-yaml \
      tar \
      wget \
      zip unzip \
      && \
    apt-get clean

# Install pandoc
RUN wget https://github.com/jgm/pandoc/releases/download/2.19.2/pandoc-2.19.2-1-amd64.deb -O tmp.deb && \
    dpkg -i tmp.deb && \
    rm -f tmp.deb

# Reveal.js
RUN wget https://github.com/hakimel/reveal.js/archive/refs/tags/4.4.0.zip -O tmp.zip && \
    unzip tmp.zip 'reveal.js-4.4.0/LICENSE' -d /slidefactory && \
    unzip tmp.zip 'reveal.js-4.4.0/dist/*' -d /slidefactory && \
    unzip tmp.zip 'reveal.js-4.4.0/plugin/*' -d /slidefactory && \
    rm -f tmp.zip

# MathJax
RUN wget https://github.com/mathjax/MathJax/archive/refs/tags/3.2.2.zip -O tmp.zip && \
    unzip tmp.zip 'MathJax-3.2.2/LICENSE' -d /slidefactory && \
    unzip tmp.zip 'MathJax-3.2.2/es5/tex-chtml-full.js' -d /slidefactory && \
    unzip tmp.zip 'MathJax-3.2.2/es5/input/tex/extensions/*' -d /slidefactory && \
    unzip tmp.zip 'MathJax-3.2.2/es5/output/chtml/fonts/woff-v2/*' -d /slidefactory && \
    unzip tmp.zip 'MathJax-3.2.2/es5/adaptors/*' -d /slidefactory && \
    rm -f tmp.zip

# Fonts
RUN FONT_DIR=NotoSans && \
    mkdir -p /slidefactory/fonts/$FONT_DIR && \
    wget https://github.com/notofonts/latin-greek-cyrillic/releases/download/NotoSans-v2.013/NotoSans-v2.013.zip -O tmp.zip && \
    unzip -j tmp.zip 'NotoSans/googlefonts/ttf/*' -d /slidefactory/fonts/$FONT_DIR && \
    unzip -j tmp.zip 'OFL.txt' -d /slidefactory/fonts/$FONT_DIR && \
    rm tmp.zip

RUN FONT_DIR=Inconsolata && \
    mkdir -p /slidefactory/fonts/$FONT_DIR && \
    wget https://github.com/googlefonts/Inconsolata/archive/refs/tags/v3.000.zip -O tmp.zip && \
    unzip -j tmp.zip 'Inconsolata-3.000/fonts/ttf/Inconsolata-*' -x '*Condensed*' '*Expanded*' -d /slidefactory/fonts/$FONT_DIR && \
    unzip -j tmp.zip 'Inconsolata-3.000/OFL.txt' -d /slidefactory/fonts/$FONT_DIR && \
    rm tmp.zip

COPY --from=slidefactory-files /slidefactory/ /slidefactory/

# Create executable
RUN echo '#!/bin/sh\n\
exec python3 /slidefactory/slidefactory.py "$@"\n\
' > /usr/bin/slidefactory && \
    chmod a+x /usr/bin/slidefactory

RUN mkdir /work

WORKDIR /work

ENTRYPOINT ["slidefactory"]
CMD ["-h"]
