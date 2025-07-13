import pandas as pd
import re
from colorama import Fore, Style
from dateutil import parser
from ydata_profiling import ProfileReport
from cleaning.prompts import ask_date_format
    
def suggest_and_fix_column_types(df):
    print(f"\n{Fore.CYAN}🔍 Analyzing column types with YData Profiling...{Style.RESET_ALL}")
    for col in df.columns:
        if df[col].dropna().apply(lambda x: str(x).strip().replace(" ", "").isdigit()).all():
            df[col] = df[col].apply(lambda x: re.sub(r"\D", "", str(x)) if pd.notna(x) else x)
            df[col] = pd.to_numeric(df[col], errors="coerce")

    profile = ProfileReport(df, minimal=True, explorative=True, infer_dtypes=True)
    desc = profile.get_description()
    variables = desc.variables

    inferred_types = {}

    for col in df.columns:
        dtype = str(df[col].dtype)
        semantic = variables.get(col, {}).get("semantic_type", [])
        suggested_type = variables.get(col, {}).get("type", "Unknown")

        df[col] = df[col].apply(lambda x: str(x).strip() if pd.notnull(x) else x)

        # Semantic matching
        if "date" in str(semantic).lower() or re.search(r"date", col, re.IGNORECASE):
            sample = df[col].dropna().astype(str).head(30)
            parseable = 0
            for val in sample:
                try:
                    parser.parse(val, dayfirst=True, fuzzy=True)
                    parseable += 1
                except:
                    continue

            if parseable >= len(sample) * 0.8:
                # Now apply full parse to column
                date_format = ask_date_format()
                def safe_parse_format(x):
                    try:
                        parsed=parser.parse(str(x), dayfirst=True, fuzzy=True)
                        return parsed.strftime(date_format)
                    except:
                        return x
                df[col] = df[col].apply(lambda x: safe_parse_format(x) if pd.notna(x) else x)
                inferred_types[col] = "date"
                print(f"{Fore.GREEN}✅ Auto-detected '{col}' as datetime (semantic: date){Style.RESET_ALL}")
                continue
        
        elif semantic and ("text" in semantic[0].lower() or "string" in semantic[0].lower()):
            df[col] = df[col].astype(str)
            inferred_types[col] = "text"
            print(f"{Fore.GREEN}✅ Auto-detected '{col}' as string (semantic: {semantic[0]}){Style.RESET_ALL}")
            continue

        elif semantic and "numeric" in semantic[0].lower():
            df[col] = pd.to_numeric(df[col], errors="coerce")
            inferred_types[col] = "numeric"
            print(f"{Fore.GREEN}✅ Auto-detected '{col}' as numeric (semantic: {semantic[0]}){Style.RESET_ALL}")
            continue
        # Custom rule: detect phone number columns from name
        if re.search(r"phone|ph\s*no|contact", col, re.IGNORECASE):
            inferred_types[col] = "phone"
            print(f"{Fore.GREEN}✅ Auto-detected '{col}' as phone number based on column name{Style.RESET_ALL}")
            continue

        # Custom rule: detect currency from column name or content
        sample = df[col].dropna().astype(str).head(30)
        currency_matches = sum(bool(re.search(r"[\$₹€]|USD|INR|Rs", val, re.IGNORECASE)) for val in sample)

        if currency_matches >= len(sample) * 0.6 or re.search(r"salary|price|amount|cost|currency", col, re.IGNORECASE):
            inferred_types[col] = "currency"
            print(f"{Fore.GREEN}✅ Auto-detected '{col}' as currency based on name/content{Style.RESET_ALL}")
            print(f"{Fore.RED} !Assumed all values are of same currency ")
            continue


        # Fallbacks
        fallback = suggested_type.lower()
        if fallback in ["text", "string", "categorical"]:
            df[col] = df[col].astype(str)
            inferred_types[col] = "categorical" if fallback == "categorical" else "text"
            print(f"{Fore.GREEN}✅ Auto-converted '{col}' to string based on fallback type ({suggested_type}){Style.RESET_ALL}")
        
        elif fallback in ["numeric", "integer", "float"]:
            df[col] = df[col].apply(lambda x: re.sub(r"\s+", "", str(x)) if pd.notna(x) else x)
            df[col] = pd.to_numeric(df[col], errors="coerce")
            inferred_types[col] = "numeric"
            print(f"{Fore.GREEN}✅ Auto-converted '{col}' to numeric after stripping spaces based on fallback type ({suggested_type}){Style.RESET_ALL}")

        elif fallback == "datetime":
            def try_parse(val):
                try:
                    return parser.parse(str(val), dayfirst=True, fuzzy=True)
                except:
                    return pd.NaT

            df[col] = df[col].apply(try_parse)
            inferred_types[col] = "datetime"
            print(f"{Fore.GREEN}✅ Auto-converted '{col}' to datetime based on fallback type ({suggested_type}){Style.RESET_ALL}")

    
        elif fallback == "boolean":
            inferred_types[col] = "boolean"
            print(f"{Fore.GREEN}✅ Auto-converted '{col}' to bool based on fallback type ({suggested_type}){Style.RESET_ALL}")
        else:
            inferred_types[col] = "unknown"
            print(f"{Fore.YELLOW}⚠️ Column '{col}' has unclear type: {suggested_type}. Leaving unchanged.{Style.RESET_ALL}")

    # ✅ Key line: attach inferred types to df
    df.attrs["inferred_types"] = inferred_types

    return df

