import re
from typing import Dict, Tuple


class NigerianPatterns:
    NIGERIAN_TRIGGER_PHRASES = [
        # Nigerian Pidgin expressions
        r"aswear", r"na them", r"dem wan kill us", r"nawa o", r"wetin be this",
        r"shey na joke", r"this is madness", r"see wetin dey happen",
        r"dem don finish us", r"na wa o", r"which kind country be this",

        # Political triggers
        r"this country is finished", r"government is lying", r"our leaders have failed us",
        r"politicians are thieves", r"dem no care about us", r"Nigeria don spoil finish",

        # Sensationalist patterns
        r"breaking[:\-]?", r"shocking truth", r"they don't want you to know",
        r"the real truth", r"hidden agenda", r"wake up nigeria",

        # Religious/ethnic triggers
        r"christian vs muslim", r"yoruba vs igbo", r"hausa vs", r"religious war",
        r"ethnic cleansing", r"genocide", r"targeted killing"
    ]

    CLICKBAIT_PATTERNS = [
        r"you won't believe", r"number \d+ will shock you", r"what happened next",
        r"see what \w+ did", r"this will amaze you", r"must see", r"viral video",
        r"gone wrong", r"you need to see this", r"incredible footage"
    ]

    # Combine and compile regex patterns for efficiency
    _COMPILED_NIGERIAN_TRIGGERS = re.compile(
        r'|'.join(f"(?:{p})" for p in NIGERIAN_TRIGGER_PHRASES),
        re.IGNORECASE
    )
    _COMPILED_CLICKBAIT_PATTERNS = re.compile(
        r'|'.join(f"(?:{p})" for p in CLICKBAIT_PATTERNS),
        re.IGNORECASE
    )

    @staticmethod
    def analyze_patterns(text: str) -> Dict:
        """Comprehensive pattern analysis for Nigerian context"""

        # Use compiled regex for trigger phrases
        trigger_matches = NigerianPatterns._COMPILED_NIGERIAN_TRIGGERS.findall(text)

        # Use compiled regex for clickbait patterns
        clickbait_matches = NigerianPatterns._COMPILED_CLICKBAIT_PATTERNS.findall(text)

        # Calculate scores
        trigger_score = len(trigger_matches) / max(len(text.split()), 1) * 100
        clickbait_score = len(clickbait_matches) / max(len(text.split()), 1) * 100

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
        """Legacy method - kept for backward compatibility"""
        result = NigerianPatterns.analyze_patterns(text)
        return result["has_triggers"] or result["has_clickbait"]


