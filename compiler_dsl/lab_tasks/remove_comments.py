"""Remove single-line and multi-line comments from source code."""

from __future__ import annotations


def remove_comments(source: str) -> str:
    result = []
    i = 0
    in_string = False
    escaped = False
    length = len(source)

    while i < length:
        char = source[i]

        if in_string:
            result.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            i += 1
            continue

        if source.startswith("//", i):
            i += 2
            while i < length and source[i] != "\n":
                i += 1
            continue

        if source.startswith("/*", i):
            i += 2
            while i < length and not source.startswith("*/", i):
                if source[i] == "\n":
                    result.append("\n")
                i += 1
            i += 2 if i < length else 0
            continue

        result.append(char)
        if char == '"':
            in_string = True
        i += 1

    return "".join(result)


if __name__ == "__main__":
    sample = "num a = 10; // comment\n/* block */\nshow(a);"
    print(remove_comments(sample))

