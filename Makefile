.PHONY: dummy clean bigclean

dummy:
	@echo "'make' is no longer used for deployment. See 'doc/intro/install.rst'"

clean:
	-find . -name __pycache__ -print0 | xargs -0 rm -rf
	-find . -name "*.pyc" -print0 | xargs -0 rm -rf
	-find . -name "*.egg-info" -print0 | xargs -0 rm -rf
	-find . -name ".*.sw?" -print0 | xargs -0 rm -rf

testclean: clean
	-rm core
	-rm *.stats
	-rm python/nav/web/static/js/package-lock.json
	-rm -rf .tox
