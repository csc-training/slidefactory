FROM pandoc/latex:3.1-alpine
WORKDIR /app

RUN <<EOF
echo "Install packages from alpine package cache"
# Common tools
apk --no-cache add \
        git \
        python3 \
        py3-pandocfilters \
        unzip \
        curl

# pandoc-emphasize-code dependencies
apk --no-cache add \
        ghc \
        alpine-sdk \
        libffi \
        libffi-dev \
        cabal

echo "Get MathJax from github"
wget -qO mathjax.tar.gz https://github.com/mathjax/MathJax/archive/refs/tags/2.7.5.tar.gz
tar -xzf mathjax.tar.gz
mv MathJax-2.7.5 mathjax

echo "Get reveal.js from github"
wget -qO reveal.tar.gz https://github.com/hakimel/reveal.js/archive/refs/tags/3.5.0.tar.gz
tar -xzf reveal.tar.gz
mv reveal.js-3.5.0 reveal.js

echo "Get CSC themes"
git clone -b pandocker https://github.com/csc-training/slidefactory.git
mv slidefactory/theme themes

echo "Get pandoc filters:"
mkdir filters
echo "- pandoc-emphasize-code"
cabal update
cabal install pandoc-emphasize-code
cp /root/.cabal/store/ghc-9.0.1/pandoc-emphasize-code*/bin/pandoc-emphasize-code /app/filters/

rm -rf slidefactory
rm *.tar.gz

echo "Get fonts with curl:"
mkdir fonts

echo "- Noto Sans"
curl -so fonts.zip "https://gwfh.mranftl.com/api/fonts/noto-sans?download=zip&subsets=greek,latin-ext&variants=700,regular,italic,700italic&formats=woff2,ttf"
unzip -qqd ./fonts fonts.zip
rm fonts.zip

echo "- Inconsolata"
curl -so fonts.zip "https://gwfh.mranftl.com/api/fonts/inconsolata?download=zip&subsets=latin&variants=700,regular&formats=woff2,ttf"
unzip -qqd ./fonts fonts.zip
rm fonts.zip
EOF

COPY ./fonts/* /app/fonts/
COPY ./defaults/* /app/defaults/
COPY ./filters/* /app/filters/

WORKDIR /data
ENTRYPOINT ["/usr/local/bin/pandoc", "--defaults=/app/defaults/revealjs.yaml", "--verbose"]
