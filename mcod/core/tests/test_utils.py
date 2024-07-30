import tempfile
from pathlib import Path

import pandas as pd

from mcod.core.utils import clean_columns_in_dataframe, save_df_to_xlsx


class TestCleanColumnsInDataframe:
    def test_clean_single_column(self):
        df = pd.DataFrame({"ColumnName1": [" Value1 ", "Value2", None, "Value3 "], "ColumnName2": [0, 10, 20, 30]})

        cleaned_df: pd.DataFrame = clean_columns_in_dataframe(df, "ColumnName1").reset_index(drop=True)
        expected_df = pd.DataFrame({"ColumnName1": [" Value1 ", "Value2", "Value3 "], "ColumnName2": [0, 10, 30]})
        pd.testing.assert_frame_equal(cleaned_df, expected_df)

    def test_clean_multiple_columns(self):
        df = pd.DataFrame(
            {"ColumnName1": [" Value1 ", "Value2", None, "Value3 "], "ColumnName2": [" Value4", "   ", "", "Value5"]}
        )

        cleaned_df: pd.DataFrame = clean_columns_in_dataframe(df, "ColumnName1", "ColumnName2").reset_index(drop=True)
        expected_df = pd.DataFrame({"ColumnName1": [" Value1 ", "Value3 "], "ColumnName2": [" Value4", "Value5"]})
        pd.testing.assert_frame_equal(cleaned_df, expected_df)

    def test_non_existent_column(self):
        df = pd.DataFrame({"ColumnName1": ["Value1", "Value2", "Value3"], "ColumnName2": [10, 20, 30]})
        cleaned_df: pd.DataFrame = clean_columns_in_dataframe(df, "NonExistentColumn")
        pd.testing.assert_frame_equal(df, cleaned_df)


def test_save_df_to_xlsx_smoke():
    data = {"Column1": [1, 2, 3], "Column2": ["4", "5", "6"], "Column3": [7, "8 ", None]}
    df = pd.DataFrame(data)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file_path = Path(temp_dir, "file_name.xlsx")
        # Given
        assert not temp_file_path.exists()
        # When
        save_df_to_xlsx(df, temp_file_path)
        # Then
        assert temp_file_path.exists()
