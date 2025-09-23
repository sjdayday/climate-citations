import json
from typing import List, Any


class NetworkFileTalker:
    """
    Simple file writer for newline-delimited JSON records.
    """

    def write_list(self, object_list: List[Any], filename: str) -> None:
        """
        Write each object in object_list as one JSON object per line to filename.
        If the file exists, append; otherwise create it.
        """
        # open in append mode (creates file if it doesn't exist)
        with open(filename, "a", encoding="utf-8") as fh:
            for obj in object_list:
                fh.write(json.dumps(obj, ensure_ascii=False) + "\n")