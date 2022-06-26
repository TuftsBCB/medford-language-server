from toml import load
for d in load("pyproject.toml")["dependencies"].keys():
    print(d, end=" ")

