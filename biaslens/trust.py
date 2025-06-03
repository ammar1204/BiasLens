import random
import re
from datetime import datetime, timedelta
from urllib.parse import urlparse
from .patterns import NigerianPatterns, FakeNewsDetector, ViralityDetector


class SourceCredibilityScorer:
    """Nigerian-focused domain reputation and source credibility scoring"""
    
    # Nigerian news sources by credibility tier
    NIGERIAN_SOURCES = {
        'highly_credible': {
            'domains': [
                'punch.ng', 'thisdaylive.com', 'premiumtimesng.com', 'channelstv.com',
                'guardian.ng', 'vanguardngr.com', 'dailytrust.com', 'tribuneonlineng.com',
                'businessday.ng', 'leadership.ng', 'thecable.ng', 'saharareporters.com'
            ],
            'score_boost': 15,
            'description': 'Established Nigerian news organizations with editorial standards'
        },
        'credible': {
            'domains': [
                'legit.ng', 'naij.com', 'pulse.ng', 'nairametrics.com', 'blueprint.ng',
                'dailypost.ng', 'independent.ng', 'nationonlineng.net', 'newtelegraphng.com'
            ],
            'score_boost': 8,
            'description': 'Recognized Nigerian news sources with good track record'
        },
        'mixed': {
            'domains': [
                'lindaikejisblog.com', 'informationng.com', 'gistmania.com',
                'tori.ng', 'yabaleftonline.ng', 'gossipmill.com'
            ],
            'score_penalty': 5,
            'description': 'Entertainment/gossip sources that sometimes share news'
        },
        'questionable': {
            'domains': [
                'trendingpolitics.ng', 'nairaland.com', 'liberianobserver.com',
                'pulsenigeria247.com', 'nationalhelm.co'
            ],
            'score_penalty': 15,
            'description': 'Sources with history of unverified or biased content'
        },
        'high_risk': {
            'domains': [
                'newsrescue.com', 'elombah.com', 'ukpakareports.com',
                'pointblanknews.com', 'ripples.ng'
            ],
            'score_penalty': 25,
            'description': 'Sources frequently associated with misinformation'
        }
    }
    
    INTERNATIONAL_CREDIBLE = {
        'domains': [
            'bbc.com', 'cnn.com', 'reuters.com', 'apnews.com', 'aljazeera.com',
            'france24.com', 'dw.com', 'voaafrica.com', 'africanews.com'
        ],
        'score_boost': 12,
        'description': 'International news sources with African coverage'
    }
    
    SOCIAL_MEDIA_PENALTIES = {
        'twitter.com': -8,
        'facebook.com': -10,
        'instagram.com': -12,
        'whatsapp': -15,  # For WhatsApp forwards
        'telegram': -12,
        'tiktok.com': -18
    }

    @classmethod
    def score_source(cls, text, url=None):
        """Score source credibility based on domain and content patterns"""
        score_adjustment = 0
        credibility_info = {
            'source_type': 'unknown',
            'credibility_tier': 'unverified',
            'explanation': '',
            'domain': None
        }
        
        # Extract domain from URL if provided
        domain = None
        if url:
            try:
                parsed = urlparse(url.lower())
                domain = parsed.netloc.replace('www.', '')
                credibility_info['domain'] = domain
            except:
                pass
        
        # Check for domain mentions in text if no URL provided
        if not domain:
            domain_patterns = r'(?:https?://)?(?:www\.)?([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
            matches = re.findall(domain_patterns, text.lower())
            if matches:
                domain = matches[0].replace('www.', '')
                credibility_info['domain'] = domain
        
        if domain:
            # Check Nigerian sources
            for tier, data in cls.NIGERIAN_SOURCES.items():
                if domain in data['domains']:
                    if 'score_boost' in data:
                        score_adjustment = data['score_boost']
                        credibility_info['source_type'] = 'nigerian_media'
                        credibility_info['credibility_tier'] = tier
                        credibility_info['explanation'] = f"Source recognized as {data['description'].lower()}"
                    else:
                        score_adjustment = -data['score_penalty']
                        credibility_info['source_type'] = 'nigerian_media'
                        credibility_info['credibility_tier'] = tier
                        credibility_info['explanation'] = f"Source flagged as {data['description'].lower()}"
                    break
            
            # Check international sources
            if score_adjustment == 0 and domain in cls.INTERNATIONAL_CREDIBLE['domains']:
                score_adjustment = cls.INTERNATIONAL_CREDIBLE['score_boost']
                credibility_info['source_type'] = 'international_media'
                credibility_info['credibility_tier'] = 'credible'
                credibility_info['explanation'] = cls.INTERNATIONAL_CREDIBLE['description']
            
            # Check social media penalties
            for social_domain, penalty in cls.SOCIAL_MEDIA_PENALTIES.items():
                if social_domain in domain:
                    score_adjustment = penalty
                    credibility_info['source_type'] = 'social_media'
                    credibility_info['credibility_tier'] = 'unverified'
                    credibility_info['explanation'] = f"Content from social media platform - higher verification needed"
                    break
        
        # Check for anonymous/unattributed content patterns
        anonymous_patterns = [
            r'\b(?:anonymous|unnamed) source\b',
            r'\b(?:according to|sources say)\b',
            r'\breport(?:s|ed)?\s+(?:say|claim|suggest)\b',
            r'\b(?:insider|source close to)\b'
        ]
        
        anonymous_count = sum(1 for pattern in anonymous_patterns 
                            if re.search(pattern, text.lower()))
        
        if anonymous_count >= 2:
            score_adjustment -= 8
            credibility_info['explanation'] += " Multiple anonymous sources detected."
        
        return score_adjustment, credibility_info


