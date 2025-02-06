# sample function
def fnc1(col1):
    if col1.isnumeric():
        return str(int(col1) * 2)
    if col1 == '':
        return ''
    else:
        return '**' + col1 + '**'

def fnc2(no, col1):
    return '**' + str(no) + ':' + col1 + '**'
