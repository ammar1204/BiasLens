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

    @staticmethod
    def analyze_patterns(text: str) -> Dict:
        """Comprehensive pattern analysis for Nigerian context"""
        text_lower = text.lower()

        # Check for trigger phrases
        trigger_matches = []
        for pattern in NigerianPatterns.NIGERIAN_TRIGGER_PHRASES:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            if matches:
                trigger_matches.extend(matches)

        # Check for clickbait patterns
        clickbait_matches = []
        for pattern in NigerianPatterns.CLICKBAIT_PATTERNS:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            if matches:
                clickbait_matches.extend(matches)

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

    @staticmethod
    def detect(text: str) -> Tuple[bool, Dict]:
        """Enhanced fake news detection with scoring"""
        fake_matches = []
        credibility_flags = []

        # Check for fake news patterns
        for pattern in FakeNewsDetector.FAKE_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                fake_matches.extend(matches)

        # Check for credibility red flags
        for pattern in FakeNewsDetector.CREDIBILITY_RED_FLAGS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                credibility_flags.extend(matches)

        # Calculate risk score
        total_words = len(text.split())
        fake_score = (len(fake_matches) / max(total_words, 1)) * 100
        credibility_score = (len(credibility_flags) / max(total_words, 1)) * 100

        # Determine overall risk
        is_suspicious = len(fake_matches) > 0 or len(credibility_flags) > 1

        # Risk level
        if fake_score > 5 or credibility_score > 3:
            risk_level = "high"
        elif fake_score > 2 or credibility_score > 1:
            risk_level = "medium"
        elif fake_score > 0 or credibility_score > 0:
            risk_level = "low"
        else:
            risk_level = "minimal"

        return is_suspicious, {
            "fake_matches": fake_matches,
            "credibility_flags": credibility_flags,
            "fake_score": round(fake_score, 2),
            "credibility_score": round(credibility_score, 2),
            "risk_level": risk_level,
            "total_flags": len(fake_matches) + len(credibility_flags)
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

    @staticmethod
    def analyze_virality(text: str) -> Dict:
        """Analyze viral manipulation patterns"""
        viral_matches = []

        for pattern in ViralityDetector.VIRAL_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                viral_matches.extend(matches)

        viral_score = (len(viral_matches) / max(len(text.split()), 1)) * 100

        return {
            "has_viral_patterns": len(viral_matches) > 0,
            "viral_matches": viral_matches,
            "viral_score": round(viral_score, 2),
            "manipulation_level": "high" if viral_score > 3 else "medium" if viral_score > 1 else "low"
        }