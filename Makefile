VERSION=$(shell python -c 'import textext; print textext.__version__')

dist:
	tar czf textext-$(VERSION).tar.gz textext.py textext.inx
