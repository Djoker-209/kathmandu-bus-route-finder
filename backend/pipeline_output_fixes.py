"""
Fixes for clean_data.py's output stage.
"""

import pandas as pd

OPERATOR_VERIFIABLE_COLUMNS = ["rating", "contact_number"]
EMPTY_SENTINELS = {"", "nan", "none", "n/a", "unknown"}


def _is_empty(value) -> bool:
    if pd.isna(value):
        return True
    return str(value).strip().lower() in EMPTY_SENTINELS


def compute_unverified_fields(df, verifiable_columns=OPERATOR_VERIFIABLE_COLUMNS):
    def row_unverified(row):
        empties = [col for col in verifiable_columns if _is_empty(row.get(col))]
        return "{" + ",".join(empties) + "}"
    return df.apply(row_unverified, axis=1)


def fix_ward_column(df, column="ward"):
    if column not in df.columns:
        return df

    def clean(value):
        if pd.isna(value):
            return ""
        s = str(value).strip()
        if s.endswith(".0"):
            s = s[:-2]
        return s

    df[column] = df[column].apply(clean)
    return df


def apply_output_fixes(operators_df, stops_df):
    if "unverified_fields" in operators_df.columns:
        operators_df["unverified_fields"] = compute_unverified_fields(operators_df)
    stops_df = fix_ward_column(stops_df, column="ward")
    return operators_df, stops_df
