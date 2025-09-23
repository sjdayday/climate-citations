import json
import os
import unittest

from climate_citations.network_file_talker import NetworkFileTalker


class TestNetworkFileTalker(unittest.TestCase):
    def test_write_file(self):
        tests_dir = os.path.dirname(__file__)
        sample_path = os.path.join(tests_dir, "sample_works_list.json")

        # Read sample input robustly: accept JSON array, {"results": [...]}, or line-delimited JSON
        with open(sample_path, "r", encoding="utf-8") as fh:
            text = fh.read()
        try:
            data = json.loads(text)
            if isinstance(data, dict) and "results" in data:
                input_list = data["results"]
            elif isinstance(data, list):
                input_list = data
            else:
                # unexpected shape -> fallback to line parsing
                input_list = [json.loads(line) for line in text.splitlines() if line.strip()]
        except json.JSONDecodeError:
            input_list = [json.loads(line) for line in text.splitlines() if line.strip()]

        test_file = os.path.join(tests_dir, "test-file")

        # Ensure clean start
        if os.path.exists(test_file):
            os.remove(test_file)

        nf = NetworkFileTalker()
        nf.write_list(input_list, test_file)

        # Read back file as newline-delimited JSON
        with open(test_file, "r", encoding="utf-8") as fh:
            output_list = [json.loads(line) for line in fh if line.strip()]

        # Assertions
        self.assertEqual(len(input_list), len(output_list))

        first_in = input_list[0]
        first_out = output_list[0]
        self.assertEqual(first_in.get("id"), first_out.get("id"))
        self.assertEqual(first_in.get("display_name"), first_out.get("display_name"))

        # Cleanup
        os.remove(test_file)


if __name__ == "__main__":
    unittest.main()