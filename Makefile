VERSION=$(shell python -c 'import textext; print textext.__version__')

dist:
	tar czf textext-$(VERSION).tar.gz textext.py textext.inx
	zip textext-$(VERSION).zip textext.py textext.inx

textext.iss:
	sed -e 's/@VERSION@/$(VERSION)/' < textext.iss.in > textext.iss


