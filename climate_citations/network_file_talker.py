import json
from typing import List, Any
from json import JSONDecoder, JSONDecodeError


class NetworkFileTalker:
    """
    Simple file writer / reader for newline-delimited or concatenated JSON records.
    """

    def write_list(self, object_list: List[Any], filename: str) -> None:
        """
        Write each object in object_list as one JSON object per line to filename.
        If the file exists, append; otherwise create it.
        """
        with open(filename, "a", encoding="utf-8") as fh:
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
                # If we cannot decode at the current position, skip to the next newline
                # and try again; this effectively ignores invalid fragments.
                next_nl = text.find("\n", idx)
                if next_nl == -1:
                    # no more newlines; give up
                    break
                idx = next_nl + 1
                continue

        return objs