class RecencyFactorAnalyzer:
    """Detect and penalize old news being reshared as current events"""
    
    # Common date patterns in news content
    DATE_PATTERNS = [
        r'\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},?\s+\d{4}\b',
        r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
        r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',
        r'\b(?:yesterday|today|last week|last month|last year)\b',
        r'\b\d{1,2}(?:st|nd|rd|th)?\s+(?:of\s+)?(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{4}\b'
    ]
    
    # Outdated event indicators
    OUTDATED_INDICATORS = [
        r'\b(?:breaking|just in|urgent|alert)\b.*\b(?:2019|2020|2021|2022|2023)\b',
        r'\b(?:covid|coronavirus|lockdown)\b.*\b(?:just happened|breaking)\b',
        r'\b(?:election|vote)\b.*\b(?:2019|2023)\b.*\b(?:now|today|breaking)\b'
    ]
    
    # Time-sensitive terms that should be recent
    TIME_SENSITIVE_TERMS = [
        'breaking', 'just in', 'urgent', 'alert', 'developing', 'live',
        'happening now', 'minutes ago', 'hours ago', 'this morning'
    ]

    @classmethod
    def analyze_recency(cls, text):
        """Analyze content for recency manipulation indicators"""
        penalty = 0
        recency_info = {
            'is_potentially_outdated': False,
            'outdated_indicators': [],
            'detected_dates': [],
            'time_sensitive_claims': [],
            'explanation': ''
        }
        
        text_lower = text.lower()
        
        # Extract dates from content
        detected_dates = []
        for pattern in cls.DATE_PATTERNS:
            matches = re.findall(pattern, text_lower)
            detected_dates.extend(matches)
        
        recency_info['detected_dates'] = detected_dates[:3]  # Limit to first 3
        
        # Check for outdated event indicators
        outdated_matches = []
        for pattern in cls.OUTDATED_INDICATORS:
            matches = re.findall(pattern, text_lower)
            outdated_matches.extend(matches)
        
        if outdated_matches:
            penalty += 20
            recency_info['is_potentially_outdated'] = True
            recency_info['outdated_indicators'] = outdated_matches[:2]
            recency_info['explanation'] = "Content appears to present old events as current news."
        
        # Check for time-sensitive claims without recent context
        time_sensitive_matches = []
        for term in cls.TIME_SENSITIVE_TERMS:
            if term in text_lower:
                time_sensitive_matches.append(term)
        
        recency_info['time_sensitive_claims'] = time_sensitive_matches[:3]
        
        # If time-sensitive terms are present but no recent dates, it's suspicious
        if time_sensitive_matches and not any(['2024', '2025'] in str(date) for date in detected_dates):
            # Check if there are any old dates (2019-2023)
            old_date_indicators = ['2019', '2020', '2021', '2022', '2023']
            has_old_dates = any(year in text_lower for year in old_date_indicators)
            
            if has_old_dates:
                penalty += 15
                recency_info['is_potentially_outdated'] = True
                recency_info['explanation'] += " Time-sensitive language used with old dates."
        
        # Check for recycled content patterns
        recycled_patterns = [
            r'\b(?:remember when|flashback|throwback)\b.*\b(?:breaking|urgent)\b',
            r'\b(?:this happened|this was when)\b.*\b(?:just in|alert)\b'
        ]
        
        for pattern in recycled_patterns:
            if re.search(pattern, text_lower):
                penalty += 12
                recency_info['is_potentially_outdated'] = True
                recency_info['explanation'] += " Content appears to recycle old events as current."
                break
        
        return penalty, recency_info


