import re
import pandas as pd
from colorama import Fore, Style
from fuzzywuzzy import fuzz
from collections import Counter
from itertools import combinations
from dateutil import parser


def normalize_phone_number(val):
    if pd.isna(val):
        return val

    digits = re.sub(r"\D", "", str(val))

    if len(digits) < 10:
        return val  # too short, skip

    number = digits[-10:]
    code = digits[:-10]

    if code and code != "91":
        # Use Excel formula style to highlight in red
        return f'=HYPERLINK("", "{val}")'
    else:
        return f"+91 {number}"

def normalize_currency(val):
    if pd.isna(val):
        return val

    s = str(val).strip()

    # ✅ Early return if it's a percentage
    if s.endswith("%"):
        return s

    multiplier = 1
    s_lower = s.lower()

    # ✅ Detect & assign multiplier
    if any(k in s_lower for k in ["k", "thousand"]):
        multiplier = 1_000
    elif any(m in s_lower for m in ["m", "million"]):
        multiplier = 1_000_000

    # ✅ Clean up numeric part only
    s_clean = re.sub(r"[^0-9.\-]", "", s)

    try:
        return float(s_clean) * multiplier
    except:
        return val

def normalize_boolean(val):
    if pd.isna(val):
        return val

    val_clean = str(val).strip().lower()

    # Exact match for known values
    true_vals = {"true", "t", "yes", "y", "1"}
    false_vals = {"false", "f", "no", "n", "0"}

    if val_clean in true_vals:
        return True
    elif val_clean in false_vals:
        return False

    # Fallback: Try first-letter logic only if value is short
    if len(val_clean) <= 4:
        if val_clean.startswith(("t", "y", "1")):
            return True
        elif val_clean.startswith(("f", "n", "0")):
            return False

    return val  # return original if unsure



def normalize_dates(series, desired_format="%d/%m/%Y"):
    formats_found = Counter()
    parsed_dates = []

    for val in series:
        if pd.isna(val):
            parsed_dates.append(val)
            continue
        try:
            dt = parser.parse(str(val), fuzzy=True)
            fmt = dt.strftime(desired_format)
            parsed_dates.append(fmt)
            formats_found[fmt] += 1
        except:
            parsed_dates.append(val)

    print(f"{Fore.CYAN}\U0001F552 Date normalization complete using format: {desired_format}{Style.RESET_ALL}")
    return pd.Series(parsed_dates)


def clean_and_preview_categoricals(df):
    inferred = df.attrs.get("inferred_types", {})
    if not inferred:
        print(f"{Fore.RED}❌ No inferred types found. Please run inference.py first.{Style.RESET_ALL}")
        return df

    print(f"\n{Fore.MAGENTA}🔎 Categorical Value Inspection & Auto-Correction...{Style.RESET_ALL}")

    for col in df.columns:
        col_lower = col.lower()
        print(f"{Fore.BLUE}→ Processing column: {col}{Style.RESET_ALL}")

        inferred_type = inferred.get(col, "")

        # Apply format-based normalizers first
        if inferred_type == "phone":
            df[col] = df[col].apply(normalize_phone_number)
            continue
        elif inferred_type == "currency":
            print("Assuming all currency is constant")
            df[col] = df[col].apply(normalize_currency)
            continue
        elif inferred_type == "boolean":
            df[col] = df[col].apply(normalize_boolean)
            continue
        elif inferred_type == "text":
            def is_safe_for_title(val):
                if pd.isna(val):
                    return False
                val_str = str(val)
        # Check for special characters or patterns that indicate we shouldn't apply .title()
                if any(char in val_str for char in ['@', '/', '\\', '_']) or re.search(r"http|www|\.\w{2,}$", val_str, re.IGNORECASE):
                    return False
                return True

            if not re.search(r"email|e-mail|mail|username|user_name|site|url|link", col, re.IGNORECASE):
                df[col] = df[col].apply(lambda x: str(x).title() if is_safe_for_title(x) else x)
            else:
                df[col] = df[col].astype(str)

        elif inferred_type == "postal":
            df[col] = df[col].apply(lambda x: str(x).strip() if pd.notna(x) else x)
            continue
        elif inferred_type == "date":
            df[col] = normalize_dates(df[col], desired_format="%d/%m/%Y")
            continue

        # Now handle categorical typo detection
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

