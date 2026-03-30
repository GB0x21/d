import unittest
from bot.price_extractor import extract_prices


class TestPriceExtractor(unittest.TestCase):
    def test_penny_price(self):
        result = extract_prices("Found item for $0.01 at HD")
        self.assertTrue(result["is_penny"])
        self.assertEqual(result["deal_price"], 0.01)

    def test_penny_word(self):
        result = extract_prices("This is a penny item at store #1234")
        self.assertTrue(result["is_penny"])

    def test_three_cents(self):
        result = extract_prices("Scanning at $0.03")
        self.assertTrue(result["is_penny"])
        self.assertEqual(result["deal_price"], 0.03)

    def test_regular_price(self):
        result = extract_prices("On sale for $12.99")
        self.assertFalse(result["is_penny"])
        self.assertEqual(result["deal_price"], 12.99)

    def test_original_and_deal_price(self):
        result = extract_prices("Was $49.99, now $0.01!")
        self.assertTrue(result["is_penny"])
        self.assertEqual(result["deal_price"], 0.01)
        self.assertEqual(result["original_price"], 49.99)
        self.assertAlmostEqual(result["discount_pct"], 100.0, places=0)

    def test_price_error_phrase(self):
        result = extract_prices("Looks like a price error at Home Depot")
        self.assertTrue(result["is_penny"])

    def test_ringing_up_as(self):
        result = extract_prices("Ringing up as $0.01 at the register")
        self.assertTrue(result["is_penny"])

    def test_no_price(self):
        result = extract_prices("Just a regular discussion post")
        self.assertFalse(result["is_penny"])
        self.assertIsNone(result["deal_price"])

    def test_dollar_sign_no_zero(self):
        result = extract_prices("Found for $.03 at checkout")
        self.assertTrue(result["is_penny"])


if __name__ == "__main__":
    unittest.main()
