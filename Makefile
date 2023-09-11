.PHONY: dummy clean distclean testclean doc .FORCE

dummy:
	@echo "'make' is no longer used for deployment. See 'doc/intro/install.rst'"

clean:
	-find . -name __pycache__ -print0 | xargs -0 rm -rf
	-find . -name "*.pyc" -print0 | xargs -0 rm -rf
	-find . -name "*.egg-info" -print0 | xargs -0 rm -rf
	-find . -name ".*.sw?" -print0 | xargs -0 rm -rf

distclean:
	-rm -rf build
	-rm -rf dist

testclean: clean
	-rm core
	-rm *.stats
	-rm python/nav/web/static/js/package-lock.json
	-rm -rf .tox

doc: doc/reference/alerttypes.rst

doc/reference/alerttypes.rst: .FORCE
	python3 doc/exts/alerttypes.py > $@

.FORCE:
