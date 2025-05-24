import re
import os

class TextExtractor:
    """
    Extracts specifications from structured plain text files for various Chevrolet models.
    """
    def __init__(self, txt_path):
        if not os.path.exists(txt_path):
            raise FileNotFoundError(f"El archivo no existe: {txt_path}")
        self.txt_path = txt_path # Store path for model name heuristic
        with open(txt_path, encoding='utf-8') as f:
            self.lines = [line.rstrip() for line in f]
        
        self.model_name = None
        self.sections = {}  # For internal tracking of identified section names
        self.versions = []  # Keeps track of the latest identified version names (cleaned)
        self.results = {"model_name": None, "versions": {}}
        self._parse()

    def _clean_line(self, text):
        """Removes source tags and extra whitespace from a line or part of a line."""
        if text is None:
            return ""
        # Remove source tags like and surrounding whitespace
        text = re.sub(r'\s*\\s*', '', text)
        return text.strip()

    def _is_plausible_version_text(self, text_cleaned):
        """Checks if a given cleaned text string could be a version identifier."""
        if not text_cleaned:
            return False
        # Filter out overly long strings or purely numeric strings that are unlikely versions
        if len(text_cleaned) > 45 or text_cleaned.isdigit():
            return False
        
        # General keywords or structure hinting it's a version/trim
        # Matches "1.0T LTZ MT", "1.5L LT MT", "TAHOE Z71 5.3L AWD", "LT", "RS", etc.
        if re.search(r'(\d\.\d[LT])|(\b(MT|AT|AWD|LWD|FWD)\b)|(\b(LTZ|RS|PRIME|Z71|LT|XLS|SLE)\b)', text_cleaned, re.IGNORECASE):
            return True
        
        # Also allow for mostly uppercase/numeric short strings (e.g., common trim names)
        if re.match(r'^[A-Z0-9\s\./-]{2,}$', text_cleaned) and len(text_cleaned.split()) < 5: # At least 2 chars, < 5 words
             return True
        return False

    def _is_version_header_line(self, raw_line_parts):
        """
        Determines if a line, split into parts, constitutes a version header.
        It checks if all parts are plausible version texts.
        """
        # Clean each part first, and filter out any parts that become empty after cleaning
        cleaned_parts = [self._clean_line(p) for p in raw_line_parts if self._clean_line(p)]
        
        if not cleaned_parts:  # No content after cleaning
            return False
        
        # Avoid misinterpreting a common section header (like "INTERIOR") as a version if it's the only item on the line
        if len(cleaned_parts) == 1:
            known_single_word_sections_upper = {
                "INTERIOR", "EXTERIOR", "SEGURIDAD", "DIMENSIONES", "TECNOLOGÍA", "MOTOR", "COLORES" # Add more if needed
            }
            # Check against common full section headers as well
            known_multi_word_sections_upper = {
                "ESPECIFICACIONES MECÁNICAS Y TÉCNICAS", "COLORES DISPONIBLES", "ESPECIFICACIONES TECNICAS"
            }
            if cleaned_parts[0].upper() in known_single_word_sections_upper or \
               cleaned_parts[0].upper() in known_multi_word_sections_upper :
                return False
        
        # All non-empty cleaned parts must look like version texts
        return all(self._is_plausible_version_text(p) for p in cleaned_parts)

    def _parse(self):
        # 1. Parse Model Name
        self.model_name = "Unknown Model" # Default
        # List of regex patterns for common boilerplate lines to ignore during model name search
        # List of regex patterns for common boilerplate lines to ignore during model name search
        boilerplate_model_patterns = [
            r"\\",                                       # Backslash
            r"^\s*$",                                    # Empty lines
            r"www\.chevrolet\.com\.pe",                  # Specific URL
            r"^\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?$",     # Numbers like 100.000 or 5.00
            r"^\d{1,3}(?:[.,]\d{3})*$",                  # Numbers like 100.000 or 5
            r"^\d{1,2}$",                                # Short numbers like 5
            r"CONNECTED BY",                             # Text: CONNECTED BY
            r"ALL NEW"                                   # Prefix: ALL NEW
        ]

        
        last_line_was_all_new = False
        # Scan the first few lines (e.g., up to 15) of the file for the model name
        for line_idx in range(min(15, len(self.lines))):
            original_line_content = self.lines[line_idx]
            # Clean the line content for checking against boilerplate patterns
            line_for_check = self._clean_line(original_line_content)

            if not line_for_check:  # Skip if line is empty after cleaning
                continue

            # Check if the cleaned line matches any boilerplate pattern
            is_boilerplate = any(re.search(pattern, line_for_check, re.IGNORECASE) for pattern in boilerplate_model_patterns)

            if is_boilerplate:
                if line_for_check.upper() == "ALL NEW": # If "ALL NEW" is found
                    last_line_was_all_new = True      # Set flag to look for model name in next line
                # Continue to next line if current one is boilerplate
                continue 
            
            # If the previous line was "ALL NEW", this non-boilerplate line is the model name
            if last_line_was_all_new:
                self.model_name = line_for_check
                break # Model name found
            
            # If not boilerplate and not immediately after "ALL NEW",
            # consider it a candidate for model name if it's reasonably short
            if len(line_for_check.split()) < 5 and len(line_for_check) < 50:
                self.model_name = line_for_check
                break # Model name found
        
        # Fallback: If model name is still "Unknown Model", try to infer from filename
        if self.model_name == "Unknown Model":
            fn_lower = os.path.basename(self.txt_path).lower()
            if "onix" in fn_lower: self.model_name = "ONIX TURBO MY25"
            elif "sail" in fn_lower: self.model_name = "NUEVO SAIL" # Or simply "SAIL"
            elif "tahoe" in fn_lower: self.model_name = "TAHOE"
            
        self.results['model_name'] = self.model_name

        # --- Main parsing loop ---
        current_section = None
        current_versions = [] # Holds the cleaned version names for the current context

        for line_content_original in self.lines:
            # Clean the full line for some checks, but original is used for splitting to preserve structure
            cleaned_line_full = self._clean_line(line_content_original)

            # Skip lines that are entirely empty after cleaning or are known footers/disclaimers
            if not cleaned_line_full or \
               cleaned_line_full.startswith("*Equipamiento disponible") or \
               "GM Chile se reserva el derecho" in cleaned_line_full or \
               "General Motors Perú S.A. se reserva el derecho" in cleaned_line_full or \
               cleaned_line_full.startswith("*Las capacidades y funcionalidades"):
                continue

            # Attempt to detect a version header line
            # Versions are typically separated by two or more spaces
            raw_columns = re.split(r"\s{2,}", line_content_original.rstrip())
            
            if self._is_version_header_line(raw_columns):
                # Extract cleaned version names, filtering out any that become empty
                current_versions = [self._clean_line(p) for p in raw_columns if self._clean_line(p)]
                self.versions = current_versions # Store the latest set of versions
                # Initialize (or ensure) entries for these versions in the results
                for v_name in current_versions:
                    self.results['versions'].setdefault(v_name, {})
                # When new versions are found, they apply to subsequent data.
                # Do not reset current_section here, as versions might be listed under an existing section.
                continue # Processed as version line, move to next line

            # Attempt to detect a section header
            # A section header is typically an all-uppercase line, often a single "column" of text.
            # We check the cleaned version of the first raw column.
            if raw_columns: # Ensure there's at least one column
                potential_section_name_cleaned = self._clean_line(raw_columns[0])
                if len(raw_columns) == 1 and potential_section_name_cleaned.isupper():
                    # Verify it's not actually a single, all-caps version name
                    if not self._is_version_header_line([potential_section_name_cleaned]): # Pass as a list
                        current_section = potential_section_name_cleaned
                        self.sections[current_section] = [] # Track identified sections (optional use)
                        # Initialize this section for all current_versions if not already present
                        if current_versions:
                            for v_name in current_versions:
                                self.results['versions'].setdefault(v_name, {}).setdefault(current_section, {})
                        continue # Processed as section line, move to next line

            # Parse specification rows if a section and versions are currently active
            if current_section and current_versions:
                # This part adheres to the original script's logic: spec name and its values are on the same line.
                # Split the original line by 2+ spaces to get potential spec name and value columns.
                spec_parts_raw = re.split(r"\s{2,}", line_content_original.rstrip())

                # Expect at least spec_name + one value for each version
                if len(spec_parts_raw) >= 1 + len(current_versions):
                    spec_key_cleaned = self._clean_line(spec_parts_raw[0])
                    
                    if not spec_key_cleaned: # If spec name is empty after cleaning, skip
                        continue

                    # Extract the raw value parts corresponding to the number of current versions
                    value_parts_raw = spec_parts_raw[1 : 1 + len(current_versions)]
                    # Clean each extracted raw value part
                    values_cleaned = [self._clean_line(val_raw) for val_raw in value_parts_raw]

                    # Ensure we have the correct number of values after potential cleaning
                    if len(values_cleaned) == len(current_versions):
                        for version_name, spec_value in zip(current_versions, values_cleaned):
                            # Ensure the version and section dicts exist
                            version_data_dict = self.results['versions'].setdefault(version_name, {})
                            section_data_dict = version_data_dict.setdefault(current_section, {})
                            section_data_dict[spec_key_cleaned] = spec_value
                # else:
                    # Lines that do not fit the "spec_name val1 val2..." structure (for the current number of versions)
                    # are currently ignored by this adapted logic if they are within a data section.
                    # This means specs where the name is on one line and values on another (common in sail.txt)
                    # will not be fully captured by this specific adaptation.
                    # A more complex parsing state (e.g., remembering a pending spec name) would be needed.
                    pass

    def get_results(self):
        """Returns the extracted specification results."""
        return self.results
