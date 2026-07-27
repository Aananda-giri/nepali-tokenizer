"""
Nepali Syllabic Tokenizer V2 Implementation
Rule-based approach using Devanagari character sets and linguistic rules
"""

import string
from typing import List, Tuple

try:
    from .syllable_dataset import SyllableDataset
except ImportError:
    from syllable_dataset import SyllableDataset

try:
    from .base_tokenizer import BaseNepaliTokenizer
except ImportError:
    from base_tokenizer import BaseNepaliTokenizer


Span = Tuple[int, int]


class NepaliSyllabicTokenizer(BaseNepaliTokenizer):
    """
    Rule-based syllabic tokenizer for Nepali language using Devanagari character sets

    Algorithm:
    1. Scan text left to right
    2. Each token starts with a vowel, consonant, or complex consonant
    3. Accumulate characters (vowel markers, halant, other markers) until the next
       vowel/consonant/complex consonant/space is reached
    """

    #: Characters replaced by a space during preprocessing.
    PUNCTUATION = frozenset(string.punctuation) | frozenset('।,.?!-\'"')

    def __init__(self, normalize: bool = False, remove_non_devanagari: bool = True):
        """
        Initialize the tokenizer with Devanagari character sets

        Args:
            normalize: If True, normalizes characters before tokenization (default: False)
                      ई -> इ, श/ष -> स, ऊ -> उ, ी -> ि, ू -> ु
            remove_non_devanagari: If True, removes non-Devanagari characters (default: True)
        """
        super().__init__(normalize=normalize, remove_non_devanagari=remove_non_devanagari)

    def _preprocess_with_offsets(self, text: str) -> Tuple[str, List[int]]:
        """
        Preprocess text while keeping track of where each surviving character
        came from in the input.

        Equivalent to _preprocess_text (punctuation -> space, whitespace runs
        collapsed to a single space), but also returns an index map so tokens can
        be reported against the *original* string rather than the cleaned one.

        Returns:
            (clean, src) where clean[k] originates at text[src[k]]
        """
        chars: List[str] = []
        src: List[int] = []
        prev_space = False

        for i, ch in enumerate(text):
            c = ' ' if (ch in self.PUNCTUATION or ch.isspace()) else ch
            if c == ' ':
                if prev_space:      # collapse the run, drop this character
                    continue
                prev_space = True
            else:
                prev_space = False
            chars.append(c)
            src.append(i)

        return ''.join(chars), src

    def _scan(self, text: str) -> List[Tuple[str, Span]]:
        """
        Core syllable scanner. Single source of truth for both tokenize() and
        pre_tokenize_str().

        Rules:
        - Scan left to right
        - Each token starts with a vowel, consonant, or complex consonant
        - Accumulate characters (vowel markers, halant, other markers) until the next
          vowel/consonant/complex consonant/space is reached

        Args:
            text: Input text string in Devanagari

        Returns:
            List of (token, (start, end)) with offsets into `text`
        """
        clean, src = self._preprocess_with_offsets(text)

        normalized = self._normalize_text(clean)
        if len(normalized) != len(clean):
            # Offsets are only meaningful if normalization is a 1:1 character
            # substitution. Fail loudly rather than return silently wrong spans.
            raise ValueError(
                "_normalize_text changed the text length; offset mapping assumes "
                "a one-to-one character substitution"
            )
        clean = normalized

        # [token, start, end] -- mutable so attaching markers can extend the span
        tokens: List[List] = []
        i = 0

        while i < len(clean):
            first_three_chars = clean[i:i + 3]
            char = clean[i]

            # 1. space
            if char.isspace():
                # Span points at the first character of a collapsed whitespace run.
                tokens.append([" ", src[i], src[i] + 1])
                i += 1
                continue

            # 2. Check Complex consonant
            if first_three_chars in SyllableDataset.COMPLEX_CONSONANTS_SET:
                tokens.append([first_three_chars, src[i], src[i + 2] + 1])
                i += 3
                continue

            # 3. check if char is vowel or consonant
            elif char in SyllableDataset.VOWELS_SET or char in SyllableDataset.CONSONANTS_SET:
                tokens.append([char, src[i], src[i] + 1])
                i += 1
                continue

            # 4. Handle vowel markers, halant, and other markers (attach to previous token)
            elif char in SyllableDataset.ATTACHING_MARKERS:
                if tokens and not tokens[-1][0].isspace():
                    tokens[-1][0] += char
                    tokens[-1][2] = src[i] + 1
                else:
                    # Handle case where marker appears at beginning (shouldn't happen in valid text)
                    tokens.append([char, src[i], src[i] + 1])
                i += 1
                continue

            # Handle any other characters (numbers, invalid characters etc.)
            # todo: convert numbers to word in pre process? `SyllableDataset.NUMBERS?`
            if not self.remove_non_devanagari:
                tokens.append([char, src[i], src[i] + 1])
            i += 1

        return [(tok, (start, end)) for tok, start, end in tokens]

    def tokenize(self, text: str) -> List[str]:
        """
        Tokenize Devanagari text into syllabic units.
        - used by deepspeech2/

        Args:
            text: Input text string in Devanagari

        Returns:
            List of tokens
        """
        if not text:
            return []
        return [tok for tok, _ in self._scan(text)]

    def pre_tokenize_str(self, text: str) -> List[Tuple[str, Span]]:
        """
        Tokenize Devanagari text into syllabic units, with offsets.
        Compatible with huggingface transformers pre_tokenizer.

        Offsets index into `text` as given, so text[start:end] returns the token
        (for tokens that survive preprocessing unchanged).

        Args:
            text: Input text string in Devanagari

        Returns:
            List of (token, (start, end))
        """
        if not text:
            return []
        return self._scan(text)

    def encode(self, text: str) -> List[str]:
        """Alias for tokenize method"""
        return self.tokenize(text)

    def decode(self, tokens: List[str]) -> str:
        """
        Decode tokens back to text
        - used by deepspeech2/

        Args:
            tokens: List of syllabic tokens, as returned by tokenize()

        Returns:
            Reconstructed text
        """
        return ''.join(tokens)

    def tokenize_batch(self, texts: List[str]) -> List[List[str]]:
        """
        Tokenize multiple texts

        Args:
            texts: List of input texts

        Returns:
            List of tokenized texts
        """
        return [self.tokenize(text) for text in texts]
