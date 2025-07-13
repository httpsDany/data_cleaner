import pandas as pd
import re
from colorama import Fore, Style
from dateutil import parser
from collections import Counter
from fuzzywuzzy import fuzz


def normalize_phone_number(val):
    if pd.isna(val):
        return val
    digits = re.sub(r"\D", "", str(val))
    if len(digits) >= 10:
        number = digits[-10:]
        code = "+" + digits[:-10] if digits[:-10] else "+91"
        return f"{code} {number}"
    return val


def normalize_currency(val):
    if pd.isna(val):
        return val
    s = str(val).replace(",", "").strip()
    if s.endswith("%"):
        return s
    s = re.sub(r"[^0-9\.\-]", "", s)
    try:
        return float(s)
    except:
        return val


def normalize_boolean(val):
    if pd.isna(val):
        return val
    val = str(val).strip().lower()
    if val.startswith(("t", "y", "1")):
        return True
    elif val.startswith(("f", "n", "0")):
        return False
    return val


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

    print(f"{Fore.CYAN}🕒 Date normalization complete using format: {desired_format}{Style.RESET_ALL}")
    return pd.Series(parsed_dates)


def get_canonical_casing(series, target):
    match = series[series.str.lower().str.strip() == target]
    return match.mode().iloc[0] if not match.empty else target.title()

def normalize_categorical_column(series, threshold=90):
    cleaned = series.copy()
    lowered = series.astype(str).str.lower().str.strip()
    freq_map = Counter(lowered)
    common_values = [val for val, count in freq_map.items() if count > 1]

    print(f"\n🔍 Fuzzy Matching Debug for column '{series.name}':")
    print(f"Common values (used as reference): {common_values}\n")

    for idx, val in series.items():
        if pd.isna(val):
            continue

        val_norm = str(val).lower().strip()

        # Direct match with canonical
        if val_norm in common_values:
            cleaned.at[idx] = get_canonical_casing(series, val_norm)
            continue

        # Fuzzy match
        best_match = None
        best_score = 0
        for target in common_values:
            score = fuzz.ratio(val_norm, target)
            if score > best_score and score >= threshold:
                best_match = target
                best_score = score

        if best_match:
            cleaned.at[idx] = get_canonical_casing(series, best_match)

    return cleaned


def normalize_column_formats(df):
    print(f"\n{Fore.MAGENTA}🔧 Normalizing column formats...{Style.RESET_ALL}")
    
    inferred_types = df.attrs.get("inferred_types", {})

    for col in df.columns:
        col_lower = col.lower()
        print(f"{Fore.BLUE}→ Processing column: {col}{Style.RESET_ALL}")

        inferred_type = inferred_types.get(col, "")

        if inferred_type == "phone":
            df[col] = df[col].apply(normalize_phone_number)

        elif inferred_type == "currency":
            print("Assuming all currency is constant")
            df[col] = df[col].apply(normalize_currency)

        elif inferred_type == "boolean":
            df[col] = df[col].apply(normalize_boolean)

        elif inferred_type == "postal":
            df[col] = df[col].apply(lambda x: str(x).strip() if pd.notna(x) else x)

        elif inferred_type == "date":
            df[col] = normalize_dates(df[col], desired_format="%d/%m/%Y")

        elif inferred_type == "categorical":
            df[col] = normalize_categorical_column(df[col])

    print(f"\n{Fore.GREEN}✅ Format normalization complete.{Style.RESET_ALL}")
    return df

