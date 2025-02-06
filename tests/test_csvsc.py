import pytest
import json
import os
import csv
import datetime
import sys
import tempfile
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from csvsc import load_config, log_error, get_input_files, read_header, process_files
from utils.expression_evaluator import ExpressionEvaluator

# テスト用の設定ファイルを作成
@pytest.fixture(scope="session")
def test_config_file():
    config_data = {
        "input_dir": str(tempfile.mkdtemp()),
        "output_dir": str(tempfile.mkdtemp()),
        "output_filename": "output.csv",
        "input_encoding": "utf-8",
        "output_encoding": "utf-8",
        "max_rows_per_file": 2,
        "output_columns": ["column1", "column3", "new_column"],
        "add_columns": {"new_column": "$[column1] + $[column2] + $#"},
        "filter_conditions": ["@[column2] > 10"]
    }
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".json", encoding='utf-8') as f:
        json.dump(config_data, f)
        config_file = f.name
    return config_file, config_data

# テスト用のCSVファイルを作成
@pytest.fixture(scope="session")
def test_csv_files(test_config_file):
    config_file, config_data = test_config_file
    input_dir = config_data["input_dir"]
    
    csv_data1 = [
        ["column1", "column2", "column3"],
        ["1", "20", "3"],
        ["4", "5", "6"],
        ["7", "12", "9"]
    ]
    csv_data2 = [
        ["column1", "column2", "column3"],
        ["10", "15", "11"],
        ["13", "1", "14"],
        ["16", "18", "17"]
    ]
    
    file_path1 = os.path.join(input_dir, "test1.csv")
    file_path2 = os.path.join(input_dir, "test2.csv")
    
    with open(file_path1, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(csv_data1)
    with open(file_path2, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(csv_data2)
    
    return file_path1, file_path2, config_data

# 設定ファイルの読み込みテスト
def test_load_config(test_config_file):
    config_file, config_data = test_config_file
    config = load_config(config_file)
    assert config == config_data

def test_load_config_not_found():
    config = load_config("not_found.json")
    assert config is None

def test_load_config_invalid_json(tmp_path):
    invalid_json_file = tmp_path / "invalid.json"
    with open(invalid_json_file, 'w') as f:
        f.write("invalid json")
    config = load_config(invalid_json_file)
    assert config is None

# エラーログ出力テスト
def test_log_error(tmp_path):
    error_log_path = "error.txt"
    log_error("test error", "test.py", 10)
    assert os.path.exists(error_log_path)
    with open(error_log_path, 'r', encoding='utf-8') as f:
        log_entries = f.readlines()
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        assert any(log_entry.startswith(timestamp) for log_entry in log_entries)
        assert any("test.py" in log_entry for log_entry in log_entries)
        assert any("10" in log_entry for log_entry in log_entries)
        assert any("test error" in log_entry for log_entry in log_entries)
    os.remove(error_log_path)

# 入力ファイルリスト取得テスト
def test_get_input_files(test_config_file):
    config_file, config_data = test_config_file
    input_dir = config_data["input_dir"]
    
    # テスト用のファイルを作成
    temp_dir = tempfile.mkdtemp()
    from pathlib import Path
    Path(os.path.join(temp_dir, "test1.csv")).touch()
    Path(os.path.join(temp_dir, "test2.tsv")).touch()
    Path(os.path.join(temp_dir, "test3.txt")).touch()
    
    files = get_input_files(input_dir)
    assert len(files) == 0
    
    files = get_input_files(temp_dir)
    assert len(files) == 2
    assert any(f.endswith("test1.csv") for f in files)
    assert any(f.endswith("test2.tsv") for f in files)

# ヘッダー行読み込みテスト
def test_read_header(test_csv_files):
    file_path1, file_path2, config_data = test_csv_files
    header1 = read_header(file_path1, "utf-8", ",")
    assert header1 == ["column1", "column2", "column3"]
    header2 = read_header(file_path2, "utf-8", ",")
    assert header2 == ["column1", "column2", "column3"]
    
    header_none = read_header("not_found.csv", "utf-8", ",")
    assert header_none is None

# ファイル処理テスト
def test_process_files(test_config_file, test_csv_files):
    config_file, config_data = test_config_file
    file_path1, file_path2, config_data = test_csv_files
    config = load_config(config_file)
    process_files(config)
    
    output_dir = config["output_dir"]
    output_filename = config["output_filename"]
    
    output_file1 = os.path.join(output_dir, os.path.splitext(output_filename)[0] + "_0001.csv")
    output_file2 = os.path.join(output_dir, os.path.splitext(output_filename)[0] + "_0002.csv")

    assert os.path.exists(output_file1)
    assert os.path.exists(output_file2)
    
    with open(output_file1, 'r', encoding='utf-8', newline='') as f:
        reader = csv.reader(f)
        output_data = list(reader)
        assert output_data[0] == ["column1", "column3", "new_column"]
        assert output_data[1] == ["1", "3", "1201"]
        assert output_data[2] == ["7", "9", "7122"]
    
    with open(output_file2, 'r', encoding='utf-8', newline='') as f:
        reader = csv.reader(f)
        output_data = list(reader)
        assert output_data[0] == ["column1", "column3", "new_column"]
        assert output_data[1] == ["10", "11", "10153"]
        assert output_data[2] == ["16", "17", "16184"]

def test_process_files_no_max_rows(test_config_file, test_csv_files):
    config_file, config_data = test_config_file
    file_path1, file_path2, config_data = test_csv_files
    config_data["max_rows_per_file"] = None
    config_data["filter_conditions"] = []
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".json", encoding='utf-8') as f:
        json.dump(config_data, f)
        config_file = f.name
    config = load_config(config_file)
    process_files(config)

    output_dir = config["output_dir"]
    output_filename = config["output_filename"]

    output_file = os.path.join(output_dir, output_filename)
    assert os.path.exists(output_file)

    with open(output_file, 'r', encoding='utf-8', newline='') as f:
        reader = csv.reader(f)
        output_data = list(reader)
        assert output_data[0] == ["column1", "column3", "new_column"]
        assert output_data[1] == ["1", "3", "1201"]
        assert output_data[2] == ["4", "6", "452"]
        assert output_data[3] == ["7", "9", "7123"]
        assert output_data[4] == ["10", "11", "10154"]
        assert output_data[5] == ["13", "14", "1315"]
        assert output_data[6] == ["16", "17", "16186"]

def test_process_files_add_column_error(test_config_file):
    config_file, config_data = test_config_file
    input_dir = config_data["input_dir"]
    
    file_path = os.path.join(input_dir, "add_column_error.csv")
    with open(file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["column1", "column2", "column3"])
        writer.writerow(["1", "a", "3"])
    
    config_data["add_columns"] = {"new_column": "@[column1] + $[column2]"}
    config_data["filter_conditions"] = []
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".json", encoding='utf-8') as f:
        json.dump(config_data, f)
        config_file = f.name
    config = load_config(config_file)
    process_files(config)
    
    error_log_path = "error.txt"
    assert os.path.exists(error_log_path)
    with open(error_log_path, 'r', encoding='utf-8') as f:
        log_entries = f.readlines()
        assert any("追加列[new_column]の計算に失敗しました" in entry for entry in log_entries)
    os.remove(error_log_path)

