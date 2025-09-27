import os
import csv
import json
import unittest

from climate_citations.network_file_talker import NetworkFileTalker
from climate_citations.openalex import OpenAlexClient, Work
# from climate_citations.network_file_talker import NetworkFileTalker, ReferenceEdge


class TestNetworkFileTalker(unittest.TestCase):
    # def test_write_file(self):
    #     tests_dir = os.path.dirname(__file__)
    #     sample_path = os.path.join(tests_dir, "sample_works_list.json")
    #     test_file = os.path.join(tests_dir, "test-file")

    #     nf = NetworkFileTalker(json_out_file=test_file)

    #     # Use read_file to produce the input list from the sample file
    #     input_list = nf.read_file(sample_path, key="results")
    #     # print(f"Input list has {len(input_list)} records")
    #     # print(f"first: {input_list[0]}")
    #     print(f"Input list has {len(input_list)} records")
    #     self.assertEqual(len(input_list), 5)  # sample file has five records


    #     # Ensure clean start
    #     if os.path.exists(test_file):
    #         os.remove(test_file)
    #     print(f"Writing {len(input_list)} records to {test_file}")
    #     nf.write_list(input_list)
    #     print(f"Wrote {len(input_list)} records to {test_file}, about to read 2nd")
    #     # Read back file using NetworkFileTalker.read_file
    #     output_list = nf.read_file(test_file)

    #     # Assertions
    #     self.assertEqual(len(input_list), len(output_list))

    #     if len(input_list) > 0:
    #         first_in = input_list[0]
    #         first_out = output_list[0]
    #         self.assertEqual(first_in.get("id"), first_out.get("id"))
    #         self.assertEqual(first_in.get("display_name"), first_out.get("display_name"))
    #         print(f"First record id: {first_out.get('id')}, display_name: {first_out.get('display_name')}")
        # Cleanup
        # if os.path.exists(test_file):
        #     os.remove(test_file)

    # def test_write_work_nodes_edges(self):
    #     tests_dir = os.path.dirname(__file__)
    #     sample_path = os.path.join(tests_dir, "sample_works_list.json")

    #     test_file = os.path.join(tests_dir, "test-file")
    #     ref_file = os.path.join(tests_dir, "reference_edges.csv")
    #     print(f"Using test files: {test_file}, {ref_file}")

    #     nf = NetworkFileTalker(json_out_file=test_file,
    #                             reference_edge_file=ref_file)

    #     # Read sample input using the talker's read_file and normalize to a list of records
    #     # request the 'results' top-level key from the sample JSON
    #     input_list = nf.read_file(sample_path, key="results")
    #     # print(f"Input: {input_list[0]} records")
    
    #     nf.write_list(input_list)

    #     # ensure clean start
    #     # for p in (test_file, ref_file):
    #     #     if os.path.exists(p):
    #     #         os.remove(p)
    #     print(f"Input list has {len(input_list)} records")
    #     try:
    #         # call the method under test
    #         nf.write_work_nodes_edges(input_list)

    #         # print the contents of test_file
    #         with open(test_file, "r", encoding="utf-8") as fh:
    #             contents = fh.read()
    #         # print(contents)

    #         # read back nodes as list and assert counts and first record fields
    #         output_list = nf.read_file(test_file)
    #         if len(output_list) == 1 and isinstance(output_list[0], list):
    #             output_list = output_list[0]

    #         # Assertions per spec
    #         # self.assertEqual(len(output_list), 5)  # test_file has five records

    #         # # verify id and display_name of first record
    #         # first_in = input_list[0]
    #         # first_out = output_list[0]
    #         # self.assertEqual(first_in.get("id"), first_out.get("id"))
    #         # self.assertEqual(first_in.get("display_name"), first_out.get("display_name"))

    #         # check reference edges CSV
    #         with open(ref_file, "r", encoding="utf-8") as fh:
    #             rows = [r.strip() for r in fh if r.strip()]
    #         self.assertEqual(len(rows), 249)

    #         self.assertEqual(rows[0], "https://openalex.org/W4249751050,https://openalex.org/W1529443799")
    #         self.assertEqual(rows[-1], "https://openalex.org/W2272473773,https://openalex.org/W118046694")

    #     finally:
    #         # cleanup
    #         for p in (test_file, ref_file):
    #             if os.path.exists(p):
    #                 os.remove(p)

    def test_build_works_and_network_for_page(self):
            tests_dir = os.path.dirname(__file__)
            sample_path = os.path.join(tests_dir, "sample_works_list.json")

            test_file = os.path.join(tests_dir, "test-file")
            ref_file = os.path.join(tests_dir, "reference_edges.csv")
            print(f"Using test files: {test_file}, {ref_file}")

            nf = NetworkFileTalker(json_out_file=test_file,
                                    reference_edge_file=ref_file)
            client = OpenAlexClient(talker=nf)

            for p in (test_file, ref_file):
                    if os.path.exists(p):
                        os.remove(p)
        

            # Read sample input using the talker's read_file and normalize to a list of records
            # request the 'results' top-level key from the sample JSON
            input_list = nf.read_file(sample_path, key="results")
            print(f"Input list has {len(input_list)} records")
            self.assertEqual(len(input_list), 5)  # sample file has five records

            results_list = []
            collected, done = client.build_works_and_network_for_page(input_list, True, results_list, 0, 5)
            self.assertEqual(collected, 5)
            self.assertTrue(done)
            self.assertEqual(len(results_list), 5)

            output_list = nf.read_file(test_file)
            if len(output_list) == 1 and isinstance(output_list[0], list):
                output_list = output_list[0]

            # Assertions per spec
            self.assertEqual(len(output_list), 5)  # test_file has five records

            # verify id and display_name of first record
            first_in = input_list[0]
            first_out = output_list[0]
            self.assertEqual(first_in.get("id"), first_out.get("id"))
            self.assertEqual(first_in.get("display_name"), first_out.get("title"))

            with open(ref_file, "r", encoding="utf-8") as fh:
                rows = [r.strip() for r in fh if r.strip()]
            self.assertEqual(len(rows), 249)

            self.assertEqual(rows[0], "https://openalex.org/W4249751050,https://openalex.org/W1529443799")
            self.assertEqual(rows[-1], "https://openalex.org/W2272473773,https://openalex.org/W641774538")




if __name__ == "__main__":
    unittest.main()