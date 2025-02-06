import csv
import random
import string

def generate_large_csv(filename, num_rows, num_columns):
    """
    指定された行数と列数で、ランダムなデータを含むCSVファイルを生成します。

    Args:
        filename (str): 生成するCSVファイルのパス。
        num_rows (int): 生成するCSVファイルの行数。
        num_columns (int): 生成するCSVファイルの列数。
    """
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)

        # ヘッダー行を書き込む
        header = [f"column{i+1}" for i in range(num_columns)]
        writer.writerow(header)

        # データ行を書き込む
        for _ in range(num_rows):
            row = [generate_random_data() for _ in range(num_columns)]
            writer.writerow(row)

def generate_random_data():
    """
    ランダムな文字列または数値を生成します。
    """
    if random.random() < 0.3:  # 30%の確率で数値を生成
        return str(random.randint(0, 1000))
    else:  # それ以外はランダムな文字列を生成
        length = random.randint(5, 20)
        return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))

if __name__ == '__main__':
    filename = "large_test.csv"
    num_rows = 1000000  # 100万行
    num_columns = 10    # 10列
    generate_large_csv(filename, num_rows, num_columns)
    print(f"{filename} を作成しました。")