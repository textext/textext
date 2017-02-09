@echo off

pandoc --verbose --variable linkcolor=blue --variable fontfamily=opensans --variable fontfamilyoptions=default,osfigures,scale=0.95 --variable margin-left=2cm --variable margin-right=2cm --variable margin-top=2.5cm --variable margin-bottom=2.5cm --variable fontsize=12pt README-TexText.md -o README-TexText.pdf

pandoc --verbose -s -S -c pandoc.css README-TexText.md -o README-TexText.html
