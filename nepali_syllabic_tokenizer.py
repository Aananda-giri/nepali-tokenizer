"""
Nepali Syllabic Tokenizer V2 Implementation
Rule-based approach using Devanagari character sets and linguistic rules
"""

import re
import string
from typing import Set, List

class SyllableDataset:
    """
    Syllable Dataset Generator for Nepali Devanagari Script
    Generates all valid syllables based on Devanagari grammar rules
    Generate and manage Nepali syllable dataset based on Devanagari grammar
    """
    
    # Devanagari character sets
    VOWELS = ['अ', 'आ', 'इ', 'ई', 'उ', 'ऊ', 'ए', 'ऐ', 'ओ', 'औ', 'ऋ', 'ॠ', 'ऌ',
              'ऑ', 'ऍ']  # candra o/e: loanwords (ऑफिस)

    CONSONANTS = [
        'क', 'ख', 'ग', 'घ', 'ङ',
        'च', 'छ', 'ज', 'झ', 'ञ',
        'ट', 'ठ', 'ड', 'ढ', 'ण',
        'त', 'थ', 'द', 'ध', 'न',
        'प', 'फ', 'ब', 'भ', 'म',
        'य', 'र', 'ल', 'व',
        'श', 'ष', 'स', 'ह' # क्ष = 'क' + '्' + 'ष', त्र = 'त' + '्' + 'र', ज्ञ ='ज' + '्' + 'ञ'
    ]

    HALANT = '्'  # Virama/halant marker
    
    # vowel markers,HALANT, OTHER_MARKERS: should be attached to the last consonant (they should not be individual tokens)
    # Any matra missing from this list is silently dropped by the tokenizer, so
    # omissions here are data loss, not just mis-segmentation.
    VOWEL_MARKERS = ['ा', 'ि', 'ी', 'ु', 'ू', 'े', 'ै', 'ो', 'ौ', 'ृ',
                     'ॉ', 'ॅ',  # candra o/e: loanwords (कॉलेज, डॉक्टर)
                     'ॄ']       # vocalic RR, pairs with ॠ above
    # Deliberately excluded: ॆ, ॊ (short e/o) -- Dravidian-range, not used in Nepali.

    OTHER_MARKERS = ['ं', 'ः', 'ँ']
    
    NUMBERS = ['०', '१', '२', '३', '४', '५', '६', '७', '८', '९']
    
    INVALID_TOKENS = ['ऌ', 'ऌं', 'ऌः', 'ऌँ', 'ॠ', 'ॠं', 'ॠः', 'ॠँ']

    # Common complex consonants (NOTE: all complex consonants have len. 3)
    COMPLEX_CONSONANTS = [
        'क्ष', 'ज्ञ','द्ध', 'द्य', 'त्त', 'द्व'
    ] + [consonant + '्' + 'र' for consonant in CONSONANTS]
    # excluding 'त्र' (tra),  'श्र' (e.g. in shree) because they would be covered under: consonant + HALANT + 'र'

    # Precomputed lookup sets for the tokenizer's scan loop. The lists above stay
    # the public API (ordered, iterable for generation); these are for membership.
    VOWELS_SET = frozenset(VOWELS)
    CONSONANTS_SET = frozenset(CONSONANTS)
    COMPLEX_CONSONANTS_SET = frozenset(COMPLEX_CONSONANTS)
    # Everything that attaches to the preceding token instead of starting one.
    ATTACHING_MARKERS = frozenset(VOWEL_MARKERS + [HALANT] + OTHER_MARKERS)


    def __init__(self):
        self.syllables: Set[str] = set()
        self._generate_syllables()
    
    def _generate_syllables(self):
        """Generate all valid Nepali syllables"""
        
        # 1. Single vowels
        self.syllables.update(self.VOWELS)
        
        # 2. Single consonants (with inherent 'a' sound)
        self.syllables.update(self.CONSONANTS)

        # 3. Add pre-defined complex consonants
        self.syllables.update(self.COMPLEX_CONSONANTS)
        
        # 4. Numbers
        self.syllables.update(self.NUMBERS)
        
        # 5. Space and punctuation
        self.syllables.update([' '])  # '।', ',', '.', '?', '!', '-', '\'', '"'
            
        # 6. Consonant/complex consonant + vowel marker
        for c in self.CONSONANTS + self.COMPLEX_CONSONANTS:
            for vm in self.VOWEL_MARKERS:
                self.syllables.add(c + vm)
                
                # e.g. दिँदै
                for om in self.OTHER_MARKERS:
                   self.syllables.add(c + vm + om)
        
        
        
        # 7. Consonant/complex consonant + halant (dead consonant)
        for c in self.CONSONANTS + self.COMPLEX_CONSONANTS:
            self.syllables.add(c + self.HALANT)

        # 8. Consonants/vowels/complex consonants with other markers (anusvara, visarga, chandrabindu)
        for c in self.CONSONANTS + self.VOWELS + self.COMPLEX_CONSONANTS:
            for om in self.OTHER_MARKERS:
                self.syllables.add(c + om)
        
        # NOTE: a "Consonant + Halanta + ra" loop used to live here. It was a
        # no-op -- those forms are already in COMPLEX_CONSONANTS, added in step 3.

        # 9. Drop the grammatically invalid combinations declared above. ऌ and ॠ
        # stay in VOWELS because they are real characters, but they do not form
        # these syllables, so remove them after generation.
        self.syllables.difference_update(self.INVALID_TOKENS)

    def contains(self, syllable: str) -> bool:
        """Check if a syllable exists in the dataset"""
        return syllable in self.syllables
    
    def get_all_syllables(self) -> Set[str]:
        """Return all syllables in the dataset"""
        return self.syllables.copy()
    
    def save_to_file(self, filepath: str):
        """Save syllable dataset to a file"""
        with open(filepath, 'w', encoding='utf-8') as f:
            for syllable in sorted(self.syllables):
                f.write(syllable + '\n')
    
    @classmethod
    def load_from_file(cls, filepath: str) -> 'SyllableDataset':
        """Load syllable dataset from a file"""
        dataset = cls.__new__(cls)
        dataset.syllables = set()
        
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                syllable = line.strip()
                if syllable:
                    dataset.syllables.add(syllable)
        
        return dataset
    
    def __len__(self):
        return len(self.syllables)
    
    def __contains__(self, item):
        return item in self.syllables


