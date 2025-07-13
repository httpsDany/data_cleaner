import re
import pandas as pd
from colorama import Fore, Style
from fuzzywuzzy import fuzz
from collections import Counter
from itertools import combinations


def clean_and_preview_categoricals(df):
    inferred = df.attrs.get("inferred_types", {})
    if not inferred:
        print(f"{Fore.RED}❌ No inferred types found. Please run inference.py first.{Style.RESET_ALL}")
        return df

    print(f"\n{Fore.MAGENTA}🔎 Categorical Value Inspection & Auto-Correction...{Style.RESET_ALL}")

    for col, inferred_type in inferred.items():
        if inferred_type != "categorical":
            continue

        print(f"\n{Fore.BLUE}→ Checking column: {col}{Style.RESET_ALL}")

        # Step 1: Build original row-wise dictionary
        check_dictionary = df[col].to_dict()

        # Step 2: Lowercase and strip all values temporarily for cleaning
        lowered_cleaned = {k: str(v).strip().lower() for k, v in check_dictionary.items() if pd.notna(v)}

        # Step 3: Extract unique values matching text pattern
        regex_pattern = re.compile(r"^[a-zA-Z\s]+$")
        unique_cleaned = list({v for v in lowered_cleaned.values() if regex_pattern.match(v)})

        print(f"{Fore.CYAN}🔍 Unique cleaned values (matching pattern):{Style.RESET_ALL}")
        print(unique_cleaned)

        # Step 4: Build frequency map to identify common values
        cleaned_series = pd.Series(lowered_cleaned.values())
        freq_map = Counter(cleaned_series)
        common_values = [val for val, count in freq_map.items() if count > 1]

        # Step 5: Fuzzy match rare values to common ones
        typo_threshold = 85
        correction_map = {}
        for val in unique_cleaned:
            if val in common_values:
                continue

            best_match = None
            best_score = 0
            for ref in common_values:
                score = fuzz.ratio(val, ref)
                if score >= typo_threshold and score > best_score:
                    best_match = ref
                    best_score = score

            if best_match:
                correction_map[val] = best_match

        # Step 6: Apply correction and re-title
        corrected = {}
        for idx, val in lowered_cleaned.items():
            fixed = correction_map.get(val, val)
            corrected[idx] = fixed.title()

        # Step 7: Restore values in original DataFrame based on row index
        for idx, val in corrected.items():
            df.at[idx, col] = val

        if correction_map:
            print(f"{Fore.YELLOW}⚠️ Auto-corrected fuzzy typos:{Style.RESET_ALL}")
            for typo, correct in correction_map.items():
                print(f"  - '{typo}' → '{correct}'")
        else:
            print(f"{Fore.GREEN}✅ No typos found to fix in column: {col}{Style.RESET_ALL}")

    return df

