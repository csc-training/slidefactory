FROM pandoc/latex:3.1-alpine
WORKDIR /app

RUN <<EOF
echo "Install packages from alpine package cache"
apk --no-cache add \
        git \
        python3 \
        py3-pandocfilters \
        unzip \
        curl \
        cabal

echo "Get MathJax from github"
wget -q -O mathjax.tar.gz https://github.com/mathjax/MathJax/archive/refs/tags/2.7.5.tar.gz
tar -xzf mathjax.tar.gz
mv MathJax-2.7.5 mathjax

echo "Get reveal.js from github"
wget -q -O reveal.tar.gz https://github.com/hakimel/reveal.js/archive/refs/tags/3.5.0.tar.gz
tar -xzf reveal.tar.gz
mv reveal.js-3.5.0 reveal.js

echo "Get CSC themes"
git clone -b pandocker https://github.com/csc-training/slidefactory.git
mv slidefactory/theme themes

echo "Get pandoc filters"
echo "CSC filters from github" 
mv slidefactory/filter filters

echo "pandoc-emphasize-code filter from github"
cabal install pandoc-emphasize-code
cabal install pandoc-types-1.17.5.4

rm -rf slidefactory
rm *.tar.gz

echo "Get fonts with curl"
mkdir fonts

# Noto Sans
curl --silent -o fonts.zip "https://gwfh.mranftl.com/api/fonts/noto-sans?download=zip&subsets=greek,latin-ext&variants=700,regular,italic,700italic&formats=woff2,ttf"
unzip -d ./fonts fonts.zip
rm fonts.zip

# Inconsolata
curl --silent -o fonts.zip "https://gwfh.mranftl.com/api/fonts/inconsolata?download=zip&subsets=latin&variants=700,regular&formats=woff2,ttf"
unzip -d ./fonts fonts.zip
rm fonts.zip
EOF

COPY ./fonts/* /app/fonts/
COPY ./defaults/* /app/defaults/
WORKDIR /data
ENTRYPOINT ["/usr/local/bin/pandoc", "--defaults=/app/defaults/revealjs.yaml", "--verbose"]
