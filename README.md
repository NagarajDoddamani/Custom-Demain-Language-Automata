# DSL Compiler Simulator

This project is a beginner-friendly compiler front-end and terminal-based compiler simulator built in Python.

It demonstrates:

- Lexical Analysis
- Syntax Analysis
- Semantic Analysis
- Three-Address Code Generation
- Interactive compiler visualization in the terminal

## What The Simulator Does

The application starts with a default DSL program loaded from `compiler_dsl/sample_programs/test.dsl` and shows a dashboard-style menu.

You can:

1. Run full compilation automatically
2. Watch a step-by-step demonstration with pauses
3. Edit DSL code directly in the terminal and compile it
4. View saved compiler outputs
5. Exit

## Menu Layout

```text
========================================================
              DSL COMPILER SIMULATOR
========================================================

Project      : Compiler Front-End
Language     : Custom DSL
Input File   : test.dsl
Status       : READY

========================================================
1. Run Full Compilation
2. Step-by-Step Demonstration
3. Edit DSL Program
4. Show Saved Outputs
5. Exit
```

## Project Structure

```text
compiler_dsl/
├── compiler/
│   ├── lexer.py
│   ├── parser.py
│   ├── semantic.py
│   ├── tac.py
│   └── session.py
├── core/
│   ├── compiler.py
│   ├── lexer.py
│   ├── parser.py
│   ├── semantic.py
│   └── tac.py
├── ui/
│   ├── animations.py
│   ├── colors.py
│   ├── dashboard.py
│   ├── display.py
│   ├── menu.py
│   ├── progress.py
│   └── table.py
├── outputs/
├── sample_programs/
├── lexer/
├── parser/
├── semantic/
├── intermediate/
├── lab_tasks/
├── ast_nodes.py
└── utils.py

main.py
tests/test_compiler.py
CFG.md
```

## DSL Keywords

- `num` for integer declarations
- `dec` for floating-point declarations
- `text` for string declarations
- `show` for print statements
- `when` for if conditions
- `otherwise` for else blocks
- `loop` for while loops

## Output Files

The simulator saves compilation artifacts automatically in:

```text
compiler_dsl/outputs/
├── tokens.txt
├── symbol_table.txt
├── tac.txt
└── logs.txt
```

## Sample DSL Program

```dsl
num a = 10;
num b = 20;
num c;

c = a + b * 2;

show(c);
```

## Example TAC

```text
t1 = b * 2
t2 = a + t1
c = t2
print c
```

## Example Console Output

```text
[INFO] Starting Lexical Analysis...
[SUCCESS] Tokens Generated Successfully
[INFO] Total Tokens Found: 52

[INFO] Starting Syntax Analysis...
[SUCCESS] Syntax Valid

[INFO] Performing Semantic Analysis...
[SUCCESS] No Semantic Errors Found

[INFO] Generating Three-Address Code...
[SUCCESS] TAC Generated Successfully
```

## How To Run

```bash
python main.py
```

## How To Run Tests

```bash
python -m unittest discover -s tests
```

## Notes

- The UI is fully terminal-based and works in PowerShell or a regular console.
- The project uses pure Python with small helper modules for tables, colors, progress bars, and explanations.
- `colorama` and `tabulate` are optional dependencies. If they are not installed, the app still runs using fallbacks.

