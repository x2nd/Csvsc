import json
import os
import csv
import datetime
import re
from utils.expression_evaluator import ExpressionEvaluator

def load_config(config_path):
    """設定ファイルを読み込む"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        log_error(f"設定ファイルが見つかりません: {config_path}")
        return None
    except json.JSONDecodeError:
        log_error(f"設定ファイルのJSON形式が不正です: {config_path}")
        return None

def log_error(message, file_path=None, line_number=None):
    """エラーログをファイルに出力する"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    error_log_path = "error.txt"
    log_entry = f"{timestamp}\t{file_path or 'N/A'}\t{line_number or 'N/A'}\t{message}\n"
    try:
        #print(f"エラーログ出力先: {os.path.abspath(error_log_path)}")
        with open(error_log_path, 'a', encoding='utf-8') as f:
            f.write(log_entry)
    except Exception as e:
        print(f"エラーログの書き込みに失敗しました: {e}")

def init_debug_log():
    """デバッグログファイルを初期化する"""
    debug_log_path = "debug.log"
    try:
        with open(debug_log_path, 'w', encoding='utf-8') as f:
            f.write("デバッグログ開始\n")
    except Exception as e:
        print(f"デバッグログファイルの初期化に失敗しました: {e}")

def write_debug_log(message, file_path=None, line_number=None):
    """デバッグログをファイルに書き込む"""
    debug_log_path = "debug.log"
    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{timestamp}\t{file_path or 'N/A'}\t{line_number or 'N/A'}\t{message}\n"
        with open(debug_log_path, 'a', encoding='utf-8') as f:
            f.write(log_entry)
    except Exception as e:
        print(f"デバッグログの書き込みに失敗しました: {e}")

def get_input_files(input_dir):
    """入力ディレクトリ内のCSV/TSVファイルをリストアップする"""
    files = []
    for filename in os.listdir(input_dir):
        if filename.lower().endswith(('.csv', '.tsv')):
            files.append(os.path.join(input_dir, filename))
    return files

def read_header(file_path, encoding, delimiter):
    """CSV/TSVファイルのヘッダー行を読み込む"""
    try:
        with open(file_path, 'r', encoding=encoding, newline='') as f:
            reader = csv.reader(f, delimiter=delimiter, quotechar='"')
            for row in reader:
                return row
    except Exception as e:
        log_error(f"ヘッダー行の読み込みに失敗しました: {e}", file_path)
        return None

def process_files(config):
    """設定に基づいてファイルを処理する"""
    input_dir = config.get('input_dir')
    input_encoding = config.get('input_encoding', 'UTF-8')
    output_encoding = config.get('output_encoding', 'auto')
    output_dir = config.get('output_dir')
    output_filename = config.get('output_filename')
    max_rows_per_file = config.get('max_rows_per_file', 0)
    output_columns = config.get('output_columns', [])
    add_columns = config.get('add_columns', {})
    filter_conditions = config.get('filter_conditions', [])
    output_quotechar = config.get('output_quotechar', '"')
    output_quote = config.get('output_quotemode')
    debug = config.get('debug', False)

    if debug:
        init_debug_log()

    if output_quote:
        output_quote = output_quote.lower()
    if output_quote == 'minimal':
        output_quote = csv.QUOTE_MINIMAL
    elif output_quote == 'numeric':
        output_quote = csv.QUOTE_NONNUMERIC
    elif output_quote == 'none':
        output_quote = csv.QUOTE_NONE
    else:
        output_quote = csv.QUOTE_ALL
        
    if not input_dir or not output_dir or not output_filename:
        log_error("入力ディレクトリ、出力ディレクトリ、出力ファイル名のいずれかが設定されていません。")
        return

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    input_files = get_input_files(input_dir)
    if not input_files:
        log_error(f"入力ディレクトリにCSV/TSVファイルが見つかりません: {input_dir}")
        return

    all_headers = []
    for file_path in input_files:
        delimiter = '\t' if file_path.lower().endswith('.tsv') else ','
        header = read_header(file_path, input_encoding, delimiter)
        if header:
            for h in header:
                if h not in all_headers:
                    all_headers.append(h)

    if not all_headers:
        log_error("ヘッダー行を読み込めませんでした。")
        return

    for col_name, expression in add_columns.items():
        if col_name not in all_headers:
            all_headers.append(col_name)

    output_file_counter = 1
    output_file_path = os.path.join(output_dir, output_filename)
    output_file = None
    output_writer = None
    row_count = 0
    sequence_number = 1

    for file_path in input_files:
        delimiter = '\t' if file_path.lower().endswith('.tsv') else ','
        try:
            with open(file_path, 'r', encoding=input_encoding, newline='') as f:
                print(f"処理中のファイル: {os.path.basename(file_path)}")
                
                reader = csv.reader(f, delimiter=delimiter, quotechar='"')
                header = next(reader)
                header_len = len(header)

                for line_num, row in enumerate(reader, start=2):
                    values = row
                    if len(values) != header_len:
                        log_error(f"データ行の項目数がヘッダー行と一致しません。スキップします。", file_path, line_num)
                        continue

                    row_data = dict(zip(header, values))
                    
                    # フィルタリング
                    if filter_conditions:
                        evaluator = ExpressionEvaluator(sequence_number, row_data)
                        skip_row = False
                        for condition in filter_conditions:
                            if not evaluator.evaluate(condition):
                                skip_row = True
                                break
                        if skip_row:
                            if debug:
                                write_debug_log(f"フィルタリングにより行をスキップしました: {evaluator.evaluate_expression}", file_path, line_num)
                            continue

                    # 追加列の計算
                    evaluator = ExpressionEvaluator(sequence_number, row_data)
                    for col_name, expression in add_columns.items():
                        try:
                            row_data[col_name] = evaluator.evaluate(expression)
                            if debug:
                                write_debug_log(f"追加列[{col_name}]の計算結果: {evaluator.evaluate_expression} = {row_data[col_name]}", file_path, line_num)
                        except Exception as e:
                            log_error(f"追加列[{col_name}]の計算に失敗しました: {e}", file_path, line_num)

                    # 出力対象の列を抽出
                    sequence_number += 1
                    output_row = []
                    if output_columns:
                        for col in output_columns:
                            output_row.append(row_data.get(col, ''))
                    else:
                        output_row = []
                        for col in all_headers:
                            output_row.append(row_data.get(col, ''))

                    if not output_file:
                        if output_encoding == 'auto':
                            output_encoding = input_encoding
                        if max_rows_per_file and output_file_counter >= 1:
                            output_file_path = os.path.splitext(os.path.join(output_dir, output_filename))[0] + f"_{output_file_counter:04d}.csv"
                        output_file = open(output_file_path, 'w', encoding=output_encoding, newline='')
                        output_writer = csv.writer(output_file, quotechar=output_quotechar, quoting=output_quote)
                        
                        output_header = []
                        if output_columns:
                            output_header = output_columns
                        else:
                            output_header = all_headers
                        output_writer.writerow(output_header)

                    output_writer.writerow(output_row)
                    row_count += 1

                    if max_rows_per_file and row_count >= max_rows_per_file:
                        output_file.close()
                        output_file = None
                        output_writer = None
                        row_count = 0
                        output_file_counter += 1

        except Exception as e:
            log_error(f"ファイルの処理中にエラーが発生しました: {e}", file_path)
            continue
    
    if output_file:
        output_file.close()

def main():
    """メイン処理"""
    config_path = "csvsc.json"
    config = load_config(config_path)
    if config:
        process_files(config)

if __name__ == "__main__":
    print("CSV/TSVファイルを処理します。")
    main()