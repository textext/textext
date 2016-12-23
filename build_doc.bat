pandoc --variable linkcolor=blue --variable fontfamily=opensans --variable fontfamilyoptions=default,osfigures,scale=0.95 --variable margin-left=2cm --variable margin-right=2cm --variable margin-top=2.5cm --variable margin-bottom=2.5cm --variable fontsize=12pt docs/Readme.md -o docs/Readme.pdf

pandoc --verbose -s -S -c pandoc.css docs/Readme.md -o docs/Readme.html
