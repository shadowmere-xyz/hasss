.PHONY:
clean:
	rm -rf ./dist ./build ./*.egg-info

.PHONY:
build:
	python3 -m build

.PHONY:
upload: clean build
	twine upload ./dist/*
