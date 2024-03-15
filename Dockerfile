FROM pandoc/latex:3.1-alpine
WORKDIR /app

RUN <<EOF
echo "Install packages from alpine package cache"
apk --no-cache add \
        git \
        python3 \
        py3-pandocfilters \
        unzip \
        curl

echo "Get MathJax from git"
wget -q -O mathjax.tar.gz https://github.com/mathjax/MathJax/archive/refs/tags/2.7.5.tar.gz
tar -xzf mathjax.tar.gz
mv MathJax-2.7.5 mathjax

echo "Get reveal.js from git"
wget -q -O reveal.tar.gz https://github.com/hakimel/reveal.js/archive/refs/tags/3.5.0.tar.gz
tar -xzf reveal.tar.gz
mv reveal.js-3.5.0 reveal.js
rm *.tar.gz

echo "Get CSC themes"
git clone -b pandocker https://github.com/csc-training/slidefactory.git
mv slidefactory/theme themes

echo "Get pandoc filters"
mv slidefactory/filter filters

rm -rf slidefactory

echo "Get fonts with curl"
mkdir fonts

# Noto Sans
curl --silent -o fonts.zip "https://gwfh.mranftl.com/api/fonts/noto-sans?download=zip&subsets=greek,latin-ext&variants=700,regular,italic,700italic&formats=woff2,ttf"
unzip -d ./fonts fonts.zip
rm fonts.zip

# Inconsolata
curl -o fonts.zip "https://gwfh.mranftl.com/api/fonts/inconsolata?download=zip&subsets=latin&variants=700,regular&formats=woff2,ttf"
unzip -d ./fonts fonts.zip
rm fonts.zip
EOF

COPY ./fonts/* /app/fonts/
COPY ./defaults/* /app/defaults/
WORKDIR /data
ENTRYPOINT ["/usr/local/bin/pandoc", "--defaults=/app/defaults/revealjs.yaml", "--verbose"]
