"""
Pattern Detection Module for BiasLens.

This module provides classes for identifying specific textual patterns that may
indicate misinformation, clickbait, regional language use, or attempts to create
virality. It uses regular expressions for pattern matching.
"""
import re
from typing import Dict, Tuple, List, Pattern, Any


class NigerianPatterns:
    """
    Identifies Nigerian Pidgin English trigger phrases and common clickbait patterns.

    These patterns can be indicative of content tailored for a Nigerian audience.
    In some contexts, particularly when combined with other indicators, they might
    also be associated with misinformation or engagement tactics. All matching is
    case-insensitive.
    """

    # Categories of Nigerian trigger phrases:
    # - Common Pidgin expressions reflecting colloquial speech.
    # - Political commentary or slogans often seen in Nigerian social media.
    # - Sensationalist phrases used to grab attention.
    # - Terms related to religious or ethnic tensions (use with caution, context is key).
    NIGERIAN_TRIGGER_PHRASES: List[str] = [
        # Nigerian Pidgin expressions
        r"aswear", r"na them", r"dem wan kill us", r"nawa o", r"wetin be this",
        r"shey na joke", r"this is madness", r"see wetin dey happen",
        r"dem don finish us", r"na wa o", r"which kind country be this",

        # Political triggers
        r"this country is finished", r"government is lying", r"our leaders have failed us",
        "politicians are thieves", r"dem no care about us", r"Nigeria don spoil finish",

        # Sensationalist patterns
        r"breaking[:\-]?", r"shocking truth", r"they don't want you to know",
        r"the real truth", r"hidden agenda", r"wake up nigeria",

        # Religious/ethnic triggers (sensitive, context-dependent)
        r"christian vs muslim", r"yoruba vs igbo", r"hausa vs", r"religious war",
        r"ethnic cleansing", r"genocide", r"targeted killing"
    ]

    # Common clickbait phrases
    CLICKBAIT_PATTERNS: List[str] = [
        r"you won't believe", r"number \d+ will shock you", r"what happened next",
        r"see what \w+ did", r"this will amaze you", r"must see", r"viral video",
        r"gone wrong", r"you need to see this", r"incredible footage"
    ]

    # Pre-compile regex patterns for efficiency.
    # Using non-capturing groups (?:...) for individual patterns within the alternation.
    _COMPILED_NIGERIAN_TRIGGERS: Pattern[str] = re.compile(
        r'|'.join(f"(?:{p})" for p in NIGERIAN_TRIGGER_PHRASES),
        re.IGNORECASE
    )
    _COMPILED_CLICKBAIT_PATTERNS: Pattern[str] = re.compile(
        r'|'.join(f"(?:{p})" for p in CLICKBAIT_PATTERNS),
        re.IGNORECASE
    )

    @staticmethod
    def analyze_patterns(text: str) -> Dict[str, Any]:
        """
        Analyzes text for Nigerian trigger phrases and clickbait patterns.

        Args:
            text (str): The text to analyze.

        Returns:
            Dict[str, Any]: A dictionary containing the analysis results:
                - "has_triggers" (bool): True if Nigerian trigger phrases are found.
                - "trigger_matches" (List[str]): List of matched trigger phrases.
                - "trigger_score" (float): Score based on frequency of trigger phrases,
                                           normalized by text length (matches per 100 words, effectively).
                - "has_clickbait" (bool): True if clickbait patterns are found.
                - "clickbait_matches" (List[str]): List of matched clickbait phrases.
                - "clickbait_score" (float): Score based on frequency of clickbait phrases,
                                             normalized by text length.
                - "total_flags" (int): Total number of matched trigger and clickbait phrases.
        """
        # Find all non-overlapping matches for Nigerian trigger phrases
        trigger_matches: List[str] = NigerianPatterns._COMPILED_NIGERIAN_TRIGGERS.findall(text)

        # Find all non-overlapping matches for clickbait patterns
        clickbait_matches: List[str] = NigerianPatterns._COMPILED_CLICKBAIT_PATTERNS.findall(text)

        # Calculate scores: number of matches per word, scaled to a percentage-like figure.
        # Using max(len(text.split()), 1) to avoid division by zero for empty text.
        num_words = max(len(text.split()), 1)
        trigger_score = (len(trigger_matches) / num_words) * 100
        clickbait_score = (len(clickbait_matches) / num_words) * 100

        return {
            "has_triggers": len(trigger_matches) > 0,
            "trigger_matches": trigger_matches,
            "trigger_score": round(trigger_score, 2),
            "has_clickbait": len(clickbait_matches) > 0,
            "clickbait_matches": clickbait_matches,
            "clickbait_score": round(clickbait_score, 2),
            "total_flags": len(trigger_matches) + len(clickbait_matches)
        }

    @staticmethod
    def has_misleading_pattern(text: str) -> bool:
        """
        Legacy method to quickly check for any misleading patterns.

        Kept for backward compatibility. Prefer `analyze_patterns` for detailed results.

        Args:
            text (str): The text to analyze.

        Returns:
            bool: True if any Nigerian trigger or clickbait pattern is found.
        """
        result = NigerianPatterns.analyze_patterns(text)
        return result["has_triggers"] or result["has_clickbait"]