class FakeNewsDetector:
    FAKE_PATTERNS = [
        # Sensationalist words
        r"\bBreaking\b", r"\bShocking\b", r"\bRevealed\b", r"\bExposed\b",
        r"\bScandal\b", r"\bCollapse\b", r"\bTotal failure\b", r"\bMust watch\b",
        r"\bAgenda\b", r"\bHidden truth\b", r"\bCover[- ]?up\b",

        # Conspiracy patterns
        r"what they (don't|don't) want you to know", r"wake up nigeria",
        r"the truth (about|behind)", r"secret (meeting|plan|agenda)",
        r"they are hiding", r"mainstream media won't tell you",

        # Emotional manipulation
        r"you will cry", r"heartbreaking", r"devastating news",
        r"this will make you angry", r"prepare to be shocked"
    ]

    CREDIBILITY_RED_FLAGS = [
        # Suspicious sources
        r"according to sources", r"insider reveals", r"anonymous tip",
        r"leaked document", r"confidential source", r"whistleblower",

        # Vague attributions
        r"experts say", r"studies show", r"research proves",
        r"scientists confirm", r"doctors warn"  # without specific names
    ]

    _COMPILED_FAKE_PATTERNS = re.compile(
        r'|'.join(f"(?:{p})" for p in FAKE_PATTERNS),
        re.IGNORECASE
    )
    _COMPILED_CREDIBILITY_FLAGS = re.compile(
        r'|'.join(f"(?:{p})" for p in CREDIBILITY_RED_FLAGS),
        re.IGNORECASE
    )

    @staticmethod
    def detect(text: str) -> Tuple[bool, Dict]:
        """Enhanced fake news detection with scoring"""
        # Use compiled regex for fake news patterns
        # This can return List[Union[str, Tuple[str,...]]]
        raw_fake_matches_output = FakeNewsDetector._COMPILED_FAKE_PATTERNS.findall(text)

        processed_fake_matches = []
        if raw_fake_matches_output:
            for match_item in raw_fake_matches_output:
                actual_match_text = ""
                if isinstance(match_item, tuple):
                    # Find the first non-empty string in the tuple
                    actual_match_text = next((s for s in match_item if s), "")
                elif isinstance(match_item, str):
                    actual_match_text = match_item

                if actual_match_text:
                    processed_fake_matches.append(actual_match_text)

        # Use compiled regex for credibility red flags (this one correctly returns List[str])
        credibility_flags = FakeNewsDetector._COMPILED_CREDIBILITY_FLAGS.findall(text)

        # Calculate risk score
        total_words = len(text.split())
        # Use length of processed_fake_matches for calculations
        fake_score = (len(processed_fake_matches) / max(total_words, 1)) * 100 if total_words > 0 else 0
        credibility_score = (len(credibility_flags) / max(total_words, 1)) * 100 if total_words > 0 else 0

        # Determine overall risk using processed_fake_matches
        is_suspicious = len(processed_fake_matches) > 0 or len(credibility_flags) > 1

        # Risk level calculation also depends on the updated fake_score
        if fake_score > 5 or credibility_score > 3: # threshold for high risk based on density
            risk_level = "high"
        elif fake_score > 2 or credibility_score > 1: # threshold for medium risk
            risk_level = "medium"
        elif len(processed_fake_matches) > 0 or len(credibility_flags) > 0: # any match means at least low risk
            risk_level = "low"
        else:
            risk_level = "minimal"

        # If is_suspicious is True but risk_level is minimal (e.g. 1 credibility_flag and 0 fake_matches), adjust to low.
        if is_suspicious and risk_level == "minimal":
            risk_level = "low"


        return is_suspicious, {
            "fake_matches": processed_fake_matches, # Use the processed list of strings
            "credibility_flags": credibility_flags,
            "fake_score": round(fake_score, 2),
            "credibility_score": round(credibility_score, 2),
            "risk_level": risk_level,
            "total_flags": len(processed_fake_matches) + len(credibility_flags) # Use length of processed list
        }


class ViralityDetector:
    """Detects patterns that make content go viral (often used in fake news)"""

    VIRAL_PATTERNS = [
        # Urgency patterns
        r"share (this|now|before)", r"retweet if you", r"tag your friends",
        r"urgent", r"time sensitive", r"delete this", r"censored",

        # FOMO (Fear of Missing Out)
        r"limited time", r"won't last long", r"before it's too late",
        r"last chance", r"final warning", r"don't miss this",

        # Social proof manipulation
        r"everyone is talking about", r"going viral", r"trending now",
        r"millions have seen", r"shared \d+ times"
    ]

    _COMPILED_VIRAL_PATTERNS = re.compile(
        r'|'.join(f"(?:{p})" for p in VIRAL_PATTERNS),
        re.IGNORECASE
    )

    @staticmethod
    def analyze_virality(text: str) -> Dict:
        """Analyze viral manipulation patterns"""
        # Use compiled regex for viral patterns
        viral_matches = ViralityDetector._COMPILED_VIRAL_PATTERNS.findall(text)

        viral_score = (len(viral_matches) / max(len(text.split()), 1)) * 100

        return {
            "has_viral_patterns": len(viral_matches) > 0,
            "viral_matches": viral_matches,
            "viral_score": round(viral_score, 2),
            "manipulation_level": "high" if viral_score > 3 else "medium" if viral_score > 1 else "low"
        }