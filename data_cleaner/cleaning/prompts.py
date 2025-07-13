import questionary

def ask_yes_no(question):
    return questionary.confirm(question, default=True).ask()

def ask_custom_headers(count):
    headers = []
    for i in range(count):
        name = questionary.text(f"Enter name for column {i + 1}:").ask()
        headers.append(name)
    return headers

def ask_columns(column_list):
    return questionary.checkbox(
        "Select columns to check for uniqueness:",
        choices=column_list
    ).ask()

def select_row_to_keep(df_rows):
    choices = []
    for idx, row in df_rows.iterrows():
        summary = f"[{idx}] " + ", ".join(str(val) for val in row.values)
        choices.append(questionary.Choice(title=summary, value=idx))

    return questionary.select(
        "Which row would you like to KEEP?",
        choices=choices
    ).ask()

def ask_date_format():
    return questionary.select(
        "Choose your preferred date format for output:",
        choices=[
            {"name": "yyyy/mm/dd", "value": "%Y/%m/%d"},
            {"name": "dd/mm/yyyy", "value": "%d/%m/%Y"},
        ]
    ).ask()

