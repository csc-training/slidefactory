#!/bin/bash

# Usage: pdf2svg.sh file.pdf
# Creates a svg file for each page

if [ "$#" -ne 1 ]; then
    echo ""
    echo "Error: wrong number of arguments!"
    echo "Usage: pdf2svg.sh file.pdf"
    echo ""
    exit 1
fi

imagefile=$1
base=$(basename -s .pdf $imagefile)

pdfseparate $imagefile $base-%02d.pdf
for pdf in $base-*
do
  pdfbase=$(basename -s .pdf $pdf)
  inkscape $pdf --export-plain-svg=$pdfbase.svg
done
rm $base-*.pdf
