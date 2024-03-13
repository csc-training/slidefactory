# TODO:
# - change used from from inconsolata to inconsolata-nerd

FROM pandoc/latex:3.1-alpine

COPY defaults/* .

WORKDIR /home/pandocker

RUN <<EOF
# Install from alpine cache
apk --no-cache add \
        git \
        font-noto \
        font-inconsolata-nerd

# Get MathJax.js
wget -O mathjax.tar.gz https://github.com/mathjax/MathJax/archive/refs/tags/2.7.5.tar.gz
tar -xzf mathjax.tar.gz
mv MathJax-2.7.5 mathjax

# Get reveal.js
wget -O reveal.tar.gz https://github.com/hakimel/reveal.js/archive/refs/tags/3.5.0.tar.gz
tar -xzf reveal.tar.gz
mv reveal.js-3.5.0 reveal.js

# Get themes
git clone https://github.com/csc-training/slidefactory.git
mv slidefactory/theme themes

# Make a defaults file that uses stuff from the themes directory
pwd
ls -lah

EOF
