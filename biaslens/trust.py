"""
Trust Score Calculation Module for BiasLens.

This module provides the `TrustScoreCalculator` class, which is responsible for
synthesizing various analytical signals (from bias detection, emotion analysis,
sentiment analysis, and pattern matching) into a single, interpretable trust score.
The score aims to quantify the perceived trustworthiness of a piece of text,
also providing explanations, actionable tips, and a qualitative summary.

All methods in this class are static, meaning it's used as a utility class
without needing to be instantiated.
"""
import random
from typing import Dict, Any, Tuple, List, Optional # Added Optional for type hinting
from .patterns import NigerianPatterns, FakeNewsDetector, ViralityDetector


class TrustScoreCalculator:
    """
    A static utility class to calculate a trust score for a given text based on
    various analytical inputs.

    The calculation starts with a base score and applies penalties or bonuses
    based on detected bias, emotional tone, sentiment polarity, and specific
    textual patterns associated with misinformation or manipulation.
    """

    # General media literacy tips, one of which can be selected if no specific contextual tip applies.
    DID_YOU_KNOW_TIPS: List[str] = [
        "Fake news often uses words like 'BREAKING' or 'SHOCKING' to create urgency.",
        "Subtle bias can be hidden in adjectives and tone, not just facts.",
        "Emotional posts get more shares—even if they're false.",
        "Sensational headlines are more likely to spread misinformation.",
        "Repetition of a lie can make people believe it—even without proof.",
        "Manipulative language often appeals to fear, anger, or patriotism.",
        "Nigerian Pidgin phrases like 'aswear' or 'nawa o' are often used to make false news seem relatable.",
        "Articles without specific sources or dates are usually less reliable.",
        "Content that asks you to 'share before it's deleted' is often manipulative.",
        "Real news rarely needs excessive exclamation marks or ALL CAPS.",
        "If something sounds too shocking to be true, verify it from multiple sources.",
        "Biased content often presents only one side of a complex issue."
    ]

    # Defines score thresholds for different qualitative trust indicators.
    TRUST_THRESHOLDS: Dict[str, int] = {
        'trusted': 70,  # Scores >= 70 are considered "Trusted"
        'caution': 40,  # Scores >= 40 but < 70 are "Caution"
        'risky': 0      # Scores < 40 are "Risky"
    }

    @staticmethod
    def get_trust_indicator(score: float) -> str:
        """
        Maps a numerical trust score to a color-coded qualitative trust indicator.

        Args:
            score (float): The numerical trust score (0-100).

        Returns:
            str: A string representing the trust indicator (e.g., "🟢 Trusted").
        """
        if score >= TrustScoreCalculator.TRUST_THRESHOLDS['trusted']:
            return "🟢 Trusted"
        elif score >= TrustScoreCalculator.TRUST_THRESHOLDS['caution']:
            return "🟡 Caution"
        else:
            return "🔴 Risky"

    @staticmethod
    def get_detailed_trust_level(score: float) -> str:
        """
        Provides a more granular qualitative categorization of the trust score.

        Args:
            score (float): The numerical trust score (0-100).

        Returns:
            str: A string describing the detailed trust level (e.g., "highly_trusted").
        """
        if score >= 85:
            return "highly_trusted"
        elif score >= 70: # 70-84
            return "trusted"
        elif score >= 55: # 55-69
            return "moderate_caution"
        elif score >= 40: # 40-54
            return "high_caution"
        elif score >= 25: # 25-39
            return "risky"
        else: # 0-24
            return "highly_risky"

    @staticmethod
    def calculate(
        bias_score: float, # Legacy bias score
        emotion_score: float, # Legacy emotion score
        sentiment_label: str, # Legacy sentiment label
        text: str,
        emotion_data: Optional[Dict[str, Any]] = None,
        sentiment_data: Optional[Dict[str, Any]] = None,
        bias_data: Optional[Dict[str, Any]] = None
    ) -> Tuple[int, str, List[str], str, Dict[str, Any]]:
        """
        Calculates an enhanced trust score by aggregating various analysis results.

        The score starts at 100 and penalties are applied based on detected issues.

        Args:
            bias_score (float): Legacy bias score (0.0-1.0), used if `bias_data` is not provided.
            emotion_score (float): Legacy emotion score (0.0-1.0), used if `emotion_data` is not provided.
            sentiment_label (str): Legacy sentiment label ("positive", "negative", "neutral"),
                                   used if `sentiment_data` is not provided.
            text (str): The original text being analyzed, used for pattern matching.
            emotion_data (Optional[Dict[str, Any]]): Full analysis result from `EmotionClassifier`.
                                                     Expected keys: 'manipulation_risk', 'is_emotionally_charged'.
            sentiment_data (Optional[Dict[str, Any]]): Full analysis result from `SentimentAnalyzer`.
                                                       Expected keys: 'bias_indicator', 'is_polarized', 'polarization_score'.
            bias_data (Optional[Dict[str, Any]]): Full analysis result from `BiasDetector`/`BiasTypeClassifier`.
                                                  Expected keys: 'flag', 'label'.

        Returns:
            Tuple[int, str, List[str], str, Dict[str, Any]]: A tuple containing:
                - score (int): The calculated trust score (0-100).
                - indicator (str): A qualitative trust indicator (e.g., "🟢 Trusted").
                - explanation (List[str]): A list of strings explaining the factors that influenced the score.
                - tip (str): An actionable media literacy tip.
                - extras (Dict[str, Any]): A dictionary with additional details:
                    - 'trust_level' (str): Detailed qualitative trust level.
                    - 'risk_factors' (List[str]): Keywords for risks identified.
                    - 'summary' (str): A concise summary statement.
                    - 'pattern_analysis' (Dict): Results from pattern detectors.
        """

        # Initialize score at 100 (maximum trust) and lists for explanations/risks.
        current_score: float = 100.0
        explanation_list: List[str] = []
        identified_risk_factors: List[str] = []

        # Perform pattern analysis directly on the text.
        # These analyses look for predefined textual red flags.
        nigerian_pattern_analysis = NigerianPatterns.analyze_patterns(text)
        is_fake_news_detected, fake_news_details = FakeNewsDetector.detect(text)
        virality_pattern_analysis = ViralityDetector.analyze_virality(text)

        # === BIAS SCORING ===
        # Penalize based on bias detection results. Stronger bias incurs a larger penalty.
        if bias_data and 'flag' in bias_data: # Use detailed bias data if available
            if bias_data['flag']: # If bias is flagged
                if 'High Confidence' in str(bias_data.get('label', '')): # Check for high confidence bias
                    current_score -= 35
                    explanation_list.append("High confidence bias detected in language patterns.")
                    identified_risk_factors.append("high_bias_detected")
                else: # Moderate or general bias
                    current_score -= 20
                    explanation_list.append("Potential bias detected in language patterns.")
                    identified_risk_factors.append("moderate_bias_detected")
        else: # Fallback to legacy bias_score if detailed data is missing
            if bias_score >= 0.8: # High legacy bias score
                current_score -= 30
                explanation_list.append("Text shows strong biased or one-sided language (legacy score).")
                identified_risk_factors.append("strong_legacy_bias")
            elif bias_score >= 0.6: # Moderate legacy bias score
                current_score -= 20
                explanation_list.append("Text shows moderate bias (legacy score).")
                identified_risk_factors.append("moderate_legacy_bias")
            elif bias_score >= 0.4: # Mild legacy bias score
                current_score -= 10
                explanation_list.append("Text shows mild bias (legacy score).")
                identified_risk_factors.append("mild_legacy_bias")

        # === EMOTION SCORING ===
        # Penalize for manipulative or overly charged emotional language.
        if emotion_data: # Use detailed emotion data
            manipulation_risk = emotion_data.get('manipulation_risk', 'minimal')
            is_emotionally_charged = emotion_data.get('is_emotionally_charged', False)

            if manipulation_risk == 'high':
                current_score -= 30
                explanation_list.append("Content uses highly manipulative emotional language.")
                identified_risk_factors.append("high_emotional_manipulation")
            elif manipulation_risk == 'medium':
                current_score -= 20
                explanation_list.append("Content shows signs of emotional manipulation.")
                identified_risk_factors.append("medium_emotional_manipulation")
            elif is_emotionally_charged: # If charged but not overtly manipulative
                current_score -= 15
                explanation_list.append("Content is significantly emotionally charged.")
                identified_risk_factors.append("emotionally_charged_content")
        else: # Fallback to legacy emotion_score
            if emotion_score >= 0.8: # Extremely emotional
                current_score -= 25
                explanation_list.append("Text is extremely emotionally charged (legacy score).")
                identified_risk_factors.append("extreme_legacy_emotion")
            elif emotion_score >= 0.6: # Strongly emotional
                current_score -= 15
                explanation_list.append("Text has strong emotional tone (legacy score).")
                identified_risk_factors.append("strong_legacy_emotion")
            elif emotion_score >= 0.4: # Mildly emotional
                current_score -= 8
                explanation_list.append("Text has mild emotional tone (legacy score).")
                identified_risk_factors.append("mild_legacy_emotion")

        # === SENTIMENT SCORING ===
        # Penalize for sentiment patterns that might indicate bias or polarization.
        if sentiment_data: # Use detailed sentiment data
            if sentiment_data.get('bias_indicator', False): # Specific flag from sentiment analysis
                current_score -= 15
                explanation_list.append("Sentiment analysis indicates potential bias in tone or framing.")
                identified_risk_factors.append("sentiment_shows_bias")

            if sentiment_data.get('is_polarized', False): # Highly polarized sentiment
                current_score -= 12
                explanation_list.append("Content shows highly polarized (extreme positive/negative) sentiment.")
                identified_risk_factors.append("polarized_sentiment")

            # Penalize for divisive sentiment (strong positive vs. strong negative)
            polarization_value = sentiment_data.get('polarization_score', 0)
            if polarization_value > 0.7: # High difference between positive and negative scores
                current_score -= 8
                explanation_list.append("Content has divisive sentiment patterns (strong positive vs. negative).")
                identified_risk_factors.append("divisive_sentiment")
        else: # Fallback to legacy sentiment_label
            if sentiment_label == 'negative':
                current_score -= 10
                explanation_list.append("Text expresses a negative tone (legacy).")
                identified_risk_factors.append("negative_legacy_sentiment")
            elif sentiment_label == 'positive': # Slight penalty for overly positive if not clearly neutral/factual
                current_score -= 3
                explanation_list.append("Text expresses a positive tone (legacy).")
                # No specific risk factor for just "positive" legacy unless very polarized.

        # === PATTERN ANALYSIS PENALTIES ===
        # Penalize for Nigerian-specific trigger phrases if their density is high.
        if nigerian_pattern_analysis['has_triggers']:
            # Penalty scales with trigger_score, capped at 20.
            # nigerian_analysis['trigger_score'] is matches per 100 words.
            penalty = min(20, nigerian_pattern_analysis['trigger_score'] * 0.5) # Adjusted multiplier
            current_score -= penalty
            explanation_list.append("Contains Nigerian expressions sometimes found in misleading local content.")
            identified_risk_factors.append("nigerian_trigger_phrases")

        # Penalize for clickbait patterns.
        if nigerian_pattern_analysis['has_clickbait']:
            penalty = min(15, nigerian_pattern_analysis['clickbait_score'] * 0.75) # Adjusted multiplier
            current_score -= penalty
            explanation_list.append("Contains clickbait patterns designed to attract clicks misleadingly.")
            identified_risk_factors.append("clickbait_patterns")

        # Penalize based on fake news pattern detection.
        if is_fake_news_detected:
            risk_level = fake_news_details.get('risk_level', 'medium')
            if risk_level == 'high':
                current_score -= 25
                explanation_list.append("High risk of fake news based on detected language patterns.")
                identified_risk_factors.append("high_fake_news_risk")
            elif risk_level == 'medium':
                current_score -= 15
                explanation_list.append("Medium risk of fake news based on detected language patterns.")
                identified_risk_factors.append("medium_fake_news_risk")
            else: # Low risk
                current_score -= 8
                explanation_list.append("Some suspicious textual patterns detected (low fake news risk).")
                identified_risk_factors.append("low_fake_news_risk")

            # Add specific matched fake news phrases to explanation for transparency
            if fake_news_details.get('fake_matches'):
                top_matches = list(set(fake_news_details['fake_matches']))[:2]  # Show top 2 unique matches
                if top_matches:
                    explanation_list.append(f"Suspicious phrases found: '{', '.join(top_matches)}'.")

        # Penalize for viral manipulation patterns.
        if virality_pattern_analysis['has_viral_patterns']:
            manipulation_level = virality_pattern_analysis.get('manipulation_level', 'low')
            if manipulation_level == 'high':
                current_score -= 20
                explanation_list.append("Contains patterns designed to manipulate viral sharing (high risk).")
                identified_risk_factors.append("high_viral_manipulation")
            elif manipulation_level == 'medium':
                current_score -= 12
                explanation_list.append("Shows some viral manipulation tactics (medium risk).")
                identified_risk_factors.append("medium_viral_manipulation")
            # Low risk patterns might not warrant a penalty unless other factors are present.

        # === FINAL ADJUSTMENTS ===
        # Small bonus if content appears very neutral and no risk factors were triggered.
        if not identified_risk_factors and \
           ((sentiment_data and sentiment_data.get('label') == 'neutral' and sentiment_data.get('confidence', 0) > 0.7) or \
            (not sentiment_data and sentiment_label == 'neutral')) and \
           ((emotion_data and not emotion_data.get('is_emotionally_charged', True) and emotion_data.get('confidence', 0) > 0.5) or \
            (not emotion_data and emotion_score < 0.3)):
            current_score += 5 # Max 100
            explanation_list.append("Content appears balanced and factual, contributing positively to trust.")

        # Ensure the score is within the 0-100 bounds.
        final_score = int(max(0, min(current_score, 100)))

        # Get qualitative descriptors for the score.
        trust_indicator = TrustScoreCalculator.get_trust_indicator(final_score)
        detailed_trust_level = TrustScoreCalculator.get_detailed_trust_level(final_score)

        # Select a relevant tip.
        contextual_tip = TrustScoreCalculator._get_contextual_tip(identified_risk_factors)

        # Generate a summary statement.
        trust_summary = TrustScoreCalculator._generate_summary(final_score, identified_risk_factors)

        if not explanation_list: # If no penalties applied
            explanation_list.append("Analysis found no significant indicators of bias or manipulation.")


        return final_score, trust_indicator, explanation_list, contextual_tip, {
            'trust_level': detailed_trust_level,
            'risk_factors': identified_risk_factors,
            'summary': trust_summary,
            'pattern_analysis': { # Include raw pattern data for transparency or further use
                'nigerian_patterns': nigerian_pattern_analysis,
                'fake_news_risk': fake_news_details if is_fake_news_detected else {"risk_level": "minimal", "total_flags": 0},
                'viral_manipulation': virality_pattern_analysis if virality_pattern_analysis['has_viral_patterns'] else {"manipulation_level": "minimal", "total_flags": 0}
            }
        }

    @staticmethod
    def _get_contextual_tip(risk_factors: List[str]) -> str:
        """
        Selects a relevant media literacy tip based on detected risk factors.

        Prioritizes tips for more severe or common risks. If no specific risks
        match predefined categories, a random general tip is chosen.

        Args:
            risk_factors (List[str]): A list of keywords for risks identified
                                      during the trust score calculation.

        Returns:
            str: A contextual or random media literacy tip.
        """
        # Tips mapped to risk factor keywords (or prefixes).
        contextual_tips_map: Dict[str, str] = {
            'high_bias': "Always check if an article presents multiple perspectives on controversial topics.",
            'emotional_manipulation': "Be extra cautious of content that makes you feel strong emotions like anger or fear.",
            'nigerian_triggers': "Local expressions can be used to make fake news seem more authentic and relatable.",
            'clickbait': "Headlines designed to get clicks often don't match the actual content of the article.",
            'viral_manipulation': "Content asking you to share urgently is often trying to spread misinformation quickly.",
            'fake_news_risk': "Look for specific dates, sources, and verifiable facts in news articles.",
            'polarized': "Highly polarized content may oversimplify complex issues; seek out neutral viewpoints."
            # Add more tips for other risk_factors like 'sentiment_shows_bias', 'divisive_sentiment'
        }

        # Priority order for checking risk factors and selecting a tip.
        priority_risks = [
            'high_bias_detected', 'high_emotional_manipulation', 'high_viral_manipulation', 'high_fake_news_risk',
            'moderate_bias_detected', 'medium_emotional_manipulation', 'medium_viral_manipulation', 'medium_fake_news_risk',
            'polarized_sentiment', 'nigerian_trigger_phrases', 'clickbait_patterns',
            'sentiment_shows_bias' # General sentiment bias
        ]

        for risk_key_prefix in priority_risks:
            # Check if any identified risk factor starts with the current priority prefix
            for identified_risk in risk_factors:
                if identified_risk.startswith(risk_key_prefix.split('_')[0]): # Match general category like "high_bias"
                    # Attempt to find a tip for the specific risk factor or its general category
                    if risk_key_prefix in contextual_tips_map:
                        return contextual_tips_map[risk_key_prefix]
                    # Fallback to general category if specific sub-category tip isn't defined
                    general_risk_category = "_".join(risk_key_prefix.split('_')[:1]) # e.g. "high_bias" -> "high" - needs better mapping
                    # This part needs a better mapping from identified_risk_factors to contextual_tips_map keys.
                    # For now, let's try a simpler match on the main part of the risk factor.
                    for tip_key, tip_text in contextual_tips_map.items():
                        if tip_key in identified_risk:
                            return tip_text

        # If no specific contextual tip is found after checking priority list, return a random general tip.
        return random.choice(TrustScoreCalculator.DID_YOU_KNOW_TIPS)

    @staticmethod
    def _generate_summary(score: int, risk_factors: List[str]) -> str:
        """
        Generates a concise, human-readable summary statement based on the trust score.
        The `risk_factors` argument is available for future enhancements where the
        summary could be more dynamic based on specific risks, but currently, it's
        primarily score-driven.

        Args:
            score (int): The final calculated trust score (0-100).
            risk_factors (List[str]): Detected risk factors (currently unused in this method).

        Returns:
            str: A summary statement reflecting the trust level.
        """
        # Score-driven summary messages.
        if score >= 85:
            return "This content appears highly trustworthy with minimal indications of bias or manipulation."
        elif score >= 70: # 70-84
            return "This content appears generally trustworthy. Standard critical evaluation is advised."
        elif score >= 55: # 55-69
            return "This content shows some concerning patterns. It's advisable to verify information from other reputable sources."
        elif score >= 40: # 40-54
            return "This content has multiple red flags for potential bias or manipulation. Approach with significant caution."
        elif score >= 25: # 25-39
            return "This content appears risky, with several indicators of manipulation or unreliable information."
        else: # 0-24
            return "This content shows strong signs of bias, manipulation, or potential misinformation. Extreme caution is advised."