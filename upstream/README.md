# upstream/ — snapshot, not the source of truth

This is a **copy** of the syllabic tokenizer as it exists in the ASR project it
was written for. The canonical version lives in that repo; edits made here do
not reach it.

It is kept for reference, not execution — `syllabic_tokenizer.py` subclasses
`BaseNepaliTokenizer`, which is not included, so importing it raises
`ModuleNotFoundError`. The runnable, dependency-free version of the same
tokenizer is `../nepali_syllabic_tokenizer.py`, flattened from these two files
with the base class's preprocessing inlined.

Worth reading here and absent from the flattened file: `pre_tokenize_str`,
which returns `(token, (start, end))` character offsets in HuggingFace
pre-tokenizer form. See §7 of `../README.md`.

If you change anything here, port it to the real repo and to
`../nepali_syllabic_tokenizer.py` — the two drifting apart is how a dropped
`not` in `remove_non_devanagari` handling went unnoticed.
