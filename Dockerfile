FROM docker.io/alpine:3.17.3 AS slidefactory-files

ARG VERSION

ADD LICENSE /slidefactory/
ADD fonts/ /slidefactory/fonts/
ADD theme/ /slidefactory/theme/
ADD slidefactory.py /slidefactory/

RUN <<EOF
# Remove possible temporary files
find /slidefactory -name '*~' -delete
find /slidefactory -name '.*' -delete

# Fix permission
chmod a+r -R /slidefactory
chmod a+x /slidefactory/slidefactory.py

# Add checksums
cd /slidefactory
find . -type f -print0 | xargs -0 sha256sum > /tmp/sha256sums_$VERSION
mv /tmp/sha256sums_$VERSION /slidefactory/

EOF

FROM docker.io/alpine:3.17.3

RUN <<EOF
mkdir /work

apk update && \
    apk add --no-cache \
    ca-certificates \
    chromium \
    pandoc \
    font-freefont \
    python3 \
    py3-pandocfilters \
    tar \
    && \
    rm -rf /var/cache/apk/*

# Reveal.js
wget https://github.com/hakimel/reveal.js/archive/refs/tags/4.4.0.zip -O tmp.zip
unzip tmp.zip 'reveal.js-4.4.0/LICENSE' -d /slidefactory
unzip tmp.zip 'reveal.js-4.4.0/dist/*' -d /slidefactory
unzip tmp.zip 'reveal.js-4.4.0/plugin/*' -d /slidefactory
rm -f tmp.zip

# MathJax
wget https://github.com/mathjax/MathJax/archive/refs/tags/3.2.2.zip -O tmp.zip
unzip tmp.zip 'MathJax-3.2.2/LICENSE' -d /slidefactory
unzip tmp.zip 'MathJax-3.2.2/es5/tex-chtml-full.js' -d /slidefactory
unzip tmp.zip 'MathJax-3.2.2/es5/input/tex/extensions/*' -d /slidefactory
unzip tmp.zip 'MathJax-3.2.2/es5/output/chtml/fonts/woff-v2/*' -d /slidefactory
unzip tmp.zip 'MathJax-3.2.2/es5/adaptors/*' -d /slidefactory
rm -f tmp.zip

# Fonts
for FONT in 'Noto Sans' 'Inconsolata'; do
    FONT_URL=$(echo "$FONT" | tr ' ' +)
    FONT_DIR=$(echo "$FONT" | tr -d ' ')
    wget "https://fonts.google.com/download?family=$FONT_URL" -O tmp.zip
    mkdir -p /slidefactory/fonts/$FONT_DIR
    if unzip -l tmp.zip | grep -q 'static'; then
        unzip tmp.zip "static/$FONT_DIR/*" -d /slidefactory/fonts/
        mv /slidefactory/fonts/static/$FONT_DIR /slidefactory/fonts/
        rmdir /slidefactory/fonts/static
        unzip tmp.zip 'OFL.txt' -d /slidefactory/fonts/$FONT_DIR
        :;
    else
        unzip tmp.zip -d /slidefactory/fonts/$FONT_DIR
        :;
    fi
    rm -f tmp.zip
    :;
done
EOF

COPY --from=slidefactory-files /slidefactory/ /slidefactory/
WORKDIR /work
ENTRYPOINT ["/slidefactory/slidefactory.py"]
CMD ["-h"]
