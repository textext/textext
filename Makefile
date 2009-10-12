VERSION=$(shell python -c 'import textext; print textext.__version__')

dist:
	tar czf textext-$(VERSION).tar.gz textext.py textext.inx LICENSE.txt
	zip textext-$(VERSION).zip textext.py textext.inx LICENSE.txt

textext.iss: textext.iss.in textext.py
	sed -e 's/@VERSION@/$(VERSION)/' < textext.iss.in > textext.iss

.PHONY: dist
