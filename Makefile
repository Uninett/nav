.PHONY: clean bigclean

clean:
	find . -name __pycache__ -print0 | xargs -0 rm -rf
	find . -name "*.pyc" -print0 | xargs -0 rm -rf
	find . -name "*.egg-info" -print0 | xargs -0 rm -rf

bigclean: clean
	rm -rf .tox
