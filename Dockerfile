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

echo "Get CSC themes"
git clone -b pandocker https://github.com/csc-training/slidefactory.git
mv slidefactory/theme themes

echo "Get pandoc filters"
mv slidefactory/filter filters

echo "Get fonts with curl"
mkdir fonts

# Noto Sans
curl --silent -o fonts.zip "https://gwfh.mranftl.com/api/fonts/noto-sans?download=zip&subsets=greek,latin-ext&variants=700,regular,italic,700italic&formats=woff2,ttf"
unzip -z -d ./fonts fonts.zip
rm fonts.zip

# Inconsolata
curl -o fonts.zip "https://gwfh.mranftl.com/api/fonts/inconsolata?download=zip&subsets=latin&variants=700,regular&formats=woff2,ttf"
unzip -z -d ./fonts fonts.zip
rm fonts.zip
EOF

# Copy the css files
echo "Copying font css files"
COPY ./fonts/* /app/fonts/

echo "Copying pandoc defaults files"
COPY ./defaults/* /app/defaults/

RUN <<ROF
ls -lah /app
ls -lah /app/fonts
ls -lah /app/defaults
ROF

WORKDIR /data

# Base executable with default flags
ENTRYPOINT ["/usr/local/bin/pandoc", "--defaults=/app/defaults/revealjs.yaml", "--verbose"]