# ExpressionEvaluatorのテスト
def test_expression_evaluator():
    evaluator = ExpressionEvaluator(1, {"column1": "10", "column2": "20"})
    assert evaluator.evaluate("$[column1] + $[column2]") == "1020"
    assert evaluator.evaluate("$[column1] + $[column2] + $#") == "10201"
    assert evaluator.evaluate("@[column1] + @[column2] + @#") == 31
    
    evaluator = ExpressionEvaluator(3, {"column1": 10, "column2": 20})
    assert evaluator.evaluate("@[column1] + @[column2] + @#") == 33
    assert evaluator.evaluate("$[column1] + $[column2] + $#") == "10203"
    
    evaluator = ExpressionEvaluator(1, {"column1": "test", "column2": "20"})
    assert evaluator.evaluate("$[column1]") == "test"
    assert evaluator.evaluate("@[column1]") == 0
    assert evaluator.evaluate("$[COLUMN1]") == "test"

    evaluator = ExpressionEvaluator(1, {"column1": 10, "column2": 20})
    assert evaluator.evaluate("$[column1] + $[column3]") == "10"
    assert evaluator.evaluate("@[column1] + @[column3]") == 10

    with pytest.raises(ValueError, match="式の評価に失敗しました"):
        evaluator.evaluate("fnc1('12')")

    evaluator = ExpressionEvaluator(1, {"column1": "10", "column2": "20"})
    with pytest.raises(ValueError, match="式の評価に失敗しました"):
        evaluator.evaluate("$[column1] + @[column2]")
            
