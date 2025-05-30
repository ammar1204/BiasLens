import unittest
from biaslens.patterns import NigerianPatterns, FakeNewsDetector, ViralityDetector

class TestNigerianPatterns(unittest.TestCase):
    def test_analyze_patterns_no_matches(self):
        text = "This is a standard English sentence."
        result = NigerianPatterns.analyze_patterns(text)
        self.assertFalse(result['has_triggers'])
        self.assertFalse(result['has_clickbait'])
        self.assertEqual(len(result['trigger_matches']), 0)
        self.assertEqual(len(result['clickbait_matches']), 0)
        self.assertEqual(result['trigger_score'], 0.0)
        self.assertEqual(result['clickbait_score'], 0.0)
        self.assertEqual(result['total_flags'], 0)

    def test_analyze_patterns_with_triggers(self):
        text = "Nawa o, this government is lying to us all. Aswear!"
        # Expected matches: "Nawa o", "government is lying", "Aswear"
        result = NigerianPatterns.analyze_patterns(text)
        self.assertTrue(result['has_triggers'])
        self.assertFalse(result['has_clickbait'])
        self.assertEqual(len(result['trigger_matches']), 3)
        self.assertIn("nawa o", [m.lower() for m in result['trigger_matches']]) # Check case-insensitivity
        self.assertIn("government is lying", [m.lower() for m in result['trigger_matches']])
        self.assertIn("aswear", [m.lower() for m in result['trigger_matches']])
        self.assertGreater(result['trigger_score'], 0)
        self.assertEqual(result['total_flags'], 3)

    def test_analyze_patterns_with_clickbait(self):
        text = "You won't believe what happened next! This will amaze you."
        # Expected: "You won't believe", "what happened next", "This will amaze you"
        result = NigerianPatterns.analyze_patterns(text)
        self.assertFalse(result['has_triggers'])
        self.assertTrue(result['has_clickbait'])
        self.assertEqual(len(result['clickbait_matches']), 3)
        self.assertIn("you won't believe", [m.lower() for m in result['clickbait_matches']])
        self.assertGreater(result['clickbait_score'], 0)
        self.assertEqual(result['total_flags'], 3)

    def test_analyze_patterns_with_both(self):
        text = "Breaking: Dem wan kill us! See what they did, you won't believe it."
        # Triggers: "Breaking:", "Dem wan kill us"
        # Clickbait: "See what they did", "you won't believe"
        result = NigerianPatterns.analyze_patterns(text)
        self.assertTrue(result['has_triggers'])
        self.assertTrue(result['has_clickbait'])
        self.assertEqual(len(result['trigger_matches']), 2)
        self.assertEqual(len(result['clickbait_matches']), 2)
        self.assertGreater(result['trigger_score'], 0)
        self.assertGreater(result['clickbait_score'], 0)
        self.assertEqual(result['total_flags'], 4)

    def test_has_misleading_pattern_legacy(self):
        text_misleading = "Nawa o, this is clickbait: you won't believe this."
        text_clean = "A normal sentence."
        self.assertTrue(NigerianPatterns.has_misleading_pattern(text_misleading))
        self.assertFalse(NigerianPatterns.has_misleading_pattern(text_clean))

