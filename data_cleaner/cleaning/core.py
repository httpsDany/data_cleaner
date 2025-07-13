import pandas as pd
import re
from colorama import Fore, Style
from cleaning.prompts import (
    ask_yes_no,
    ask_custom_headers,
    ask_columns,
    select_row_to_keep
)

# ---------- HEADER CLEANING ----------

def has_symbols_or_numbers(text):
    # Ignore 'Unnamed: x' headers (we'll handle them separately)
    if str(text).lower().startswith("unnamed"):
        return False
    return bool(re.search(r'[0-9@#$%^&*()\-+=|\\/<>\[\]{}]', str(text)))

def push_headers_to_row(df):
    df.columns = [str(c) for c in df.columns]
    df.loc[-1] = df.columns  # insert headers as first row
    df.index = df.index + 1
    df = df.sort_index().reset_index(drop=True)
    return df

def check_and_fix_headers(df):
    print(f"\n{Fore.CYAN}Checking headers...{Style.RESET_ALL}")
    headers = list(df.columns)

    # Drop columns where header is blank AND all values are null
    to_drop = [col for col in df.columns if str(col).strip() == "" and df[col].isnull().all()]
    if to_drop:
        print(f"{Fore.YELLOW}⚠️ Dropping {len(to_drop)} fully empty columns: {to_drop}{Style.RESET_ALL}")
        df = df.drop(columns=to_drop)
    headers=list(df.columns)

    # 1. Check for symbols or numbers
    if any(has_symbols_or_numbers(h) for h in headers):
        print(f"{Fore.YELLOW}⚠️ Invalid headers found (symbols/numbers):{Style.RESET_ALL} {headers}")
        df = push_headers_to_row(df)
        df.columns = ask_custom_headers(len(df.columns))
        return df

def check_and_fix_headers(df):
    print(f"\n{Fore.CYAN}Checking headers...{Style.RESET_ALL}")

    # Step 1: Drop any column where the header is blank or unnamed AND all values are null
    cols_to_drop = []
    for col in df.columns:
        header_str = str(col).strip().lower()
        if (header_str == "" or header_str.startswith("unnamed")) and df[col].isnull().all():
            cols_to_drop.append(col)

    if cols_to_drop:
        print(f"{Fore.YELLOW}⚠️ Dropping {len(cols_to_drop)} fully empty columns: {cols_to_drop}{Style.RESET_ALL}")
        df = df.drop(columns=cols_to_drop)

    # Step 2: Refresh headers list AFTER dropping
    headers = list(df.columns)

    # Step 3: Check for symbols/numbers in headers
    if any(has_symbols_or_numbers(h) for h in headers):
        print(f"{Fore.YELLOW}⚠️ Invalid headers found (symbols/numbers):{Style.RESET_ALL} {headers}")
        df = push_headers_to_row(df)
        df.columns = ask_custom_headers(len(df.columns))
        return df

    # Step 4: Identify blank/unnamed headers that still have data in them
    missing = [
        i for i, h in enumerate(headers)
        if (str(h).strip() == "" or str(h).lower().startswith("unnamed"))
    ]
    if missing:
        print(f"{Fore.YELLOW}⚠️ Some headers are blank or unnamed: {missing}{Style.RESET_ALL}")
        if ask_yes_no("Would you like to manually enter new headers?"):
            for idx in missing:
                col_data = df.iloc[:5, idx].tolist()
                print(f"\n{Fore.CYAN}🔎 Preview of column {idx} (first 5 cells):{Style.RESET_ALL}")
                for i, val in enumerate(col_data):
                    print(f"  {i+1}) {val if pd.notna(val) else 'NaN'}")
                name = ask_custom_headers(1)[0]
                df.columns.values[idx] = name
            print(f"{Fore.GREEN}✅ Headers updated: {list(df.columns)}{Style.RESET_ALL}")
            return df
        else:
            df = push_headers_to_row(df)
            df.columns = ask_custom_headers(len(df.columns))
            return df

    # Step 5: Final confirmation
    print(f"{Fore.CYAN}Detected headers:{Style.RESET_ALL}")
    for i, h in enumerate(headers):
        print(f"{i+1}) {h}")
    print(f"\n{Fore.CYAN}First row of data:{Style.RESET_ALL}")
    print(df.iloc[0])

    if ask_yes_no("Do the current headers look correct?"):
        return df

    print(f"{Fore.YELLOW}→ Treating current headers as first row data.{Style.RESET_ALL}")
    df = push_headers_to_row(df)
    df.columns = ask_custom_headers(len(df.columns))
    return df

# ---------- DUPLICATE HANDLING ----------

def handle_duplicates_by_column(df):
    if not ask_yes_no("Is there a unique column (or set of columns) to identify duplicates?"):
        return df

    columns = ask_columns(df.columns)
    if not columns:
        return df

    dupes = df[df.duplicated(subset=columns, keep=False)]

    if dupes.empty:
        print(f"{Fore.GREEN}✅ No duplicates found based on selected column(s).{Style.RESET_ALL}")
        return df

    print(f"{Fore.YELLOW}⚠️ Found {len(dupes)} potential duplicates:{Style.RESET_ALL}")
    skip_indices = set()

    for idx, row in dupes.iterrows():
        if idx in skip_indices:
            continue

        match = df[df[columns].eq(row[columns].values).all(axis=1)]

        if len(match.drop_duplicates()) == 1:
            df.drop(match.index[1:], inplace=True)
            skip_indices.update(match.index)
        else:
            print(f"\n{Fore.RED}⚠️ Duplicate key found, but rows differ:{Style.RESET_ALL}")
            to_keep = select_row_to_keep(match)
            to_drop = match.index.difference([to_keep])
            df.drop(index=to_drop, inplace=True)
            skip_indices.update(match.index)

    print(f"{Fore.GREEN}✅ Duplicate handling complete.{Style.RESET_ALL}")
    return df.reset_index(drop=True)

# ---------- NULL HANDLING ----------

def handle_null_rows(df):
    null_rows = df[df.isnull().any(axis=1)]
    null_count = df.isnull().sum().sum()

    if null_rows.empty:
        print(f"{Fore.GREEN}✅ No null values found.{Style.RESET_ALL}")
        return df

    print(f"{Fore.YELLOW}⚠️ Found {null_count} null values in {len(null_rows)} rows.{Style.RESET_ALL}")
    # Print rows with red-colored NaNs
    for idx, row in null_rows.iterrows():
        pretty = []
        for val in row.values:
            if pd.isna(val):
                pretty.append(f"{Fore.RED}{Style.BRIGHT}NaN{Style.RESET_ALL}")
            else:
                pretty.append(str(val))
        print(f"{idx}\t" + "\t".join(pretty))

    if ask_yes_no("Would you like to delete all rows with null values?"):
        df = df.dropna().reset_index(drop=True)
        print(f"{Fore.GREEN}✅ Rows with nulls deleted.{Style.RESET_ALL}")
    else:
        print(f"{Fore.CYAN}These rows will be highlighted in the Excel output.{Style.RESET_ALL}")
        df.attrs["highlight_nulls"] = null_rows.index.tolist()

    return df

