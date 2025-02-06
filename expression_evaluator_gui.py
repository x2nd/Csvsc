import flet
from flet import IconButton, Page, Row, TextField, icons, Text, Column, AlertDialog, TextButton
from utils.expression_evaluator import ExpressionEvaluator

class VariableEntry(Row):
    def __init__(self, parent, row_num, name_value=None):
        super().__init__()
        self.parent_gui = parent
        self.row_num = row_num
        self.name_field = TextField(label="列名", width=200, multiline=True, min_lines=1)
        self.value_field = TextField(label="値", width=200, multiline=True, min_lines=1)
        if name_value:
            self.name_field.value = name_value[0]
            self.value_field.value = name_value[1]
        self.remove_button = IconButton(icon=flet.Icons.REMOVE, on_click=self.remove_variable_row)
        self.controls = [
            self.name_field,
            self.value_field,
            self.remove_button
        ]

    def remove_variable_row(self, e):
        self.parent_gui.remove_variable_row(self.row_num)

class ExpressionEvaluatorGUI:
    def __init__(self, page: Page):
        self.page = page
        self.page.title = "数式確認ツール"
        self.page.window.width = 600
        self.page.window.height = 500
        self.page.vertical_alignment = "start"
        self.page.horizontal_alignment = "center"

        self.row_entry = TextField(label="行数", value="1", width=100)
        self.expression_entry = TextField(label="数式", value="$# + $[column1] + $[column2]", width=550)
        self.result_label = TextField(label="結果", value="結果はここに表示されます", width=550, read_only=True, multiline=True, min_lines=1)
        self.variable_entries = []
        self.variables_column = Column()
        self.add_variable_row(None, ("column1", "10"))
        self.add_variable_row(None, ("column2", "20"))

        self.page.add(
            Column([
                Row([Text("行数:"), self.row_entry]),
                Row([Text("列:"),
                    IconButton(icon=flet.Icons.ADD, on_click=self.add_variable_row)
                ]),
                self.variables_column,
                Row([]),
                Row([self.expression_entry]),
                Row([]),
                Row([flet.FilledTonalButton("評価", on_click=self.evaluate_expression, width=100)]),
                 Row([]),
               Row([self.result_label])
            ])
        )

    def add_variable_row(self, e=None, name_value=None):
        row_num = len(self.variable_entries) + 1
        variable_entry = VariableEntry(self, row_num, name_value)
        self.variable_entries.append(variable_entry)
        self.variables_column.controls.append(variable_entry)
        self.page.update()

    def remove_variable_row(self, row_num):
        if row_num <= 0 or row_num > len(self.variable_entries):
            return
        
        entry_to_remove = self.variable_entries[row_num-1]
        self.variables_column.controls.remove(entry_to_remove)
        del self.variable_entries[row_num-1]
        
        # 行番号を振り直す
        for i, entry in enumerate(self.variable_entries):
            entry.row_num = i + 1
        self.page.update()

    def evaluate_expression(self, e):
        try:
            sequence_number = int(self.row_entry.value)
            variables = {}
            for entry in self.variable_entries:
                name = entry.name_field.value.strip()
                value = entry.value_field.value.strip()
                if name:
                    variables[name] = value
            expression = self.expression_entry.value

            evaluator = ExpressionEvaluator(sequence_number, variables)
            result = evaluator.evaluate(expression)
            self.result_label.value = evaluator.evaluate_expression + ' = ' + str(result)
            self.page.update()
        except ValueError as e:
            #self.show_error_dialog(str(e))
            self.result_label.value = evaluator.evaluate_expression + ' = ' + str(e)
            self.page.update()
            
        except Exception as e:
            #self.show_error_dialog(f"予期せぬエラーが発生しました: {e}")
            self.result_label.value = evaluator.evaluate_expression + ' = ' + f"予期せぬエラーが発生しました: {e}"
            self.page.update()

    def show_error_dialog(self, message):
        dlg = AlertDialog(
            modal=True,
            title=Text("エラー"),
            content=Text(message),
            actions=[TextButton("OK", on_click=lambda e: self.page.close(dlg))],
            actions_alignment=flet.MainAxisAlignment.END,
        )
        self.page.open(dlg)

def main(page: Page):
    ExpressionEvaluatorGUI(page)

if __name__ == "__main__":
    flet.app(target=main)