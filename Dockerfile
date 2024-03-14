# TODO:
# - change used from from inconsolata to inconsolata-nerd

FROM pandoc/latex:3.1-alpine

WORKDIR /
RUN <<EOF
# Install from alpine cache
apk --no-cache add \
        git \
        font-noto \
        font-inconsolata-nerd \
        py3-pandocfilters

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

# Get filters
mv slidefactory/filter filters

EOF

WORKDIR /data

# Base executable with default flags
ENTRYPOINT [ "/usr/local/bin/pandoc", \
             "--data-dir=/data", \
             "--mathjax=/mathjax/MathJax.js", \
             "--to revealjs", \
             "--from markdown", \
             "--metadata revealjs-url=/reveal.js/", \
             "--metadata revealjs-css-url=/reveal.js/", \
             "--metadata theme=csc-2016", \
             "--metadata themepath=/themes/csc-2016", \
             "--standalone", \
             "--template=/themes/csc-2016/template.html", \
             "--highlight-style=pygments", \
             "--filter=/filters/background-image.py", \
             "--filter=/filters/contain-slide.py", \
             "--filter=/filters/url-encode.py", \
           ]