class VerificationBadgeSystem:
    """Integration with fact-checking organizations and verification systems"""
    
    FACT_CHECKING_ORGS = {
        'africa_check': {
            'name': 'Africa Check',
            'url': 'africacheck.org',
            'focus': 'African fact-checking',
            'credibility': 'high'
        },
        'dubawa': {
            'name': 'Dubawa',
            'url': 'dubawa.org',
            'focus': 'Nigerian fact-checking',
            'credibility': 'high'
        },
        'reuters_fact_check': {
            'name': 'Reuters Fact Check',
            'url': 'reuters.com/fact-check',
            'focus': 'Global fact-checking',
            'credibility': 'high'
        },
        'snopes': {
            'name': 'Snopes',
            'url': 'snopes.com',
            'focus': 'Global fact-checking',
            'credibility': 'high'
        }
    }
    
    # Fact-check result indicators
    FACT_CHECK_INDICATORS = {
        'verified': {
            'patterns': [r'\b(?:verified|confirmed|fact.checked|authentic)\b'],
            'score_boost': 20,
            'badge': '✅ Verified'
        },
        'partially_true': {
            'patterns': [r'\b(?:partially true|mixed|some truth)\b'],
            'score_boost': 5,
            'badge': '⚠️ Partially Verified'
        },
        'disputed': {
            'patterns': [r'\b(?:disputed|contested|unverified|unconfirmed)\b'],
            'score_penalty': 10,
            'badge': '❓ Disputed'
        },
        'false': {
            'patterns': [r'\b(?:false|fake|hoax|debunked|misleading)\b'],
            'score_penalty': 25,
            'badge': '❌ False'
        }
    }

    @classmethod
    def check_verification_status(cls, text, url=None):
        """Check for verification badges and fact-check references"""
        verification_info = {
            'has_fact_check_reference': False,
            'fact_check_org': None,
            'verification_status': 'unverified',
            'badge': None,
            'explanation': '',
            'score_adjustment': 0
        }
        
        text_lower = text.lower()
        
        # Check for fact-checking organization references
        for org_key, org_data in cls.FACT_CHECKING_ORGS.items():
            if org_data['url'] in text_lower or org_data['name'].lower() in text_lower:
                verification_info['has_fact_check_reference'] = True
                verification_info['fact_check_org'] = org_data['name']
                verification_info['score_adjustment'] += 10
                verification_info['explanation'] = f"References {org_data['name']} fact-checking."
                break
        
        # Check for fact-check result indicators
        for status, data in cls.FACT_CHECK_INDICATORS.items():
            for pattern in data['patterns']:
                if re.search(pattern, text_lower):
                    verification_info['verification_status'] = status
                    verification_info['badge'] = data['badge']
                    
                    if 'score_boost' in data:
                        verification_info['score_adjustment'] += data['score_boost']
                    else:
                        verification_info['score_adjustment'] -= data['score_penalty']
                    
                    verification_info['explanation'] += f" Content marked as {status.replace('_', ' ')}."
                    break
            
            if verification_info['verification_status'] != 'unverified':
                break
        
        # Check for verification bypass patterns (red flags)
        bypass_patterns = [
            r'\b(?:they don\'t want you to know|mainstream media won\'t tell you)\b',
            r'\b(?:before it gets deleted|share before removal)\b',
            r'\b(?:fact.checkers are lying|ignore fact.checkers)\b'
        ]
        
        for pattern in bypass_patterns:
            if re.search(pattern, text_lower):
                verification_info['score_adjustment'] -= 15
                verification_info['explanation'] += " Contains anti-verification messaging."
                break
        
        return verification_info


