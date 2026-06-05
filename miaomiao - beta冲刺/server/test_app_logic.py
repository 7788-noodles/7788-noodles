import unittest
from unittest.mock import patch

import app


class BillParseLogicTest(unittest.TestCase):
    def test_extract_amount_from_text(self):
        self.assertEqual(app.extract_amount("午饭花了25"), 25)
        self.assertEqual(app.extract_amount("工资到账5000"), 5000)
        self.assertEqual(app.extract_amount("报销120.5元"), 120.5)

    def test_detect_bill_type(self):
        self.assertEqual(app.detect_bill_type("工资到账5000"), "收入")
        self.assertEqual(app.detect_bill_type("收到兼职收入300"), "收入")
        self.assertEqual(app.detect_bill_type("午饭花了25"), "支出")
        self.assertEqual(app.detect_bill_type("买水果18"), "支出")

    def test_classify_income_category(self):
        self.assertEqual(app.classify_income_category("工资到账5000")["category"], "工资")
        self.assertEqual(app.classify_income_category("奖金到账800")["category"], "奖金")
        self.assertEqual(app.classify_income_category("兼职收入300")["category"], "兼职")
        self.assertEqual(app.classify_income_category("报销到账120")["category"], "报销")
        self.assertEqual(app.classify_income_category("理财分红50")["category"], "理财")
        self.assertEqual(app.classify_income_category("收到红包20")["category"], "其他收入")

    def test_parse_income_bill(self):
        result = app.parse_text_to_bill("工资到账5000")

        self.assertEqual(result["type"], "收入")
        self.assertEqual(result["amount"], 5000)
        self.assertEqual(result["category"], "工资")
        self.assertEqual(result["remark"], "工资到账5000")

    def test_parse_expense_bill_without_calling_ai(self):
        with patch.object(
            app,
            "classify_category_with_ai_placeholder",
            return_value={"category": "餐饮", "remark": "午饭花了25"}
        ):
            result = app.parse_text_to_bill("午饭花了25")

        self.assertEqual(result["type"], "支出")
        self.assertEqual(result["amount"], 25)
        self.assertEqual(result["category"], "餐饮")
        self.assertEqual(result["remark"], "午饭花了25")


if __name__ == "__main__":
    unittest.main()
