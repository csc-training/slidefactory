#!/bin/sh

# Default arguments
do_pdf=
theme="csc-2016"

# Parse arguments
while getopts "hpt:" name; do
    case "$name" in
        p)
            do_pdf=1;;
        t)
            theme="$OPTARG";;
        h|?)
            printf "Usage: %s: [-p] [-t theme] file.md\n" $0
            printf "\nAvailable themes in $SLIDEFACTORY_THEME_ROOT:\n"
            for d in $SLIDEFACTORY_THEME_ROOT/*; do
                if [ -f "$d/template.html" ]; then
                    printf "  %s\n" $(basename $d)
                fi
            done
            exit 2;;
    esac
done
shift $(($OPTIND - 1))

theme_dpath="$SLIDEFACTORY_THEME_ROOT/$theme"

# Convert files
for fpath in "$@"; do
    html_fpath=${fpath%.*}.html
    echo "Converting $fpath to $html_fpath"
    pandoc -d "$theme_dpath/defaults.yaml" --template="$theme_dpath/template.html" -o "$html_fpath" --metadata-file="$theme_dpath/urls.yaml" "$fpath"
    if [ $? -eq 0 ] && [ ! -z "$do_pdf" ]; then
        pdf_fpath=${fpath%.*}.pdf
        html_abs_fpath=$(readlink -f "$html_fpath")
        echo "Converting $html_fpath to $pdf_fpath"
        chromium-browser --headless --disable-gpu --disable-software-rasterizer --hide-scrollbars --virtual-time-budget=10000000 --run-all-compositor-stages-before-draw --print-to-pdf="$pdf_fpath" "file://$html_abs_fpath?print-pdf"
    fi
done
