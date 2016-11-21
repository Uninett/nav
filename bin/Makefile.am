bin_SCRIPTS = $(wildcard *.py) $(wildcard *.sh) \
              eventengine \
              ipdevpolld \
              nav \
              navcheckservice \
              navdf \
              naventity \
              navoidverify \
              navpgdump \
              navsnmp \
              navstats \
              navsyncdb \
              navtopology \
              navuser \
              thresholdmon

check:
	PYTHONPATH=. $(top_srcdir)/python/runtests.py $(top_srcdir)/tests/unittests-bin
