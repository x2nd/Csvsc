import re
import os
import sys
import importlib.util
import inspect

def load_custom_functions(fn_dir):
    """fnディレクトリから関数をロードする"""
    custom_functions = {}
    
    # fnディレクトリが存在しない場合は空の辞書を返す
    if not os.path.exists(fn_dir):
        return custom_functions
        
    # Pythonファイルを検索
    for filename in os.listdir(fn_dir):
        if filename.endswith('.py'):
            module_path = os.path.join(fn_dir, filename)
            module_name = os.path.splitext(filename)[0]
            
            try:
                # モジュールを動的にロード
                spec = importlib.util.spec_from_file_location(module_name, module_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # モジュール内の関数を取得
                for name, obj in inspect.getmembers(module):
                    if inspect.isfunction(obj) and not name.startswith('_'):
                        custom_functions[name] = obj
                        
            except Exception as e:
                print(f"関数のロード中にエラーが発生しました {module_path}: {e}")
                
    return custom_functions

class ExpressionEvaluator:
    def __init__(self, sequence_number, variables=None, fn_dir=None):
        self.variables = variables or {}
        self.sequence_number = str(sequence_number)
        # 変数名を小文字に変換
        self.variables = {k.lower(): v for k, v in self.variables.items()}
        # 実行ファイルのパスを基準にfnフォルダを探す
        base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
        self.fn_dir = fn_dir or os.path.join(base_path, 'fn')
        # fnフォルダから関数をロード
        self.custom_functions = load_custom_functions(self.fn_dir)
    def evaluate(self, expression):
        """数式を評価する"""        
        # カスタム関数とデータを組み合わせた評価環境を作成
        eval_env = {
            **self.variables,
            **self.custom_functions
        }
        
        # 安全な評価のために制限された環境で実行
        self.evaluate_expression = self._replace_column_names(expression)
        try:
            return eval(self.evaluate_expression.replace('\r','\\r').replace('\n','\\n'), {"__builtins__": {}}, eval_env)
        except Exception as e:
            raise ValueError(f"式の評価に失敗しました: {expression}, エラー: {str(e)}")

    def _replace_column_names(self, expression):
        """数式内の列名を実際の値に置換する"""
        def replace_str(match):
            column_name = match.group(1).lower()
            if column_name in self.variables:
                return f"'{self.variables[column_name].replace('\'','\\\'')}'"
            else:
                return f"''"
                
        def replace_int(match):
            column_name = match.group(1).lower()
            if column_name in self.variables:
                try:
                    return str(int(self.variables[column_name]))
                except ValueError:
                    return "0"
            else:
                return "0"
        exp_ret = expression.replace('@#', self.sequence_number)
        exp_ret = exp_ret.replace('$#', f"'{self.sequence_number}'")
        exp_ret = re.sub(r'@\[(\w+)\]', replace_int, exp_ret)
        return re.sub(r'\$\[(\w+)\]', replace_str, exp_ret)


