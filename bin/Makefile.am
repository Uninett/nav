bin_SCRIPTS = $(wildcard *.py) $(wildcard *.sh) nav ipdevpolld navtopology eventengine navsyncdb navpgdump thresholdmon

check:
	PYTHONPATH=. $(top_srcdir)/python/runtests.py $(top_srcdir)/tests/unittests-bin
