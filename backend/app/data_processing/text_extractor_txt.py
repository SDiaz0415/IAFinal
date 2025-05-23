import re
import os

class TextExtractor:
    """
    Extracts specifications from a structured plain text file for Chevrolet Onix Turbo MY25.
    """
    def __init__(self, txt_path):
        if not os.path.exists(txt_path):
            raise FileNotFoundError(f"El archivo no existe: {txt_path}")
        with open(txt_path, encoding='utf-8') as f:
            self.lines = [line.rstrip() for line in f]
        self.model_name = None
        self.sections = {}
        self.versions = []
        self.results = {"model_name": None, "versions": {}}
        self._parse()

    def _parse(self):
        # Identify model name from the first non-empty line
        for line in self.lines:
            if line.strip():
                self.model_name = line.strip()
                break
        self.results['model_name'] = self.model_name

        current_section = None
        current_versions = []

        # Pattern to detect the version header line (e.g., '1.0T LTZ MT   1.0T RS MT   1.0T PRIME AT')
        version_pattern = re.compile(r"(\d\.\dT\s+\w+(?:\s+MT|\s+AT))")

        for i, line in enumerate(self.lines):
            # Detect section header: uppercase word or words without multiple columns
            if line.isupper() and not version_pattern.search(line):
                current_section = line.strip()
                self.sections[current_section] = []
                continue

            # Detect versions line: at least two version patterns
            if version_pattern.search(line):
                cols = re.split(r"\s{2,}", line.strip())
                if len(cols) > 1 and all(version_pattern.match(v) for v in cols):
                    current_versions = cols
                    self.versions = current_versions
                    # Initialize version entries
                    for v in self.versions:
                        self.results['versions'][v] = {}
                    continue

            # Parse specification rows under a section if versions are known
            if current_section and current_versions:
                if not line.strip():
                    continue  # skip empty lines
                parts = re.split(r"\s{2,}", line)
                # Expect at least spec name + values for each version
                if len(parts) >= 1 + len(current_versions):
                    spec_key = parts[0].strip()
                    values = parts[1:1 + len(current_versions)]
                    for v, val in zip(current_versions, values):
                        # Initialize nested section dict
                        sec_dict = self.results['versions'][v].setdefault(current_section, {})
                        sec_dict[spec_key] = val.strip()

    def get_results(self):
        """Returns the extracted specification results."""
        return self.results


# if __name__ == '__main__':
#     import json
#     extractor = TextExtractor('202411-03-onix-turbo-my25(1).txt')
#     results = extractor.get_results()
#     print(json.dumps(results, ensure_ascii=False, indent=2))