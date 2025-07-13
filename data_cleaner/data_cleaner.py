import sys
import pandas as pd
from termcolor import cprint
from cleaning.inference import suggest_and_fix_column_types
from cleaning.io import load_file, save_file
from cleaning.core import (    check_and_fix_headers,
    handle_duplicates_by_column,
    handle_null_rows
)

from pyfiglet import Figlet
from colorama import init
from cleaning.format_cleaning import clean_and_preview_categoricals
init()

def show_banner(font='starwars'):
    def center_text(text, width=80):
        return "\n".join(line.center(width) for line in text.splitlines())

    figlet = Figlet(font=font)
    banner = figlet.renderText("Data Cleaner")
    centered_banner = center_text(banner)

    cprint(centered_banner, 'yellow', attrs=['bold'])

def main():
    if len(sys.argv) < 2:
        cprint("❌ Please provide the path to a CSV file.", "red")
        sys.exit(1)
    
    show_banner()

    filepath = sys.argv[1]
    df = load_file(filepath)
    
    #core.py functions
    df= check_and_fix_headers(df)
    df = suggest_and_fix_column_types(df)
    df = handle_duplicates_by_column(df)
    df = handle_null_rows(df)

    # Run type inference and fix types
    
    #format_cleaner.category
    df=clean_and_preview_categoricals(df)

    # Save the cleaned file
    output_path = filepath.replace(".", "_cleaned.", 1)
    save_file(df, output_path)
    cprint(f"\n✅ Cleaned file saved to: {output_path}", "green")


if __name__ == "__main__":
    main()

