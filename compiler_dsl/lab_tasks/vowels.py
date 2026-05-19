"""Count vowels and consonants in a string."""

from __future__ import annotations

from dataclasses import dataclass


VOWELS = set("aeiouAEIOU")


@dataclass
class VowelCounter:
    text: str

    def count(self) -> tuple[int, int]:
        vowels = 0
        consonants = 0
        for char in self.text:
            if char.isalpha():
                if char in VOWELS:
                    vowels += 1
                else:
                    consonants += 1
        return vowels, consonants


def count_vowels_consonants(text: str) -> tuple[int, int]:
    return VowelCounter(text).count()


if __name__ == "__main__":
    sample = "Compiler"
    vowels, consonants = count_vowels_consonants(sample)
    print(f"Input: {sample}")
    print(f"Vowels: {vowels}")
    print(f"Consonants: {consonants}")

