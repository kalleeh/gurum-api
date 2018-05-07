import unittest
import apps


class TestHandlerCase(unittest.TestCase):

    def test_response(self):
        print("testing response.")
        result = app.get(None, None)
        print(result)
        self.assertEqual(result['statusCode'], 200)
        self.assertEqual(result['headers']['Content-Type'], 'application/json')
        self.assertIn('Hello World', result['body'])


if __name__ == '__main__':
    unittest.main()