class FakeNewsDetector:
    """
    Identifies textual patterns commonly associated with fake news or misinformation.

    This includes sensationalist language, conspiracy-related phrases, emotionally manipulative
    expressions, and references to vague or unverifiable sources.
    Matching is case-insensitive.
    """

    # Patterns often found in fake news headlines or content:
    # - Sensationalist keywords designed to shock or alarm.
    # - Phrases hinting at conspiracies or hidden information.
    # - Language intended to evoke strong emotional responses.
    FAKE_PATTERNS: List[str] = [
        # Sensationalist words
        r"\bBreaking\b", r"\bShocking\b", r"\bRevealed\b", r"\bExposed\b",
        r"\bScandal\b", r"\bCollapse\b", r"\bTotal failure\b", r"\bMust watch\b",
        r"\bAgenda\b", r"\bHidden truth\b", r"\bCover[- ]?up\b", # Matches "cover-up" or "cover up"

        # Conspiracy patterns
        r"what they (don't|do not) want you to know", r"wake up nigeria", # "don't" or "do not"
        r"the truth (about|behind)", r"secret (meeting|plan|agenda)",
        r"they are hiding", r"mainstream media won't tell you",

        # Emotional manipulation
        r"you will cry", r"heartbreaking", r"devastating news",
        r"this will make you angry", r"prepare to be shocked"
    ]

    # Patterns indicating reliance on questionable or unverifiable sources:
    # - References to anonymous or vague sources.
    # - Broad claims without specific attribution.
    CREDIBILITY_RED_FLAGS: List[str] = [
        # Suspicious sources
        r"according to sources", r"insider reveals", r"anonymous tip",
        r"leaked document", r"confidential source", r"whistleblower reports", # Added "reports"

        # Vague attributions
        r"experts say", r"studies show", r"research proves",
        r"scientists confirm", r"doctors warn"  # Often used without naming specific experts/studies
    ]

    # Pre-compiled regex for efficiency
    _COMPILED_FAKE_PATTERNS: Pattern[str] = re.compile(
        r'|'.join(f"(?:{p})" for p in FAKE_PATTERNS),
        re.IGNORECASE
    )
    _COMPILED_CREDIBILITY_FLAGS: Pattern[str] = re.compile(
        r'|'.join(f"(?:{p})" for p in CREDIBILITY_RED_FLAGS),
        re.IGNORECASE
    )

    @staticmethod
    def detect(text: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Detects fake news patterns and credibility red flags in text, providing a risk assessment.

        Args:
            text (str): The text to analyze.

        Returns:
            Tuple[bool, Dict[str, Any]]:
                - The first element (bool) is True if the text is deemed suspicious
                  (based on pattern counts).
                - The second element is a dictionary with detailed analysis:
                    - "fake_matches" (List[str]): Matched fake news patterns.
                    - "credibility_flags" (List[str]): Matched credibility red flags.
                    - "fake_score" (float): Score for fake news patterns.
                    - "credibility_score" (float): Score for credibility red flags.
                    - "risk_level" (str): Overall risk assessment ("high", "medium", "low", "minimal").
                    - "total_flags" (int): Total number of matched patterns and flags.
        """
        fake_matches: List[str] = FakeNewsDetector._COMPILED_FAKE_PATTERNS.findall(text)
        credibility_flags: List[str] = FakeNewsDetector._COMPILED_CREDIBILITY_FLAGS.findall(text)

        total_words = max(len(text.split()), 1)
        # Scores represent the density of flagged patterns per 100 words.
        fake_score = (len(fake_matches) / total_words) * 100
        credibility_score = (len(credibility_flags) / total_words) * 100

        # Determine overall suspicion: any fake match or more than one credibility flag.
        # The threshold for credibility_flags (e.g., > 1) can be tuned.
        is_suspicious = len(fake_matches) > 0 or len(credibility_flags) > 1

        # Determine qualitative risk level based on scores.
        # Thresholds are heuristic and can be adjusted.
        if fake_score > 5.0 or credibility_score > 3.0: # High density of fake patterns or several credibility issues
            risk_level = "high"
        elif fake_score > 2.0 or credibility_score > 1.0: # Moderate density
            risk_level = "medium"
        elif fake_score > 0 or credibility_score > 0: # Any pattern found
            risk_level = "low"
        else:
            risk_level = "minimal" # No specific patterns detected

        return is_suspicious, {
            "fake_matches": fake_matches,
            "credibility_flags": credibility_flags,
            "fake_score": round(fake_score, 2),
            "credibility_score": round(credibility_score, 2),
            "risk_level": risk_level,
            "total_flags": len(fake_matches) + len(credibility_flags)
        }


class ViralityDetector:
    """
    Detects linguistic patterns designed to encourage sharing or create urgency/FOMO.

    These patterns are often employed in content aiming for rapid, widespread
    dissemination (virality), which can sometimes be associated with manipulative
    or low-quality information. Matching is case-insensitive.
    """

    # Patterns related to:
    # - Urgency or direct calls to share/engage.
    # - Fear Of Missing Out (FOMO) tactics.
    # - Manipulative claims of social proof or trending status.
    VIRAL_PATTERNS: List[str] = [
        # Urgency patterns / Calls to action
        r"share (this|now|before it's removed)", r"retweet if you", r"tag your friends", # Added "before it's removed"
        r"\burgent\b", r"time sensitive", r"\bdelete this\b", r"\bcensored\b",

        # FOMO (Fear of Missing Out)
        r"limited time offer", r"won't last long", r"before it's too late", # Added "offer"
        r"last chance", r"final warning", r"don't miss this opportunity", # Added "opportunity"

        # Social proof manipulation
        r"everyone is talking about this", r"going viral now", r"trending across the nation", # Made more specific
        r"millions have already seen", r"shared over \d+ times" # More specific "over X times"
    ]

    # Pre-compiled regex for efficiency
    _COMPILED_VIRAL_PATTERNS: Pattern[str] = re.compile(
        r'|'.join(f"(?:{p})" for p in VIRAL_PATTERNS),
        re.IGNORECASE
    )

    @staticmethod
    def analyze_virality(text: str) -> Dict[str, Any]:
        """
        Analyzes text for patterns indicative of attempts to create virality.

        Args:
            text (str): The text to analyze.

        Returns:
            Dict[str, Any]: A dictionary containing the virality analysis:
                - "has_viral_patterns" (bool): True if viral patterns are found.
                - "viral_matches" (List[str]): List of matched viral patterns.
                - "viral_score" (float): Score based on frequency of viral patterns,
                                         normalized by text length.
                - "manipulation_level" (str): Assessed level of viral manipulation cues
                                              ("high", "medium", "low").
        """
        viral_matches: List[str] = ViralityDetector._COMPILED_VIRAL_PATTERNS.findall(text)

        total_words = max(len(text.split()), 1)
        # Score represents the density of viral patterns per 100 words.
        viral_score = (len(viral_matches) / total_words) * 100

        # Determine qualitative manipulation level based on the score.
        # Thresholds are heuristic.
        if viral_score > 3.0: # High density of viral cues
            manipulation_level = "high"
        elif viral_score > 1.0: # Moderate density
            manipulation_level = "medium"
        else: # Low or no cues
            manipulation_level = "low"
            if not viral_matches : manipulation_level = "minimal"


        return {
            "has_viral_patterns": len(viral_matches) > 0,
            "viral_matches": viral_matches,
            "viral_score": round(viral_score, 2),
            "manipulation_level": manipulation_level
        }