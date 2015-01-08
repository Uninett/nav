bin_SCRIPTS = $(wildcard *.py) $(wildcard *.sh) \
              eventengine \
              ipdevpolld \
              nav \
              navdf \
              naventity \
              navoidverify \
              navpgdump \
              navsyncdb \
              navtopology \
              thresholdmon

check:
	PYTHONPATH=. $(top_srcdir)/python/runtests.py $(top_srcdir)/tests/unittests-bin