class NepaliSyllabicTokenizer:
    """
    Rule-based syllabic tokenizer for Nepali language using Devanagari character sets

    Algorithm:
    1. Scan text left to right
    2. Each token starts with a vowel, consonant, or complex consonant
    3. Accumulate characters (vowel markers, halant, other markers) until the next
       vowel/consonant/complex consonant/space is reached
    """

    def __init__(self, remove_non_devanagari: bool = True):
        """
        Initialize the tokenizer with Devanagari character sets

        Args:
            remove_non_devanagari: If True, removes non-Devanagari characters (default: True)
        """
        self.remove_non_devanagari = remove_non_devanagari

    def _preprocess_text(self, text: str) -> str:
        """
        Preprocess text by replacing punctuations with spaces and normalizing spaces

        Args:
            text: Input text

        Returns:
            Preprocessed text with punctuations replaced by single spaces
            and multiple spaces collapsed to single spaces
        """
        # Replace all standard ASCII punctuation characters with single space
        for punct in string.punctuation:
            text = text.replace(punct, ' ')

        # Replace Nepali punctuation marks with single space
        nepali_punctuation = ['।', ',', '.', '?', '!', '-', '\'', '"']
        for punct in nepali_punctuation:
            text = text.replace(punct, ' ')

        # Replace multiple spaces with single space using regex
        text = re.sub(r'\s+', ' ', text)

        return text

    def tokenize(self, text: str) -> List[str]:
        """
        Tokenize Devanagari text into syllabic units.

        Rules:
        - Scan left to right
        - Each token starts with a vowel, consonant, or complex consonant
        - Accumulate characters (vowel markers, halant, other markers) until the next
          vowel/consonant/complex consonant/space is reached

        Args:
            text: Input text string in Devanagari

        Returns:
            List of tokens
        """
        if not text:
            return []

        # Step 0: Preprocess text - replace punctuations with spaces and normalize spaces
        text = self._preprocess_text(text)

        tokens = []
        i = 0

        while i < len(text):
            first_three_chars = text[i:i+3]
            char = text[i]

            # 1. space
            if char.isspace():
                tokens.append(" ")
                i += 1
                continue

            # 2. Check Complex consonant
            if first_three_chars in SyllableDataset.COMPLEX_CONSONANTS_SET:
                tokens.append(first_three_chars)
                i += 3
                continue

            # 3. check if char is vowel or consonant
            elif char in SyllableDataset.VOWELS_SET or char in SyllableDataset.CONSONANTS_SET:
                    tokens.append(char)
                    i += 1
                    continue

            # 4. Handle vowel markers, halant, and other markers (attach to previous token)
            elif char in SyllableDataset.ATTACHING_MARKERS:
                if tokens and not tokens[-1].isspace():
                    tokens[-1] += char
                else:
                    # Handle case where marker appears at beginning (shouldn't happen in valid text)
                    tokens.append(char)
                i += 1
                continue

            # Handle any other characters (numbers, invalid characters etc.)
            # todo: convert numbers to word in pre process? `SyllableDataset.NUMBERS?`
            if not self.remove_non_devanagari:
                tokens.append(char)
            i += 1

        return list(tokens)

    def encode(self, text: str) -> List[str]:
        """Alias for tokenize method"""
        return self.tokenize(text)

    def decode(self, tokens: List[str]) -> str:
        """
        Decode tokens back to text

        Args:
            tokens: List of syllabic tokens

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

if __name__ == "__main__":

        tokenizer = NepaliSyllabicTokenizer()
        print("व्यक्तित्वमा प्रभाव पर्ने: \t", tokenizer.tokenize("व्यक्तित्वमा प्रभाव पर्ने"))
        print("घाउ लागेको क्षेत्रमा: \t", tokenizer.tokenize("घाउ लागेको क्षेत्रमा"))
        print("क्रान्ति: \t", tokenizer.tokenize("क्रान्ति"))
        print("अन्तर्राष्ट्रिय: \t", tokenizer.tokenize("अन्तर्राष्ट्रिय"))
"""
# Output
व्यक्तित्वमा प्रभाव पर्ने:     ['व्', 'य', 'क्', 'ति', 'त्', 'व', 'मा', ' ', 'प्र', 'भा', 'व', ' ', 'प', 'र्', 'ने']
घाउ लागेको क्षेत्रमा:       ['घा', 'उ', ' ', 'ला', 'गे', 'को', ' ', 'क्षे', 'त्र', 'मा']
क्रान्ति:               ['क्रा', 'न्', 'ति']
"""