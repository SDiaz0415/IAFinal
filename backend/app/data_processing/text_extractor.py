import re
import fitz
import os

class PDFMechanicalSpecExtractor:
    """
    Extracts mechanical and technical specifications from a structured text representation of a PDF.
    It assumes the input 'full_content_string' is derived from a PDF and contains markers like
    '' and '--- PAGE Y ---', with tables often preceded by 'The following table:'.
    """

    def __init__(self, pdf_input):
        """
        Initializes the extractor with either a path to a PDF, a file-like object, or a raw text string.

        Args:
            pdf_input (str | file-like object): Path to PDF, file-like object, or full text string.
        """
        self.full_content = self._load_pdf_or_text(pdf_input)
        print( self.full_content )
        self.sources = self._parse_sources()

    def _load_pdf_or_text(self, source):
        """
        Loads and converts PDF to text if a path or file object is passed.
        Otherwise, assumes it's raw text.

        Returns:
            str: The full text content of the PDF.
        """
        if isinstance(source, str) and os.path.exists(source):
            # Es una ruta al archivo PDF
            with fitz.open(source) as doc:
                return self._extract_text_with_page_markers(doc)
        elif hasattr(source, "read"):  # file-like object
            try:
                file_bytes = source.read()
                with fitz.open(stream=file_bytes, filetype="pdf") as doc:
                    return self._extract_text_with_page_markers(doc)
            except Exception as e:
                raise ValueError(f"Error al leer el archivo PDF: {str(e)}")
        elif isinstance(source, str):
            # Asume que es el texto plano del PDF
            return source
        else:
            raise TypeError("pdf_input debe ser una ruta, un archivo o un string de texto")

    def _extract_text_with_page_markers(self, doc):
        """
        Extrae texto de un documento PyMuPDF, agregando marcadores de página.

        Args:
            doc: Documento abierto con fitz.open()

        Returns:
            str: Texto con separadores de página.
        """
        text = ""
        for i, page in enumerate(doc, 1):
            text += page.get_text() + f"\n|--- PAGE {i} ---|\n"
        return text

    def _parse_sources(self):
        sources = {}
        chunks = re.split(r'\|--- PAGE \d+ ---\|', self.full_content)
        for i, chunk in enumerate(chunks):
            content = chunk.strip()
            if content:
                sources[i] = content
        return sources

    def _parse_table_string(self, table_str):
        """
        Parses a string representation of a table into a list of lists (rows and columns).
        The table string is expected to be CSV-like, with quoted cells.

        Args:
            table_str (str): The string containing the table data.

        Returns:
            list: A list of lists, where each inner list represents a row and its elements are cell values.
        """
        # Remove common table preamble
        table_str = table_str.replace("The following table:", "").strip()
        lines = table_str.splitlines()
        parsed_table = []
        for line in lines:
            if not line.strip():
                continue
            # Regex to split by comma, but not if comma is inside double quotes
            # Also strips surrounding quotes from each part.
            parts = [p.strip().strip('"') for p in re.split(r',(?=(?:[^"]*"[^"]*")*[^"]*$)', line)]
            if parts:
                parsed_table.append(parts)
        return parsed_table

    def _find_versions_from_text_sources(self, candidate_source_ids):
        """
        Attempts to identify vehicle version names from specified text source blocks.
        This is typically used for documents where versions are listed above specification tables.

        Args:
            candidate_source_ids (list): A list of source IDs to scan for version names.

        Returns:
            list: A list of identified version names (strings).
        """
        versions = []
        # Regex pattern to identify typical version/trim names
        # Looks for lines that seem like model trims (e.g., "1.5L LT MT", "TAHOE Z71 5.3L AWD")
        version_pattern = re.compile(
            r"^(?P<version>[\w\s./-]+(?:LTZ|LT|RS|PRIME|Z71|AWD|MT|AT)[\w\s./-]*)$",
            re.MULTILINE | re.IGNORECASE
        )

        for src_id in candidate_source_ids:
            content = self.sources.get(src_id, "")
            content = content.replace("The following table:", "").strip() # Clean up
            
            # Split content by newlines to evaluate each line as a potential version string
            possible_version_lines = content.splitlines()
            for line in possible_version_lines:
                line = line.strip()
                if not line: continue

                match = version_pattern.match(line)
                if match:
                    version_name = match.group("version").strip()
                    # Further heuristics to qualify a version name
                    if 1 < len(version_name.split()) < 6 and len(version_name) > 3 and len(version_name) < 30:
                         # Avoid common section titles mistaken for versions
                        if not any(kw in version_name.lower() for kw in ["interior", "exterior", "seguridad", "tipo de", "motor", "transmisión"]):
                            versions.append(version_name)
        
        return list(dict.fromkeys(versions)) # Deduplicate while preserving order

    def extract_mechanical_specifications(self):
        """
        Main extraction method. Identifies relevant sections (specifications, dimensions),
        determines vehicle versions, parses tables, and consolidates the data.

        Returns:
            dict: A dictionary containing the extracted model name and a nested dictionary
                  of versions, each with its specifications.
                  Example:
                  {
                      "model_name": "Chevrolet Tahoe",
                      "versions": {
                          "TAHOE Z71 5.3L AWD": {
                              "Potencia (HP @rpm)": "355 @5600", ...
                          }, ...
                      }
                  }
        """
        results = {"model_name": None, "versions": {}}

        # Attempt to determine model name
        if "TAHOE" in self.full_content: results["model_name"] = "Chevrolet Tahoe"
        elif "SAIL" in self.full_content: results["model_name"] = "Chevrolet Sail"
        elif "ONIX TURBO" in self.full_content: results["model_name"] = "Chevrolet Onix Turbo"
        
        # Keywords for sections to extract
        spec_section_keywords = ["ESPECIFICACIONES MECÁNICAS Y TÉCNICAS", "ESPECIFICACIONES TECNICAS"]
        dim_section_keywords = ["DIMENSIONES Y CAPACIDADES", "DIMENSIONES"]
        all_relevant_keywords = spec_section_keywords + dim_section_keywords

        # Find all source IDs that are titles of relevant sections or tables within them
        relevant_table_source_ids = []
        current_section_title_source_id = None
        active_section_keywords = []

        for src_id in sorted(self.sources.keys()):
            content = self.sources[src_id]
            
            # Check if this source content is a title for a relevant section
            is_title_for_relevant_section = False
            for keyword_set in [spec_section_keywords, dim_section_keywords]:
                if any(kw.lower() in content.lower() for kw in keyword_set) and \
                   "The following table:" not in content.lower():
                    is_title_for_relevant_section = True
                    active_section_keywords = keyword_set # Remember which section we are in
                    current_section_title_source_id = src_id
                    break
            
            # Check if this source contains a table marker
            is_table_marker_present = "The following table:" in content.lower()

            if is_table_marker_present:
                # If this source itself is a table AND its title matches relevant keywords
                if any(kw.lower() in content.lower() for kw in all_relevant_keywords):
                    relevant_table_source_ids.append(src_id)
                    current_section_title_source_id = None # Consumed this title/table block
                # Or if this table follows a relevant title found in the *previous* source block
                elif current_section_title_source_id == src_id -1 and \
                     any(kw.lower() in self.sources.get(current_section_title_source_id, "").lower() for kw in active_section_keywords):
                    relevant_table_source_ids.append(src_id)
                    current_section_title_source_id = None # Consumed association

        # Try to find global versions from text sources around the first identified spec table
        global_versions = []
        if relevant_table_source_ids:
            first_spec_table_sid = min(relevant_table_source_ids)
            # Look in a window of 3 sources before the first spec table
            version_candidate_sids = [sid for sid in range(max(0, first_spec_table_sid - 3), first_spec_table_sid)]
            global_versions = self._find_versions_from_text_sources(version_candidate_sids)

        # Process each identified table
        for table_sid in relevant_table_source_ids:
            table_content_str = self.sources.get(table_sid, "")
            parsed_table_rows = self._parse_table_string(table_content_str)

            if not parsed_table_rows:
                continue

            versions_for_this_table = []
            data_rows_start_index = 0 # From which row the actual data starts (0 if no version header row)

            # Check if the first row of this table defines version names as columns
            header_row = parsed_table_rows[0]
            if len(header_row) > 1:
                # Heuristic: first cell is a label, or empty/generic, and subsequent cells are version names
                first_cell_is_label = header_row[0].strip() != "" and not any(
                    kw in header_row[0].lower() for kw in ["mt", "at", "lt", "awd", "z71", "rs"] # Avoid first cell being a version itself
                )
                first_cell_is_generic_or_empty = header_row[0].strip() == "" or \
                                               header_row[0].lower() in ["modelo", "versión", "tipo", "especificaciones"]

                if first_cell_is_label or first_cell_is_generic_or_empty:
                    potential_version_names_in_header = [v.strip() for v in header_row[1:] if v.strip()]
                    
                    # Validate if these look like actual version names
                    are_valid_versions = False
                    if potential_version_names_in_header:
                        are_valid_versions = all(
                            re.search(r'(MT|AT|LTZ|RS|PRIME|AWD|Z71|LS|LT|PREMIER)', v, re.IGNORECASE) and
                            not v.isnumeric() and 2 < len(v) < 25
                            for v in potential_version_names_in_header
                        )
                    
                    if are_valid_versions:
                        versions_for_this_table = potential_version_names_in_header
                        data_rows_start_index = 1 # Skip this header row for data extraction
                        for v_name in versions_for_this_table: # Ensure version keys exist
                            if v_name not in results["versions"]: results["versions"][v_name] = {}
            
            # If table-specific versions were not found in its header, use global_versions
            if not versions_for_this_table:
                versions_for_this_table = global_versions
            
            # Fallback for single-version documents like Tahoe if no versions identified yet
            if not versions_for_this_table and results["model_name"] == "Chevrolet Tahoe":
                tahoe_key = "TAHOE Z71 5.3L AWD" # Default/known key for Tahoe
                versions_for_this_table = [tahoe_key]
                if tahoe_key not in results["versions"]: results["versions"][tahoe_key] = {}
            
            # If still no versions, and table has multiple data columns, it's ambiguous
            if not versions_for_this_table:
                # If table is 2-column (key-value), assume a single default version
                if len(parsed_table_rows[0]) == 2 and data_rows_start_index == 0:
                     default_key = "default_version"
                     versions_for_this_table = [default_key]
                     if default_key not in results["versions"]: results["versions"][default_key] = {}
                else: # Cannot reliably process multi-column data without version context
                    continue 

            # Extract data from rows
            for row_num in range(data_rows_start_index, len(parsed_table_rows)):
                row_cells = parsed_table_rows[row_num]
                if not row_cells: continue

                spec_key = ""
                spec_values_start_col = -1

                if len(row_cells) == 1: # Row has only one cell, assumed to be the spec key
                    spec_key = row_cells[0].strip()
                elif row_cells[0].strip() == "" and len(row_cells) > 1: # First cell empty, spec key is in the second cell
                    spec_key = row_cells[1].strip()
                    spec_values_start_col = 2 # Data values would start from 3rd cell
                else: # Standard: spec key is in the first cell
                    spec_key = row_cells[0].strip()
                    spec_values_start_col = 1 # Data values start from 2nd cell
                
                if not spec_key: continue # Skip if no valid specification key

                if len(versions_for_this_table) == 1: # Single version context
                    version_name = versions_for_this_table[0]
                    if version_name not in results["versions"]: results["versions"][version_name] = {}
                    
                    spec_value = ""
                    if spec_values_start_col != -1 and spec_values_start_col < len(row_cells):
                        spec_value = row_cells[spec_values_start_col].strip()
                    results["versions"][version_name][spec_key] = spec_value
                else: # Multiple versions context
                    for i, version_name in enumerate(versions_for_this_table):
                        if version_name not in results["versions"]: results["versions"][version_name] = {}
                        
                        current_value_col_index = spec_values_start_col + i
                        spec_value = ""
                        if current_value_col_index < len(row_cells):
                            spec_value = row_cells[current_value_col_index].strip()
                        results["versions"][version_name][spec_key] = spec_value
        
        # Final cleanup: remove empty version dicts or default keys if better ones were found
        if "default_version" in results["versions"] and (len(results["versions"]) > 1 or not results["versions"]["default_version"]):
            if not results["versions"]["default_version"]: # if it's empty
                del results["versions"]["default_version"]
        
        results["versions"] = {k: v for k, v in results["versions"].items() if v} # Remove entirely empty version entries

        return results