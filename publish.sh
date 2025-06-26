echo "Publishing package to PyPI..."
rm -rf ./dist/* && python3 -m build && python3 -m twine upload dist/* && rm -rf ./dist/*
echo "Package published successfully."