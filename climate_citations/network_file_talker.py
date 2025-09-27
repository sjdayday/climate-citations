from dataclasses import dataclass
import json
import csv
from dataclasses import is_dataclass, asdict
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
        print(f"NetworkFileTalker initialized with json_out_file={self.json_out_file}, reference_edge_file={self.reference_edge_file}") 

    def write_list(self, object_list: List[Any], filename: Optional[str] = None) -> None:
        """
        Write each object in object_list as one JSON object per line to filename.
        If filename is None, use self.json_out_file. Append if file exists.
        """
        target = filename or self.json_out_file
        print(f"write_list is Writing {len(object_list)} records to {target}")
        with open(target, "a", encoding="utf-8") as fh:
            for obj in object_list:
                # convert dataclass instances to plain dicts
                if is_dataclass(obj):
                    payload = asdict(obj)
                # already serializable dict
                elif isinstance(obj, dict):
                    payload = obj
                else:
                    # fallback: try object's __dict__, otherwise stringify
                    try:
                        payload = obj.__dict__
                    except Exception:
                        payload = str(obj)
                fh.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def read_file(self, filename: str, key: Optional[str] = None) -> List[Any]:
        """
        Read a file that contains one or more JSON objects. If `key` is provided,
        attempt to parse the whole file as JSON and return the value at top-level
        `key` (if present). Otherwise, fall back to streaming/concatenated JSON parsing.

        Returns a list of parsed objects (or empty list on missing file / no valid JSON).
        """
        try:
            with open(filename, "r", encoding="utf-8") as fh:
                text = fh.read()
        except FileNotFoundError:
            return []

        # If a top-level key is requested, try to parse entire document and extract it.
        if key:
            print(f"read_file: Attempting to read key '{key}' from {filename}")
            try:
                whole = json.loads(text)
                if isinstance(whole, dict) and key in whole:
                    val = whole[key]
                    print(f"read_file: Found key '{key}' with type {type(val)}")
                    # If the value is JSON text (string), try to parse it
                    if isinstance(val, str):
                        print(f"read_file: key '{key}' value is string, attempting to parse as JSON text")
                        try:
                            parsed = json.loads(val)
                            print(f"read_file: key '{key}' string parsed as JSON with type {type(parsed)}")
                            if isinstance(parsed, list):
                                print(f"read_file: key '{key}' returning list of {len(parsed)} items")
                                return parsed
                            print(f"read_file: key '{key}' returning single item list")
                            return [parsed]
                        except json.JSONDecodeError:
                            print(f"read_file: key '{key}' value is not JSON text, returning as string")
                            return [val]
                    # If it's already a list/object, return it (wrap non-list in list)
                    if isinstance(val, list):
                        print(f"read_file2: key '{key}' returning list of {len(val)} items")
                        return val
                    print(f"read_file2: key '{key}' returning single item list")
                    return [val]
            except json.JSONDecodeError:
                print(f"read_file: Failed to parse entire file as JSON, falling back to streaming parse")
                # fall through to streaming parse if top-level parse fails
                pass

        # streaming/concatenated JSON parse (existing behavior)
        print(f"read_file: Streaming parse of {filename}")
        decoder = JSONDecoder()
        objs: List[Any] = []
        idx = 0
        text_len = len(text)

        while True:
            # skip whitespace
            while idx < text_len and text[idx].isspace():
                idx += 1
            if idx >= text_len:
                break
            try:
                obj, end = decoder.raw_decode(text, idx)
                objs.append(obj)
                idx = end
            except JSONDecodeError:
                # If decoding fails at this position, skip to next newline and continue
                next_nl = text.find("\n", idx)
                if next_nl == -1:
                    break
                idx = next_nl + 1
                continue
        print(f"read_file3: Parsed {len(objs)} JSON objects from {filename}")
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
        # print(f"Writing {len(page_work_list)} nodes to {target_nodes} and edges to {target_edges}")
        # prepare node objects (convert dataclasses to dicts)
        # node_objs: List[Any] = []
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

        # write nodes -- but convert to Work objects first 
        print(f"write_work_nodes_edges: Writing {len(page_work_list)} nodes to {target_nodes}")
        self.write_list(page_work_list, target_nodes)

        # collect and write edges
        all_edges: List[ReferenceEdge] = []
        for w in page_work_list:
            edges = self.build_reference_edges(w)
            print(f"build_reference_edges: Found {len(edges)} edges for work {getattr(w, 'id', 'unknown')}")
            print(f"Edges: {edges[0]}")
            if edges:
                all_edges.extend(edges)

        if all_edges:
            print(f"write_work_nodes_edges: Writing {len(all_edges)} edges to {target_edges}")
            self.write_reference_edges(all_edges, target_edges)