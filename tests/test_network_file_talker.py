import os
import unittest

from climate_citations.network_file_talker import NetworkFileTalker


class TestNetworkFileTalker(unittest.TestCase):
    def test_write_file(self):
        tests_dir = os.path.dirname(__file__)
        sample_path = os.path.join(tests_dir, "sample_works_list.json")

        nf = NetworkFileTalker()

        # Use read_file to produce the input list from the sample file
        input_list = nf.read_file(sample_path)

        test_file = os.path.join(tests_dir, "test-file")

        # Ensure clean start
        if os.path.exists(test_file):
            os.remove(test_file)

        nf.write_list(input_list, test_file)

        # Read back file using NetworkFileTalker.read_file
        output_list = nf.read_file(test_file)

        # Assertions
        self.assertEqual(len(input_list), len(output_list))

        if len(input_list) > 0:
            first_in = input_list[0]
            first_out = output_list[0]
            self.assertEqual(first_in.get("id"), first_out.get("id"))
            self.assertEqual(first_in.get("display_name"), first_out.get("display_name"))

        # Cleanup
        if os.path.exists(test_file):
            os.remove(test_file)


if __name__ == "__main__":
    unittest.main()