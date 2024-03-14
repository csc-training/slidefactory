# TODO:
# - change used from from inconsolata to inconsolata-nerd

FROM pandoc/latex:3.1-alpine

WORKDIR /app
RUN <<EOF
# Install from alpine cache
apk --no-cache add \
        git \
        python3 \
        py3-pandocfilters

# Get MathJax.js
wget -q -O mathjax.tar.gz https://github.com/mathjax/MathJax/archive/refs/tags/2.7.5.tar.gz
tar -xzf mathjax.tar.gz
mv MathJax-2.7.5 mathjax

# Get reveal.js
wget -q -O reveal.tar.gz https://github.com/hakimel/reveal.js/archive/refs/tags/3.5.0.tar.gz
tar -xzf reveal.tar.gz
mv reveal.js-3.5.0 reveal.js

# Get themes
git clone https://github.com/csc-training/slidefactory.git
mv slidefactory/theme themes

# Get filters
mv slidefactory/filter filters

# Get fonts
EOF

RUN <<EOF
# Make defaults file
mkdir defaults

cat << DEF > defaults/revealjs.yaml
data-dir: /data
to: revealjs
from: markdown
metadata:
  revealjs-url: /app/reveal.js
  theme: csc-2016
  themepath: /app/themes/csc-2016
standalone: true
self-contained: true
template: /app/themes/csc-2016/template.html
highlight-style: pygments
filters:
  - type: json
    path: /app/filters/background-image.py
  - type: json
    path: /app/filters/contain-slide.py
  - type: json
    path: /app/filters/url-encode.py
html-math-method:
  method: mathjax
  url: /app/mathjax/MathJax.js
DEF
EOF

WORKDIR /data

# Base executable with default flags
ENTRYPOINT ["/usr/local/bin/pandoc", "--defaults=/app/defaults/revealjs.yaml", "--verbose"]