class TestFakeNewsDetector(unittest.TestCase):
    def test_detect_no_fake_news(self):
        text = "The weather is sunny today."
        is_suspicious, details = FakeNewsDetector.detect(text)
        self.assertFalse(is_suspicious)
        self.assertEqual(len(details['fake_matches']), 0)
        self.assertEqual(len(details['credibility_flags']), 0)
        self.assertEqual(details['fake_score'], 0.0)
        self.assertEqual(details['credibility_score'], 0.0)
        self.assertEqual(details['risk_level'], 'minimal')
        self.assertEqual(details['total_flags'], 0)

    def test_detect_with_fake_patterns(self):
        text = "SHOCKING! The truth about what they don't want you to know. Mainstream media won't tell you!"
        # Expected fake: "SHOCKING", "what they don't want you to know", "mainstream media won't tell you"
        is_suspicious, details = FakeNewsDetector.detect(text)
        self.assertTrue(is_suspicious)
        self.assertEqual(len(details['fake_matches']), 3)
        self.assertIn("SHOCKING", details['fake_matches'])
        self.assertGreater(details['fake_score'], 0)
        self.assertIn(details['risk_level'], ['medium', 'high']) # Depends on word count vs matches

    def test_detect_with_credibility_flags(self):
        text = "According to sources, experts say this is a major event. Insider reveals all!"
        # Expected credibility: "According to sources", "experts say", "Insider reveals"
        is_suspicious, details = FakeNewsDetector.detect(text)
        self.assertTrue(is_suspicious) # is_suspicious if len(credibility_flags) > 1
        self.assertEqual(len(details['credibility_flags']), 3)
        self.assertIn("according to sources", [m.lower() for m in details['credibility_flags']])
        self.assertGreater(details['credibility_score'], 0)
        self.assertIn(details['risk_level'], ['medium', 'high'])

    def test_detect_with_both_patterns_and_flags(self):
        text = "BREAKING: Experts say the secret plan is EXPOSED! What they don't want you to know."
        # Fake: "BREAKING", "EXPOSED", "What they don't want you to know"
        # Credibility: "Experts say"
        is_suspicious, details = FakeNewsDetector.detect(text)
        self.assertTrue(is_suspicious)
        self.assertEqual(len(details['fake_matches']), 3)
        self.assertEqual(len(details['credibility_flags']), 1) # is_suspicious because fake_matches > 0
        self.assertGreater(details['fake_score'], 0)
        self.assertGreater(details['credibility_score'], 0)
        self.assertEqual(details['risk_level'], 'high') # Likely high due to multiple flags

    def test_risk_level_logic(self):
        # Low risk (one fake match in long text)
        text_low = "This is a very long text with one instance of revealed information that might be interesting."
        _, details_low = FakeNewsDetector.detect(text_low)
        self.assertEqual(details_low['risk_level'], 'low')

        # Minimal risk
        text_min = "Perfectly normal."
        _, details_min = FakeNewsDetector.detect(text_min)
        self.assertEqual(details_min['risk_level'], 'minimal')


class TestViralityDetector(unittest.TestCase):
    def test_analyze_virality_no_patterns(self):
        text = "This is a factual statement."
        result = ViralityDetector.analyze_virality(text)
        self.assertFalse(result['has_viral_patterns'])
        self.assertEqual(len(result['viral_matches']), 0)
        self.assertEqual(result['viral_score'], 0.0)
        self.assertEqual(result['manipulation_level'], 'minimal')

    def test_analyze_virality_with_patterns(self):
        text = "Share this NOW before it's too late! Everyone is talking about this. RETWEET IF YOU AGREE."
        # Expected: "Share this NOW", "before it's too late", "Everyone is talking about this", "RETWEET IF YOU"
        result = ViralityDetector.analyze_virality(text)
        self.assertTrue(result['has_viral_patterns'])
        self.assertEqual(len(result['viral_matches']), 4)
        self.assertIn("Share this NOW", result['viral_matches'])
        self.assertIn("everyone is talking about this", [m.lower() for m in result['viral_matches']])
        self.assertGreater(result['viral_score'], 0)
        self.assertIn(result['manipulation_level'], ['medium', 'high'])

    def test_manipulation_level_logic(self):
        # Low (one match in very long text, making score low)
        text_low = "This is a very long text, a really very long text, " + \
                   "that goes on and on to make the word count high. " + \
                   "Eventually, it says you should share now. " + \
                   "But the density of this phrase is very low."
        num_words = len(text_low.split())
        # (1 / num_words) * 100 should be low. If num_words is ~30, score is ~3.33 -> high
        # Let's make it much longer for a low score.
        long_filler = "word " * 100
        text_low_density = long_filler + "share now" + long_filler
        result_low = ViralityDetector.analyze_virality(text_low_density)
        # (1 / 201) * 100 = ~0.5. This should be 'low'
        self.assertEqual(result_low['manipulation_level'], 'low')

        # Medium
        text_medium = "Share now! Tag your friends. This is important." # 2-3 matches in moderate text
        result_medium = ViralityDetector.analyze_virality(text_medium)
        self.assertIn(result_medium['manipulation_level'], ['medium', 'high']) # depends on exact word count

        # High
        text_high = "URGENT! SHARE THIS! RETWEET IF YOU AGREE! EVERYONE IS TALKING ABOUT THIS! BEFORE IT'S TOO LATE!"
        result_high = ViralityDetector.analyze_virality(text_high)
        self.assertEqual(result_high['manipulation_level'], 'high')

if __name__ == '__main__':
    unittest.main()