class TrustScoreCalculator:
    DID_YOU_KNOW_TIPS = [
        "Verify information before sharing. Check multiple reputable sources to confirm a story's accuracy.",
        "Be wary of headlines designed to provoke strong emotions. They might prioritize clicks over facts.",
        "Look for bylines and author credentials. Anonymous sources can be a red flag for misinformation.",
        "Check the publication date. Old news can be re-shared out of context to mislead.",
        "Examine the 'About Us' page of a source to understand its mission, ownership, and potential biases.",
        "Distinguish between news reporting, opinion pieces, and sponsored content. Each has a different purpose.",
        "Cross-reference claims with fact-checking websites like Africa Check, Dubawa, or Snopes.",
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
                  emotion_data=None, sentiment_data=None, bias_data=None, url=None):
        """
        Enhanced trust score calculation with source credibility, recency, and verification

        Args:
            bias_score: Legacy bias score (for backward compatibility)
            emotion_score: Legacy emotion score
            sentiment_label: Legacy sentiment label
            text: Original text
            emotion_data: Full emotion analysis dict (optional)
            sentiment_data: Full sentiment analysis dict (optional)
            bias_data: Full bias analysis dict (optional)
            url: Source URL for credibility analysis (optional)
        """

        # Initialize score and tracking
        score = 100
        explanation = []
        risk_factors = []

        # === NEW ENHANCED FEATURES ===
        
        # 1. Source Credibility Analysis
        source_adjustment, credibility_info = SourceCredibilityScorer.score_source(text, url)
        score += source_adjustment
        
        if credibility_info['credibility_tier'] != 'unverified':
            explanation.append(f"Source credibility: {credibility_info['explanation']}")
            if source_adjustment > 0:
                risk_factors.append(f"credible_source_{credibility_info['credibility_tier']}")
            else:
                risk_factors.append(f"questionable_source_{credibility_info['credibility_tier']}")
        
        # 2. Recency Factor Analysis
        recency_penalty, recency_info = RecencyFactorAnalyzer.analyze_recency(text)
        score -= recency_penalty
        
        if recency_info['is_potentially_outdated']:
            explanation.append(recency_info['explanation'])
            risk_factors.append("outdated_content")
        
        # 3. Verification Badge System
        verification_info = VerificationBadgeSystem.check_verification_status(text, url)
        score += verification_info['score_adjustment']
        
        if verification_info['has_fact_check_reference']:
            explanation.append(verification_info['explanation'])
            risk_factors.append(f"fact_check_{verification_info['verification_status']}")

        # === EXISTING ANALYSIS (Enhanced) ===
        
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
        # Enhanced bonus for verified, credible, recent content
        if (len([rf for rf in risk_factors if not rf.startswith('credible_source')]) == 0 and
                sentiment_label == 'neutral' and
                (not emotion_data or emotion_data.get('manipulation_risk', 'minimal') == 'minimal' and not emotion_data.get('is_emotionally_charged', False)) and
                (not bias_data or not bias_data.get('flag', False)) and
                credibility_info['credibility_tier'] in ['highly_credible', 'credible'] and
                not recency_info['is_potentially_outdated']):
            score += 10
            explanation.append("Content appears balanced, factual, and from credible source.")

        # Verification badge bonus
        if verification_info['badge']:
            explanation.append(f"Verification status: {verification_info['badge']}")

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
            'source_credibility': credibility_info,
            'recency_analysis': recency_info,
            'verification_status': verification_info,
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