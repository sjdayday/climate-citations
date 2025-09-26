from dataclasses import dataclass
import json
import csv
import requests
from typing import List, Any, Optional
from json import JSONDecoder, JSONDecodeError

# New dataclass for an edge (from_work -> referenced_work)
@dataclass
class ReferenceEdge:
    from_work: str
    referenced_work: str

# Note: build_reference_edges and write_reference_edge(s) moved to network_file_talker.py


class NetworkFileTalker:
    """
        Simple file writer / reader for newline-delimited or concatenated JSON records.
    """
    def __init__(self, json_out_file: Optional[str] = "json_out_file.txt", reference_edge_file: Optional[str] = "reference_edges.csv"):
        self.json_out_file = json_out_file
        self.reference_edge_file = reference_edge_file    

    def write_list(self, object_list: List[Any], filename: Optional[str] = None) -> None:
        """
        Write each object in object_list as one JSON object per line to filename.
        If filename is None, use self.json_out_file. Append if file exists.
        """
        target = filename or self.json_out_file
        with open(target, "a", encoding="utf-8") as fh:
            for obj in object_list:
                fh.write(json.dumps(obj, ensure_ascii=False) + "\n")

    def read_file(self, filename: str) -> List[Any]:
        """
        Read a file that contains one or more JSON objects. Objects may be on a single
        line or span multiple lines, and objects may be concatenated in the file.

        Behavior:
        - Return a list of parsed objects.
        - Ignore sections that are not valid JSON (skip to next newline on parse error).
        - If the file does not exist or contains no valid JSON objects, return [].
        """
        try:
            with open(filename, "r", encoding="utf-8") as fh:
                text = fh.read()
        except FileNotFoundError:
            return []

        decoder = JSONDecoder()
        objs: List[Any] = []
        idx = 0
        text_len = len(text)

        while True:
            while idx < text_len and text[idx].isspace():
                idx += 1
            if idx >= text_len:
                break
            try:
                obj, end = decoder.raw_decode(text, idx)
                objs.append(obj)
                idx = end
            except JSONDecodeError:
                next_nl = text.find("\n", idx)
                if next_nl == -1:
                    # no more newlines; give up
                    break
                idx = next_nl + 1
                continue

        return objs

    def build_reference_edges(self, work: Any) -> List[ReferenceEdge]:
        """
        Build ReferenceEdge objects from a Work-like object.
        Accepts objects with attribute 'id' and either 'references' or 'referenced_works'.
        """
        refs = getattr(work, "references", None)
        if refs is None:
            refs = getattr(work, "referenced_works", None)
        if not refs:
            return []
        edges: List[ReferenceEdge] = []
        for r in refs:
            edges.append(ReferenceEdge(from_work=getattr(work, "id"), referenced_work=r))
        return edges

    def write_reference_edges(self, reference_edges: List[ReferenceEdge], filename: Optional[str] = None) -> None:
        """
        Write ReferenceEdge list to CSV file (from_work, referenced_work).
        If filename is None, use self.reference_edge_file. Append if file exists.
        """
        target = filename or self.reference_edge_file
        with open(target, "a", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            for e in reference_edges:
                writer.writerow([e.from_work, e.referenced_work])

    def write_work_nodes_edges(self, page_work_list: List[Any], work_node_file: Optional[str] = None, reference_edge_file: Optional[str] = None) -> None:
        """
        Write a list of Work-like objects as newline JSON node records and collect/write
        their ReferenceEdge CSV entries.
        - Converts dataclass Work objects to dicts.
        - Uses provided filenames or falls back to instance defaults.
        """
        if not page_work_list:
            return

        target_nodes = work_node_file or self.json_out_file
        target_edges = reference_edge_file or self.reference_edge_file

        # prepare node objects (convert dataclasses to dicts)
        node_objs: List[Any] = []
        # for w in page_work_list:
        #     if is_dataclass(w):
        #         node_objs.append(asdict(w))
        #     elif isinstance(w, dict):
        #         node_objs.append(w)
        #     else:
        #         # best-effort: try to serialize attributes
        #         try:
        #             node_objs.append(w.__dict__)
        #         except Exception:
        #             node_objs.append(str(w))

        # write nodes
        self.write_list(node_objs, target_nodes)

        # collect and write edges
        all_edges: List[ReferenceEdge] = []
        for w in page_work_list:
            edges = self.build_reference_edges(w)
            if edges:
                all_edges.extend(edges)

        if all_edges:
            self.write_reference_edges(all_edges, target_edges)