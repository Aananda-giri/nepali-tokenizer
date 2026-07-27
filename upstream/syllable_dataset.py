"""
Syllable Dataset Generator for Nepali Devanagari Script
Generates all valid syllables based on Devanagari grammar rules
"""

from typing import Set


class SyllableDataset:
    """Generate and manage Nepali syllable dataset based on Devanagari grammar"""
    
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
