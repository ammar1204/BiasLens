import random
from .patterns import NigerianPatterns, FakeNewsDetector, ViralityDetector


class TrustScoreCalculator:
    DID_YOU_KNOW_TIPS = [
        "Verify information before sharing. Check multiple reputable sources to confirm a story's accuracy.",
        "Be wary of headlines designed to provoke strong emotions. They might prioritize clicks over facts.",
        "Look for bylines and author credentials. Anonymous sources can be a red flag for misinformation.",
        "Check the publication date. Old news can be re-shared out of context to mislead.",
        "Examine the 'About Us' page of a source to understand its mission, ownership, and potential biases.",
        "Distinguish between news reporting, opinion pieces, and sponsored content. Each has a different purpose.",
        "Cross-reference claims with fact-checking websites like Snopes, PolitiFact, or Africa Check.",
        "Be skeptical of content that claims to have 'secret' or 'exclusive' information without evidence.",
        "Consider the images and videos used. Are they original, or are they altered or taken from unrelated events?",
        "Understand that all sources can have some level of bias. Seek diverse perspectives to get a fuller picture.",
        "Pay attention to the language used. Loaded words, stereotypes, and generalizations can indicate bias.",
        "If a story sounds too good or too outrageous to be true, it often is. Investigate further.",
        "Support responsible journalism. Reliable news gathering requires resources and ethical standards.",
        "Media literacy is a key skill in the digital age. Continuously question and evaluate the information you consume.",
        "Look for corrections and clarifications. Reputable news organizations admit and fix their mistakes.",
        "Beware of echo chambers and filter bubbles. Actively seek out viewpoints that challenge your own.",
        "Check if statistical claims are backed by clear data sources and methodologies.",
        "Recognize that headlines don't always tell the full story. Read the article thoroughly.",
        "Be cautious with user-generated content (comments, social media posts) as it's often unverified.",
        "Understand the difference between correlation and causation when interpreting data or events."
    ]

    TRUST_THRESHOLDS = {
        'trusted': 70,
        'caution': 40,
        'risky': 0
    }

    @staticmethod
    def get_trust_indicator(score):
        """Get color-coded trust indicator"""
        if score >= TrustScoreCalculator.TRUST_THRESHOLDS['trusted']:
            return "🟢 Trusted"
        elif score >= TrustScoreCalculator.TRUST_THRESHOLDS['caution']:
            return "🟡 Caution"
        else:
            return "🔴 Risky"

    @staticmethod
    def get_detailed_trust_level(score):
        """Get more detailed trust categorization"""
        if score >= 85:
            return "highly_trusted"
        elif score >= 70:
            return "trusted"
        elif score >= 55:
            return "moderate_caution"
        elif score >= 40:
            return "high_caution"
        elif score >= 25:
            return "risky"
        else:
            return "highly_risky"

    @staticmethod
    def calculate(bias_score, emotion_score, sentiment_label, text,
                  emotion_data=None, sentiment_data=None, bias_data=None):
        """
        Enhanced trust score calculation using all available analysis data

        Args:
            bias_score: Legacy bias score (for backward compatibility)
            emotion_score: Legacy emotion score
            sentiment_label: Legacy sentiment label
            text: Original text
            emotion_data: Full emotion analysis dict (optional)
            sentiment_data: Full sentiment analysis dict (optional)
            bias_data: Full bias analysis dict (optional)
        """

        # Initialize score and tracking
        score = 100
        explanation = []
        risk_factors = []

        # Pattern Analysis
        nigerian_analysis = NigerianPatterns.analyze_patterns(text)
        fake_detected, fake_details = FakeNewsDetector.detect(text)
        viral_analysis = ViralityDetector.analyze_virality(text)

        # === BIAS SCORING ===
        if bias_data and 'flag' in bias_data:
            if bias_data['flag']:
                if 'High Confidence' in str(bias_data.get('label', '')):
                    score -= 35
                    explanation.append("High confidence bias detected in language patterns.")
                    risk_factors.append("high_bias")
                else:
                    score -= 20
                    explanation.append("Potential bias detected in language patterns.")
                    risk_factors.append("moderate_bias")

                # Add specific bias type to explanation
                bias_type_info = bias_data.get('type_analysis', {})
                detected_bias_type = bias_type_info.get('type')

                if detected_bias_type and detected_bias_type not in ['neutral', 'no bias', 'analysis_error', None]:
                    explanation.append(f"Dominant bias type identified: {detected_bias_type.replace('_', ' ').title()}.")
                elif detected_bias_type == 'neutral' or detected_bias_type == 'no bias':
                    explanation.append("Bias type analysis indicates neutrality.")
                # If 'analysis_error' or None, no specific type explanation is added for type
        else:
            # Fallback to legacy scoring
            if bias_score >= 0.8:
                score -= 30
                explanation.append("Text shows strong biased or one-sided language.")
                risk_factors.append("strong_bias")
            elif bias_score >= 0.6:
                score -= 20
                explanation.append("Text shows moderate bias.")
                risk_factors.append("moderate_bias")
            elif bias_score >= 0.4:
                score -= 10
                explanation.append("Text shows mild bias.")
                risk_factors.append("mild_bias")

        # === EMOTION SCORING ===
        if emotion_data:
            manipulation_risk = emotion_data.get('manipulation_risk', 'minimal')
            is_charged = emotion_data.get('is_emotionally_charged', False)

            if manipulation_risk == 'high':
                score -= 30
                explanation.append("Content uses highly manipulative emotional language.")
                risk_factors.append("emotional_manipulation")
            elif manipulation_risk == 'medium':
                score -= 20
                explanation.append("Content shows signs of emotional manipulation.")
                risk_factors.append("moderate_emotion")
            elif is_charged:
                score -= 15
                explanation.append("Content is emotionally charged.")
                risk_factors.append("emotional_content")
        else:
            # Fallback to legacy scoring
            if emotion_score >= 0.8:
                score -= 25
                explanation.append("Text is extremely emotionally charged.")
                risk_factors.append("extreme_emotion")
            elif emotion_score >= 0.6:
                score -= 15
                explanation.append("Text has strong emotional tone.")
                risk_factors.append("strong_emotion")
            elif emotion_score >= 0.4:
                score -= 8
                explanation.append("Text has mild emotional tone.")
                risk_factors.append("mild_emotion")

        # === SENTIMENT SCORING ===
        if sentiment_data:
            if sentiment_data.get('bias_indicator', False):
                score -= 15
                explanation.append("Sentiment analysis indicates potential bias.")
                risk_factors.append("sentiment_bias")

            if sentiment_data.get('is_polarized', False):
                score -= 12
                explanation.append("Content shows highly polarized sentiment.")
                risk_factors.append("polarized_content")

            polarization = sentiment_data.get('polarization_score', 0)
            if polarization > 0.7:
                score -= 8
                explanation.append("Content has divisive sentiment patterns.")
                risk_factors.append("divisive_sentiment")
        else:
            # Fallback to legacy scoring
            if sentiment_label == 'negative':
                score -= 10
                explanation.append("Text expresses a negative tone.")
                risk_factors.append("negative_sentiment")
            elif sentiment_label == 'positive':
                score -= 3
                explanation.append("Text expresses a positive tone.")

        # === PATTERN ANALYSIS ===
        if nigerian_analysis['has_triggers']:
            penalty = min(20, nigerian_analysis['trigger_score'] * 2)
            score -= penalty
            explanation.append("Contains Nigerian expressions commonly used in misleading content.")
            risk_factors.append("nigerian_triggers")

        if nigerian_analysis['has_clickbait']:
            penalty = min(15, nigerian_analysis['clickbait_score'] * 3)
            score -= penalty
            explanation.append("Contains clickbait patterns designed to attract clicks.")
            risk_factors.append("clickbait")

        # === FAKE NEWS PATTERNS ===
        if fake_detected:
            risk_level = fake_details.get('risk_level', 'medium')
            if risk_level == 'high':
                score -= 25
                explanation.append("High risk of fake news based on language patterns.")
                risk_factors.append("high_fake_risk")
            elif risk_level == 'medium':
                score -= 15
                explanation.append("Medium risk of fake news based on language patterns.")
                risk_factors.append("medium_fake_risk")
            else:
                score -= 8
                explanation.append("Some suspicious patterns detected.")
                risk_factors.append("low_fake_risk")

            # Add specific pattern mentions
            if fake_details.get('fake_matches'):
                top_matches = fake_details['fake_matches'][:3]  # Show top 3
                explanation.append(f"Suspicious phrases: {', '.join(set(top_matches))}")

        # === VIRAL MANIPULATION ===
        if viral_analysis['has_viral_patterns']:
            manipulation_level = viral_analysis.get('manipulation_level', 'low')
            if manipulation_level == 'high':
                score -= 20
                explanation.append("Contains patterns designed to manipulate viral sharing.")
                risk_factors.append("viral_manipulation")
            elif manipulation_level == 'medium':
                score -= 12
                explanation.append("Shows some viral manipulation tactics.")
                risk_factors.append("mild_viral_manipulation")

        # === FINAL ADJUSTMENTS ===
        # Bonus for neutral, well-balanced content
        if (len(risk_factors) == 0 and
                sentiment_label == 'neutral' and # This uses legacy sentiment_label
                (not emotion_data or emotion_data.get('manipulation_risk', 'minimal') == 'minimal' and not emotion_data.get('is_emotionally_charged', False)) and # Check new emotion_data if available
                (not bias_data or not bias_data.get('flag', False))): # Check new bias_data if available
            score += 5
            explanation.append("Content appears balanced and factual.")

        # Ensure score stays within bounds
        score = max(0, min(score, 100))

        # Generate indicator and trust level
        indicator = TrustScoreCalculator.get_trust_indicator(score)
        trust_level = TrustScoreCalculator.get_detailed_trust_level(score)

        # Select appropriate tip
        tip = TrustScoreCalculator._get_contextual_tip(risk_factors)

        # Generate summary
        summary = TrustScoreCalculator._generate_summary(score, risk_factors)

        return score, indicator, explanation, tip, {
            'trust_level': trust_level,
            'risk_factors': risk_factors,
            'summary': summary,
            'pattern_analysis': {
                'nigerian_patterns': nigerian_analysis,
                'fake_news_risk': fake_details if fake_detected else None,
                'viral_manipulation': viral_analysis if viral_analysis['has_viral_patterns'] else None
            }
        }

    @staticmethod
    def _get_contextual_tip(risk_factors):
        """Get tip based on detected risk factors"""
        contextual_tips = {
            'high_bias': "Examine if the content fairly represents different viewpoints or oversimplifies complex issues. Look for balanced reporting.",
            'emotional_manipulation': "Identify emotionally charged words. Question if the emotion is justified by evidence or used to cloud judgment.",
            'nigerian_triggers': "Local expressions can be used to make fake news seem more authentic and relatable.", # Kept as is
            'clickbait': "Clickbait headlines often exaggerate or omit crucial details. Compare headlines with article content critically.",
            'viral_manipulation': "Be skeptical of posts urging immediate sharing. Verify content before amplifying it, especially if it seems designed to go viral.",
            'fake_risk': "Verify information using the 'SIFT' method: Stop, Investigate the source, Find better coverage, Trace claims to the original context."
        }

        # Return tip based on highest priority risk factor
        # Order of check matters for priority
        priority_risks = [
            'high_fake_risk', 'medium_fake_risk', 'low_fake_risk', # Group fake_risk checks
            'high_bias', 'moderate_bias', 'strong_bias', # Group bias checks
            'emotional_manipulation', 'extreme_emotion', 'strong_emotion', # Group emotion checks
            'viral_manipulation', 'mild_viral_manipulation',
            'nigerian_triggers',
            'clickbait'
        ]

        for risk_key_prefix in priority_risks:
            # Map specific risk_factors (like 'high_fake_risk') to general contextual_tips keys (like 'fake_risk')
            mapped_tip_key = None
            if 'fake_risk' in risk_key_prefix: mapped_tip_key = 'fake_risk'
            elif 'bias' in risk_key_prefix: mapped_tip_key = 'high_bias' # Use the general 'high_bias' tip for all bias levels
            elif 'emotion' in risk_key_prefix: mapped_tip_key = 'emotional_manipulation' # Use general for all emotion levels
            elif 'viral' in risk_key_prefix: mapped_tip_key = 'viral_manipulation'
            elif 'nigerian' in risk_key_prefix: mapped_tip_key = 'nigerian_triggers'
            elif 'clickbait' in risk_key_prefix: mapped_tip_key = 'clickbait'

            if mapped_tip_key and any(rf.startswith(risk_key_prefix.split('_')[0]) for rf in risk_factors):
                 # Check if the specific risk_key_prefix (or its root) is present in risk_factors
                 if any(risk_key_prefix in rf_actual for rf_actual in risk_factors):
                    return contextual_tips.get(mapped_tip_key, random.choice(TrustScoreCalculator.DID_YOU_KNOW_TIPS))


        # Fallback if no specific contextual tip matches the detected risk factors
        return random.choice(TrustScoreCalculator.DID_YOU_KNOW_TIPS)

    @staticmethod
    def _generate_summary(score, risk_factors):
        """Generate human-readable summary"""
        if score >= 85:
            return "This content appears highly trustworthy with minimal bias or manipulation."
        elif score >= 70:
            return "This content appears generally trustworthy but exercise normal caution."
        elif score >= 55:
            return "This content shows some concerning patterns - verify from other sources."
        elif score >= 40:
            return "This content has multiple red flags - approach with significant caution."
        elif score >= 25:
            return "This content appears risky with several manipulation indicators."
        else:
            return "This content shows strong signs of bias, manipulation, or misinformation."