# CFG Documentation

The custom DSL uses the following grammar in BNF style:

```bnf
<program> ::= <statement_list>

<statement_list> ::= <statement> <statement_list>
                   | ε

<statement> ::= <declaration>
              | <assignment>
              | <print_statement>
              | <if_statement>
              | <while_statement>
              | <block>

<block> ::= "{" <statement_list> "}"

<declaration> ::= <type_keyword> <identifier> ";"
                | <type_keyword> <identifier> "=" <expression> ";"

<type_keyword> ::= "num"
                 | "dec"
                 | "text"

<assignment> ::= <identifier> "=" <expression> ";"

<print_statement> ::= "show" "(" <expression> ")" ";"

<if_statement> ::= "when" "(" <expression> ")" <block>
                | "when" "(" <expression> ")" <block> "otherwise" <block>

<while_statement> ::= "loop" "(" <expression> ")" <block>

<expression> ::= <equality>

<equality> ::= <comparison> <equality_tail>

<equality_tail> ::= ("==" | "!=") <comparison> <equality_tail>
                 | ε

<comparison> ::= <term> <comparison_tail>

<comparison_tail> ::= ("<" | ">" | "<=" | ">=") <term> <comparison_tail>
                   | ε

<term> ::= <factor> <term_tail>

<term_tail> ::= ("+" | "-") <factor> <term_tail>
             | ε

<factor> ::= <unary> <factor_tail>

<factor_tail> ::= ("*" | "/") <unary> <factor_tail>
              | ε

<unary> ::= "-" <unary>
         | <primary>

<primary> ::= <identifier>
           | <number>
           | <string>
           | "(" <expression> ")"

<identifier> ::= letter { letter | digit | "_" }
<number> ::= integer | decimal
<string> ::= double-quoted text
```

Semantic note:
- The compiler front-end uses one global symbol table to keep the project beginner-friendly.
- `num` stores integers, `dec` stores floating-point values, and `text` stores strings.
- Relational expressions produce an internal `bool` type used by `when` and `loop`.

