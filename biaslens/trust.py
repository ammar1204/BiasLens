import random
import math
from typing import Dict, List, Tuple, Optional
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

    # Improved thresholds with more granular levels
    TRUST_THRESHOLDS = {
        'highly_trusted': 85,
        'trusted': 70,
        'moderate_caution': 55,
        'high_caution': 40,
        'risky': 25,
        'highly_risky': 0
    }

    # Scoring weights for different risk factors
    SCORING_WEIGHTS = {
        'bias': {
            'high_confidence': 35,
            'moderate': 20,
            'mild': 10,
            'nigerian_specific': 15  # Additional penalty for Nigerian context bias
        },
        'emotion': {
            'manipulation_high': 30,
            'manipulation_medium': 18,
            'charged': 12,
            'extreme': 25,
            'strong': 15,
            'mild': 6
        },
        'fake_news': {
            'high_risk': 40,  # Increased - fake news is critical
            'medium_risk': 25,
            'low_risk': 12
        },
        'clickbait': {
            'high': 20,
            'medium': 12,
            'low': 6
        },
        'viral_manipulation': {
            'high': 25,
            'medium': 15,
            'low': 8
        },
        'nigerian_triggers': {
            'high': 18,
            'medium': 12,
            'low': 6
        },
        'sentiment': {
            'polarized': 15,
            'divisive': 10,
            'negative': 8,
            'positive_bias': 5  # Even positive can be biased
        }
    }

    @staticmethod
    def get_trust_indicator(score: float) -> str:
        """Get color-coded trust indicator with improved granularity"""
        if score >= 85:
            return "🟢 Highly Trusted"
        elif score >= 70:
            return "🟢 Trusted"
        elif score >= 55:
            return "🟡 Moderate Caution"
        elif score >= 40:
            return "🟡 High Caution"
        elif score >= 25:
            return "🔴 Risky"
        else:
            return "🔴 Highly Risky"

    @staticmethod
    def get_detailed_trust_level(score: float) -> str:
        """Get detailed trust categorization"""
        for level, threshold in TrustScoreCalculator.TRUST_THRESHOLDS.items():
            if score >= threshold:
                return level
        return "highly_risky"

    @staticmethod
    def calculate(bias_score: float, emotion_score: float, sentiment_label: str, text: str,
                  emotion_data: Optional[Dict] = None, sentiment_data: Optional[Dict] = None, 
                  bias_data: Optional[Dict] = None) -> Tuple[float, str, List[str], str, Dict]:
        """
        Enhanced trust score calculation with improved logic and weighting
        """
        # Initialize with perfect score
        base_score = 100.0
        deductions = []
        risk_factors = []
        explanation = []

        # Pattern Analysis
        nigerian_analysis = NigerianPatterns.analyze_patterns(text)
        fake_detected, fake_details = FakeNewsDetector.detect(text)
        viral_analysis = ViralityDetector.analyze_virality(text)

        # === BIAS SCORING (Enhanced) ===
        bias_deduction = TrustScoreCalculator._calculate_bias_deduction(
            bias_score, bias_data, deductions, risk_factors, explanation
        )

        # === EMOTION SCORING (Enhanced) ===
        emotion_deduction = TrustScoreCalculator._calculate_emotion_deduction(
            emotion_score, emotion_data, deductions, risk_factors, explanation
        )

        # === SENTIMENT SCORING (Enhanced) ===
        sentiment_deduction = TrustScoreCalculator._calculate_sentiment_deduction(
            sentiment_label, sentiment_data, deductions, risk_factors, explanation
        )

        # === FAKE NEWS ANALYSIS (Enhanced) ===
        fake_deduction = TrustScoreCalculator._calculate_fake_news_deduction(
            fake_detected, fake_details, deductions, risk_factors, explanation
        )

        # === NIGERIAN PATTERN ANALYSIS (Enhanced) ===
        pattern_deduction = TrustScoreCalculator._calculate_pattern_deduction(
            nigerian_analysis, deductions, risk_factors, explanation
        )

        # === VIRAL MANIPULATION ANALYSIS (Enhanced) ===
        viral_deduction = TrustScoreCalculator._calculate_viral_deduction(
            viral_analysis, deductions, risk_factors, explanation
        )

        # === CALCULATE FINAL SCORE ===
        total_deduction = sum(deductions)
        
        # Apply diminishing returns to prevent over-penalization
        adjusted_deduction = TrustScoreCalculator._apply_diminishing_returns(total_deduction)
        
        final_score = max(0, min(base_score - adjusted_deduction, 100))

        # === POSITIVE ADJUSTMENTS ===
        final_score = TrustScoreCalculator._apply_positive_adjustments(
            final_score, risk_factors, sentiment_label, emotion_data, bias_data, explanation
        )

        # Generate results
        indicator = TrustScoreCalculator.get_trust_indicator(final_score)
        trust_level = TrustScoreCalculator.get_detailed_trust_level(final_score)
        tip = TrustScoreCalculator._get_contextual_tip(risk_factors)
        summary = TrustScoreCalculator._generate_summary(final_score, risk_factors)

        return final_score, indicator, explanation, tip, {
            'trust_level': trust_level,
            'risk_factors': risk_factors,
            'summary': summary,
            'deductions': deductions,
            'total_deduction': total_deduction,
            'adjusted_deduction': adjusted_deduction,
            'pattern_analysis': {
                'nigerian_patterns': nigerian_analysis,
                'fake_news_risk': fake_details if fake_detected else None,
                'viral_manipulation': viral_analysis if viral_analysis['has_viral_patterns'] else None
            }
        }

    @staticmethod
    def _calculate_bias_deduction(bias_score: float, bias_data: Optional[Dict], 
                                deductions: List[float], risk_factors: List[str], 
                                explanation: List[str]) -> float:
        """Calculate bias-related score deductions"""
        deduction = 0.0
        
        if bias_data and 'flag' in bias_data:
            if bias_data['flag']:
                # Enhanced bias detection logic
                confidence_level = bias_data.get('confidence', 0)
                bias_level = bias_data.get('bias_level', 'low')
                
                if bias_level == 'high' or confidence_level > 0.8:
                    deduction = TrustScoreCalculator.SCORING_WEIGHTS['bias']['high_confidence']
                    explanation.append("High confidence bias detected with strong language patterns.")
                    risk_factors.append("high_bias")
                elif bias_level == 'medium' or confidence_level > 0.6:
                    deduction = TrustScoreCalculator.SCORING_WEIGHTS['bias']['moderate']
                    explanation.append("Moderate bias detected in language patterns.")
                    risk_factors.append("moderate_bias")
                else:
                    deduction = TrustScoreCalculator.SCORING_WEIGHTS['bias']['mild']
                    explanation.append("Mild bias detected in language patterns.")
                    risk_factors.append("mild_bias")

                # Additional penalty for Nigerian-specific bias
                nigerian_detections = bias_data.get('nigerian_detections', [])
                if nigerian_detections:
                    high_confidence_nigerian = [d for d in nigerian_detections if d.get('confidence', 0) > 0.7]
                    if high_confidence_nigerian:
                        additional_deduction = TrustScoreCalculator.SCORING_WEIGHTS['bias']['nigerian_specific']
                        deduction += additional_deduction
                        explanation.append(f"Nigerian-specific bias detected: {', '.join([d.get('term', '') for d in high_confidence_nigerian[:2]])}")
                        risk_factors.append("nigerian_bias")

                # Bias type information
                bias_type = bias_data.get('type_analysis', {}).get('type')
                if bias_type and bias_type not in ['neutral', 'no bias', 'analysis_error']:
                    explanation.append(f"Bias type: {bias_type.replace('_', ' ').title()}")
                    
        else:
            # Fallback to legacy scoring
            if bias_score >= 0.8:
                deduction = TrustScoreCalculator.SCORING_WEIGHTS['bias']['high_confidence']
                explanation.append("Strong biased language detected.")
                risk_factors.append("strong_bias")
            elif bias_score >= 0.6:
                deduction = TrustScoreCalculator.SCORING_WEIGHTS['bias']['moderate']
                explanation.append("Moderate bias detected.")
                risk_factors.append("moderate_bias")
            elif bias_score >= 0.4:
                deduction = TrustScoreCalculator.SCORING_WEIGHTS['bias']['mild']
                explanation.append("Mild bias detected.")
                risk_factors.append("mild_bias")

        deductions.append(deduction)
        return deduction

    @staticmethod
    def _calculate_emotion_deduction(emotion_score: float, emotion_data: Optional[Dict], 
                                   deductions: List[float], risk_factors: List[str], 
                                   explanation: List[str]) -> float:
        """Calculate emotion-related score deductions"""
        deduction = 0.0
        
        if emotion_data:
            manipulation_risk = emotion_data.get('manipulation_risk', 'minimal')
            is_charged = emotion_data.get('is_emotionally_charged', False)
            
            if manipulation_risk == 'high':
                deduction = TrustScoreCalculator.SCORING_WEIGHTS['emotion']['manipulation_high']
                explanation.append("High emotional manipulation detected.")
                risk_factors.append("emotional_manipulation")
            elif manipulation_risk == 'medium':
                deduction = TrustScoreCalculator.SCORING_WEIGHTS['emotion']['manipulation_medium']
                explanation.append("Moderate emotional manipulation detected.")
                risk_factors.append("moderate_emotional_manipulation")
            elif is_charged:
                deduction = TrustScoreCalculator.SCORING_WEIGHTS['emotion']['charged']
                explanation.append("Emotionally charged content detected.")
                risk_factors.append("emotional_content")
                
        else:
            # Legacy emotion scoring
            if emotion_score >= 0.8:
                deduction = TrustScoreCalculator.SCORING_WEIGHTS['emotion']['extreme']
                explanation.append("Extremely emotionally charged content.")
                risk_factors.append("extreme_emotion")
            elif emotion_score >= 0.6:
                deduction = TrustScoreCalculator.SCORING_WEIGHTS['emotion']['strong']
                explanation.append("Strong emotional tone detected.")
                risk_factors.append("strong_emotion")
            elif emotion_score >= 0.4:
                deduction = TrustScoreCalculator.SCORING_WEIGHTS['emotion']['mild']
                explanation.append("Mild emotional tone detected.")
                risk_factors.append("mild_emotion")

        deductions.append(deduction)
        return deduction

    @staticmethod
    def _calculate_sentiment_deduction(sentiment_label: str, sentiment_data: Optional[Dict], 
                                     deductions: List[float], risk_factors: List[str], 
                                     explanation: List[str]) -> float:
        """Calculate sentiment-related score deductions"""
        deduction = 0.0
        
        if sentiment_data:
            if sentiment_data.get('bias_indicator', False):
                deduction += TrustScoreCalculator.SCORING_WEIGHTS['sentiment']['negative']
                explanation.append("Sentiment analysis indicates potential bias.")
                risk_factors.append("sentiment_bias")

            if sentiment_data.get('is_polarized', False):
                deduction += TrustScoreCalculator.SCORING_WEIGHTS['sentiment']['polarized']
                explanation.append("Highly polarized sentiment detected.")
                risk_factors.append("polarized_content")

            polarization = sentiment_data.get('polarization_score', 0)
            if polarization > 0.7:
                deduction += TrustScoreCalculator.SCORING_WEIGHTS['sentiment']['divisive']
                explanation.append("Divisive sentiment patterns detected.")
                risk_factors.append("divisive_sentiment")
                
        else:
            # Legacy sentiment scoring
            if sentiment_label == 'negative':
                deduction = TrustScoreCalculator.SCORING_WEIGHTS['sentiment']['negative']
                explanation.append("Negative sentiment tone detected.")
                risk_factors.append("negative_sentiment")
            elif sentiment_label == 'positive':
                # Even positive sentiment can indicate bias
                deduction = TrustScoreCalculator.SCORING_WEIGHTS['sentiment']['positive_bias']
                explanation.append("Positive sentiment may indicate bias.")

        deductions.append(deduction)
        return deduction

    @staticmethod
    def _calculate_fake_news_deduction(fake_detected: bool, fake_details: Dict, 
                                     deductions: List[float], risk_factors: List[str], 
                                     explanation: List[str]) -> float:
        """Calculate fake news related deductions"""
        deduction = 0.0
        
        if fake_detected:
            risk_level = fake_details.get('risk_level', 'medium')
            
            if risk_level == 'high':
                deduction = TrustScoreCalculator.SCORING_WEIGHTS['fake_news']['high_risk']
                explanation.append("High risk of fake news detected.")
                risk_factors.append("high_fake_risk")
            elif risk_level == 'medium':
                deduction = TrustScoreCalculator.SCORING_WEIGHTS['fake_news']['medium_risk']
                explanation.append("Medium risk of fake news detected.")
                risk_factors.append("medium_fake_risk")
            else:
                deduction = TrustScoreCalculator.SCORING_WEIGHTS['fake_news']['low_risk']
                explanation.append("Low risk suspicious patterns detected.")
                risk_factors.append("low_fake_risk")

            # Add specific patterns to explanation
            if fake_details.get('fake_matches'):
                top_matches = list(set(fake_details['fake_matches'][:3]))
                explanation.append(f"Suspicious phrases: {', '.join(top_matches)}")

        deductions.append(deduction)
        return deduction

    @staticmethod
    def _calculate_pattern_deduction(nigerian_analysis: Dict, deductions: List[float], 
                                   risk_factors: List[str], explanation: List[str]) -> float:
        """Calculate Nigerian pattern related deductions"""
        deduction = 0.0
        
        if nigerian_analysis['has_triggers']:
            trigger_score = nigerian_analysis['trigger_score']
            if trigger_score > 0.7:
                deduction += TrustScoreCalculator.SCORING_WEIGHTS['nigerian_triggers']['high']
            elif trigger_score > 0.4:
                deduction += TrustScoreCalculator.SCORING_WEIGHTS['nigerian_triggers']['medium']
            else:
                deduction += TrustScoreCalculator.SCORING_WEIGHTS['nigerian_triggers']['low']
                
            explanation.append("Nigerian trigger phrases commonly used in misleading content.")
            risk_factors.append("nigerian_triggers")

        if nigerian_analysis['has_clickbait']:
            clickbait_score = nigerian_analysis['clickbait_score']
            if clickbait_score > 0.7:
                deduction += TrustScoreCalculator.SCORING_WEIGHTS['clickbait']['high']
            elif clickbait_score > 0.4:
                deduction += TrustScoreCalculator.SCORING_WEIGHTS['clickbait']['medium']
            else:
                deduction += TrustScoreCalculator.SCORING_WEIGHTS['clickbait']['low']
                
            explanation.append("Clickbait patterns designed to attract clicks.")
            risk_factors.append("clickbait")

        deductions.append(deduction)
        return deduction

    @staticmethod
    def _calculate_viral_deduction(viral_analysis: Dict, deductions: List[float], 
                                 risk_factors: List[str], explanation: List[str]) -> float:
        """Calculate viral manipulation related deductions"""
        deduction = 0.0
        
        if viral_analysis['has_viral_patterns']:
            manipulation_level = viral_analysis.get('manipulation_level', 'low')
            
            if manipulation_level == 'high':
                deduction = TrustScoreCalculator.SCORING_WEIGHTS['viral_manipulation']['high']
                explanation.append("High viral manipulation tactics detected.")
                risk_factors.append("viral_manipulation")
            elif manipulation_level == 'medium':
                deduction = TrustScoreCalculator.SCORING_WEIGHTS['viral_manipulation']['medium']
                explanation.append("Moderate viral manipulation tactics detected.")
                risk_factors.append("mild_viral_manipulation")
            else:
                deduction = TrustScoreCalculator.SCORING_WEIGHTS['viral_manipulation']['low']
                explanation.append("Mild viral manipulation patterns detected.")
                risk_factors.append("low_viral_manipulation")

        deductions.append(deduction)
        return deduction

    @staticmethod
    def _apply_diminishing_returns(total_deduction: float) -> float:
        """Apply diminishing returns to prevent over-penalization"""
        if total_deduction <= 50:
            return total_deduction
        elif total_deduction <= 80:
            # Reduced impact for medium penalties
            return 50 + (total_deduction - 50) * 0.7
        else:
            # Further reduced impact for high penalties
            return 50 + 30 * 0.7 + (total_deduction - 80) * 0.5

    @staticmethod
    def _apply_positive_adjustments(score: float, risk_factors: List[str], sentiment_label: str,
                                  emotion_data: Optional[Dict], bias_data: Optional[Dict], 
                                  explanation: List[str]) -> float:
        """Apply positive adjustments for high-quality content"""
        bonus = 0
        
        # Bonus for truly neutral, well-balanced content
        is_neutral_sentiment = sentiment_label == 'neutral'
        is_minimal_emotion = (not emotion_data or 
                            (emotion_data.get('manipulation_risk', 'minimal') == 'minimal' and 
                             not emotion_data.get('is_emotionally_charged', False)))
        is_unbiased = (not bias_data or not bias_data.get('flag', False))
        
        if len(risk_factors) == 0 and is_neutral_sentiment and is_minimal_emotion and is_unbiased:
            bonus += 8
            explanation.append("Content appears balanced and factual.")
        elif len(risk_factors) <= 1 and is_neutral_sentiment:
            bonus += 4
            explanation.append("Content shows good neutrality.")
        elif len(risk_factors) <= 2:
            bonus += 2
            explanation.append("Content has minimal risk factors.")

        return min(score + bonus, 100)

    @staticmethod
    def _get_contextual_tip(risk_factors: List[str]) -> str:
        """Get contextual tip based on detected risk factors"""
        contextual_tips = {
            'bias': "Examine if the content fairly represents different viewpoints. Look for balanced reporting that acknowledges complexity.",
            'emotion': "Be wary of content that uses strong emotions to bypass critical thinking. Question if the emotion is justified by evidence.",
            'fake_news': "Verify information using the 'SIFT' method: Stop, Investigate the source, Find better coverage, Trace claims to original context.",
            'nigerian_triggers': "Local expressions can make fake news seem authentic. Verify Nigerian content through multiple local sources.",
            'clickbait': "Clickbait headlines often exaggerate. Compare headlines with actual article content and check for sensationalism.",
            'viral_manipulation': "Be skeptical of content designed to trigger immediate sharing. Verify before amplifying, especially urgent-sounding claims.",
            'sentiment': "Highly polarized content may be designed to create division. Seek balanced perspectives on controversial topics."
        }

        # Priority order for tip selection
        tip_priorities = ['fake_news', 'bias', 'emotion', 'viral_manipulation', 'nigerian_triggers', 'clickbait', 'sentiment']
        
        for priority in tip_priorities:
            if any(priority in rf for rf in risk_factors):
                return contextual_tips[priority]
        
        return random.choice(TrustScoreCalculator.DID_YOU_KNOW_TIPS)

    @staticmethod
    def _generate_summary(score: float, risk_factors: List[str]) -> str:
        """Generate human-readable summary with context"""
        risk_count = len(risk_factors)
        
        if score >= 85:
            return f"This content appears highly trustworthy with {risk_count} risk factors detected."
        elif score >= 70:
            return f"This content appears generally trustworthy with {risk_count} minor concerns."
        elif score >= 55:
            return f"This content shows {risk_count} concerning patterns - verify from other sources."
        elif score >= 40:
            return f"This content has {risk_count} red flags - approach with significant caution."
        elif score >= 25:
            return f"This content appears risky with {risk_count} manipulation indicators."
        else:
            return f"This content shows strong signs of bias, manipulation, or misinformation ({risk_count} risk factors)."