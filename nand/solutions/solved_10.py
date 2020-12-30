import re

# integerConstant: a decimal number in the range 0 ... 32767
# stringConstant: '"', a sequence of Unicode characters, not including double quote or newline, '"'
# identifier: a sequence of letters, digits, and underscore ( '_' ) not starting with a digit.

def lex(string):
    # This is simple and requires no additional packages, but there are more elegant ways to get 
    # this job done.

    keywords = set([
        "class", "constructor", "function",
        "method", "field", "static", "var", "int",
        "char", "boolean", "void", "true", "false",
        "null", "this", "let", "do", "if", "else",
        "while", "return",
    ])
    symbols = set("'{}()[].,;+-*/&|<>=~")
    
    tokens = []
    
    while string != "":
        m = re.match(r"^([0-9]+)", string)
        if m is not None:
            token_str = m.group(1)
            int_val = int(token_str)
            if not (0 <= int_val <= 32767):
                raise Exception(f"Integer constant out of range: {int_val}")
            tokens.append(("integerConstant", int_val))
            string = string[len(token_str):]
            continue
            
        m = re.match(r'^"([^"\n]*)"', string)
        if m is not None:
            token_str = m.group(1)
            tokens.append(("stringConstant", token_str))
            string = string[len(token_str)+2:]
            continue
    
        m = re.match(r"^([a-zA-Z_][a-zA-Z_0-9]*)", string)
        if m is not None:
            token_str = m.group(1)
            if token_str in keywords:
                tokens.append(("keyword", token_str))
            else:
                tokens.append(("identifier", token_str))
            string = string[len(token_str):]
            continue
        
        m = re.match(r"^(//[^\n]*)", string)
        if m is not None:
            string = string[len(m.group(1)):]
            continue
        
        m = re.match(r"^(/\*.*\*/)", string, re.DOTALL)
        if m is not None:
            string = string[len(m.group(1)):]
            continue
        
        if string[0] in symbols:
            tokens.append(("symbol", string[0]))
            string = string[1:]
            continue 
            
        if string[0] in " \t\n":
            string = string[1:]
            continue
        
        raise Exception("Unexpected input: {string}")

    return tokens