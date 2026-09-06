# -*- coding: utf-8 -*-
"""
This programme is for test all functionalities of smart.
"""
import os
import traceback
import sys
import logging
from pathlib import Path

from compiller_tool.import_tool import PATH_LIB
from compiller_tool.string_tool import SMART_KEYWORD

def config_log() -> None:
    """Set the logging.basicConfig"""
    if "--compile-debug" in sys.argv:
        sys.argv.remove("--compile-debug")

        logging.basicConfig(
            format="SmartCompiller %(levelname)s: %(message)s",
            level=logging.INFO,
            stream=sys.stdout,  # for redirecting the output
            force=True
        )
    else:
        logging.basicConfig(
            format="SmartCompiller %(levelname)s: %(message)s",
            level=logging.WARNING,
            stream=sys.stdout,
            force=True
        )

config_log()

import smart_emulator
from smart_compiller import compile_smart
from compiller_tool import compiller_data_run
from compiller_tool.color_tool import Colors
from compiller_tool.smart_exception import SmartError


ERASE_PROGRESSBAR = "\033[2K\033[1G"

SYMBOL_OK = False

TEST_OK = "✔️   " if SYMBOL_OK else f"{Colors.GREEN}OK{Colors.RESET}  "
TEST_ERROR = "❌   " if SYMBOL_OK else f"{Colors.RED}ERR{Colors.RESET}  "

class TestError(Exception):
    """Main Exception for test."""
    pass

class StopTest(TestError):
    """This exception is for stop the test."""
    pass

class OutputError(TestError):
    """If the output of programme are not good."""
    pass

class Test:
    """This class is for testing all functionalities of smart."""
    def __init__(self, name:str, code:str, output:str="", compile_output:str="", compile_only:bool=False, sucess:bool=True, stdin_test:str="", max_op:int=10000):
        """
        Set information about test.
        """
        self.name = name
        self.code = code
        self.compile_only = compile_only
        self.output = output + "\n\nEnd of run"
        self.compile_output = compile_output
        self.sucess = sucess
        self.stdin_test = stdin_test
        self.max_op = max_op
    def show_test(self, start_compilation:bool=True) -> None:
        """Print the detail of test"""
        print(
            f"{Colors.BG_BLUE}\t\tTest: {self.name}{Colors.RESET}",
            f"{Colors.GREEN}INFO:{Colors.RESET}",
            f"Compile only: {self.compile_only}",
            f"Normal sucess: {self.sucess}",
            f"{Colors.YELLOW}Starting compilation...{Colors.RESET}" if start_compilation else "",

            sep="\n"
        )


    def run(self) -> None:
        """This function is for running the test."""
        global all_ok, error_counter

        compiller_data_run.reset_data()

        with open("test/test.sma", "w") as f:
            f.write(self.code)

        self.show_test()

        error = False
        error_output = ""
        compilation_error = False

        try:
            self.code_compile = compile_smart("test/test.sma", make_file=False, thread_mode = [False, "", False, False], first_call=True)

            if "  " in self.code_compile:
                raise OutputError(f"{Colors.RED}Double space on output. Risk of error with address counting...{Colors.RESET}")

            if self.code_compile != self.compile_output:
                if self.compile_only:
                    raise OutputError(f"The output of compilation is not good:\n{self.code_compile}")

        except SmartError as se:
            error = True
            compilation_error = True
            error_output = str(se)

        except Exception as e:
            error = True
            error_output = "Smart Emulator error: " + str(e)

        else:
            if not self.compile_only:
                try:
                    output = smart_emulator.start_test(self.code_compile, self.max_op, stdin=self.stdin_test)

                    if output != self.output:
                        raise OutputError(f"The output of programme is not good:\n{output}")

                except smart_emulator.EmulatorStdinError as e:
                    print(f"{Colors.RED}The programm try to read on entry but the entry is end.{Colors.RESET}\n{Colors.MAGENTA}It caused by too call to input function...{Colors.RESET}")

                    error = True
                    error_output = str(e)

                except smart_emulator.EmulatorMaxOPError as e:
                    print(f"{Colors.RED}The programm exeded the max operation limit ({self.max_op}).{Colors.RESET}\n{Colors.MAGENTA}It can be caused by an infinite loop...{Colors.RESET}")

                    error = True
                    error_output = str(e)

                except TimeoutError as e:
                    print(str(e))

                except OutputError as oe:
                    error = True
                    error_output = str(oe)

                except Exception as e:
                    error = True
                    error_output = str(e)

        if (error and self.sucess) or (not(error) and not(self.sucess)):
            all_ok = False
            error_counter += 1

            print(
                f"{ERASE_PROGRESSBAR}{TEST_ERROR}{Colors.BG_RED}ERROR: Test failed{Colors.RESET}",
                f"{Colors.RED}{'Compilation error' if compilation_error else 'Runtime error'}",
                f"Error output: {error_output}{Colors.RESET}",

                sep="\n"
            )

            reply = input("Continue test ? (y/n): ")

            if reply.lower() == "n":
                raise StopTest("Test stopped by user")

            print(end="\n"*10)

        else:

            print(f"{ERASE_PROGRESSBAR}{TEST_OK}{Colors.BG_GREEN}Test OK{Colors.RESET}", end="\n"*10)

class ModuleTest(Test):
    """This class is for testing a Smart code with some modules (in different files)."""
    def __init__(self, name:str, code_modules:list[tuple[str, str]], output:str="", compile_output:str="", compile_only:bool=False, sucess:bool=True, stdin_test:int=10000):
        super().__init__(name, code_modules[0][1], output, compile_output, compile_only, sucess, stdin_test)

        self.code_modules = code_modules[1:]    # get all modules except main module

    '''def show_module_test(self) -> None:
        """Print the detail of module test"""
        print(f"{Colors.BG_BLUE}Test with some modules:{Colors.RESET}")
        self.show_test()'''

    def run_modules(self) -> None:
        """This function make all module and run test.
        Next delete the modules."""

        for module in self.code_modules:
            with open(f"test/{module[0]}", "w") as f:
                f.write(module[1])

        self.run()

        for module in self.code_modules:
            os.remove(f"test/{module[0]}")

LIB_PATH = {
    "screen_tool": ("smart_lib/screen_tool/screen_tool.sma",),
    "string": ("smart_lib/string/convert.sma",),
    "input": ("smart_lib/input/readkeys.sma",)
}

def control_lib() -> bool:
    """Return True if all library are good."""
    if not Path(PATH_LIB["global"]).is_dir():
        print(f"{Colors.YELLOW}Warning: missing global lib directory ({PATH_LIB['global']}). The library test will be skip.{Colors.RESET}.")
        return False
    elif not Path(PATH_LIB["smart"]).is_dir():
        print(f"{Colors.YELLOW}Warning: missing Smart lib directory ({PATH_LIB['smart']}). The library test will be skip.{Colors.RESET}.")
        return False

    for lib, path in LIB_PATH.items():
        for p in path:
            lib_path = os.path.join(PATH_LIB["base"], p)

            if sys.platform == "win32":
                lib_path = lib_path.replace("/", "\\")

            if not Path(lib_path).is_file():
                print(f"{Colors.YELLOW}Warning: missing library file ({lib_path}), of {lib} library. The library test will be skip.{Colors.RESET}.")
                return False

    return True


try:

    smart_emulator.GUI_MODE = False
    smart_emulator.on_test = True

    os.makedirs("test", exist_ok=True)

    all_ok = True
    error_counter = 0

    if control_lib():

        TEST_LIB = (
            Test(
                "Test library import",  # test for import all library. When a new library is added, add a test for it.
                code="""
                    // --- screen tool ---
                    import "screen_tool/screen_tool.sma";

                    // --- string library ---
                    import "string/convert.sma";

                    // --- input library ---
                    import "input/readkeys.sma";

                    print: "OK";
                """,
                output="OK"
            ),
            # --- screen tool ---
            Test(
                "Test screen tool",
                code="""
                    import "screen_tool/screen_tool.sma";
                    screen_clean:;
                    print: "OK";
                """,
                output='\n' * 24 + "OK"
            ),
            # --- string library ---
            Test(
                "Test convert",
                code="""
                    import "string/convert.sma";
                    .a = int_to_char: 1;
                    print: .a;

                    .b = char_to_int: '1';
                    if .b == 1{;
                        print: "OK";
                    }
                """,
                output="1OK"
            ),
            # --- input library ---
            Test(
                "Test readkeys",
                code=r"""
                    import "input/readkeys.sma";

                    ~my_string = "";

                    // read 21 character (len of string):
                    readkeys: ~my_string, False;  // on ~my_string will be the input from keyword.

                    print: ~my_string;

                    ~my_string = ""; // reset the string

                    // read while the caracter is not '\r' or 21 was read:
                    readkeys: ~my_string, '\r';
                    print: ~my_string;
                """,
                stdin_test="FIRST LINE INPUT     LINE2\r",
                output="FIRST LINE INPUT     LINE2\n" # the \r on emulator is replace by \n
            )
        )
    else:
        input("Press enter to continue...")
        TEST_LIB = ()

    ERROR_VARIABLE_KEYWORD = tuple(  # the test for a variable with a reserved name
        Test(
            f"Error set variable named {keyword}",
            code=f".{keyword} = 1;",
            sucess=False
        ) for keyword in SMART_KEYWORD
    )

    INCREMENT_DECREMENT = (
        Test(
            "Simple increment",
            code="""
                .a = 0;
                .a++;
                print: .a + '0';
            """,
            output="1"
        ),
        Test(
            "Simple decrement",
            code="""
                .a = 10;
                .a--;
                print: .a + '0';
            """,
            output="9"
        ),
        Test(
            "Advenced decrement increment",
            code="""
                .i = 11;
                .i--;
                .i--;
                .i--;
                .i++;
                print: .i + '0';
            """,
            output="9"
        ),
        Test(
            "Increment / decrement in advenced variable",
            code="""
                ~str = "AB";
                ~str[0]++;
                print: ~str[0];
                ~str[0]--;
                print: ~str[0];

                ~str[1]--;
                print: ~str[1];
                ~str[1]++;
                print: ~str[1];
            """,
            output="BAAB"
        ),
        # --- error ---
        Test(
            "Sintaxe error on increment",
            code="""
                .++;
            """,
            sucess=False
        ),
        Test(
            "Increment/decrement advenced value",
            code="""
                ~str = "AAAA";
                ~str--;
                ~str++;
            """,
            sucess=False
        ),
        Test(
            "Increment/decrement advenced value on runtime index", # this test is actually sucess=False because not implemented. Succetible to change if the functionalyty is implemented.
            code="""
                .index = 1;
                ~str = "AAA";
                ~str[.index]++;
                ~str[.index]--;
                print: ~str;
            """,
            sucess=False
        )
    )

    TEST_COMPARATOR = (
        Test(
            "== test",
            code="""
                .a = 1;
                .b = 1;
                .c = 2;

                .comparator = .a == .b;
                print: .comparator + '0';

                .comparator = .a == .c;
                print: .comparator + '0';
            """,
            output="10"
        ),
        Test(
            ">= test",
            code="""
                .a = 1;
                .b = 2;
                .c = 3;

                .comparator = .a >= .b;
                print: .comparator + '0';

                .comparator = .b >= .a;
                print: .comparator + '0';

                .comparator = .c >= .b;
                print: .comparator + '0';

                .comparator = .c >= 3;
                print: .comparator + '0';
            """,
            output="0111"
        ),
        Test(
            "< test",
            code="""
                .a = 1;
                .b = 2;
                .c = 3;

                .comparator = .a < .b;
                print: .comparator + '0';

                .comparator = .b < .a;
                print: .comparator + '0';

                .comparator = .c < .b;
                print: .comparator + '0';

                .comparator = .c < 3;
                print: .comparator + '0';
            """,
            output="1000"
        ),
        Test(
            "!= test",
            code="""
                .a = 1;
                .b = 0;
                .c = 2;

                .comparator = .a != .b;
                print: .comparator + '0';

                .comparator = .a != .c;
                print: .comparator + '0';

                .comparator = .a != 1;
                print: .comparator + '0';
            """,
            output="110"
        ),
        # --- error ---
        Test(
            "Missing value on comparator - 1",
            code="""
                .a = 1 ==;
                .b = 1 >=;
                .c = 1 <;
                .d = 1 !=;
            """,
            sucess=False
        ),
        Test(
            "Missing value on comparator - 2",
            code="""
                .a = == 1;
                .b = >= 1;
                .c = < 1;
                .d = != 1;
            """,
            sucess=False
        )
    )

    SYNTAXE_ERROR_TEST = (  # this test have the same class Test but for test syntax error.
        Test(
            "Forget ';'",
            code='print: "TEST"\nprint: "ERROR"',
            compile_only=True,
            sucess=False
        ),
        Test(
            "Unclosed str",
            code="print: \"TEST",
            compile_only=True,
            sucess=False
        ),
        Test(
            "Bad char in str",
            code='print: "a"',
            compile_only=True,
            sucess=False
        ),
        Test(
            "Bad char in char",
            code="print: 'a'",
            compile_only=True,
            sucess=False
        ),
        Test(
            "Syntax error after str",
            code='print: "HELLO" error',
            compile_only=True,
            sucess=False
        ),
        Test(
            "Syntax error after char",
            code="print: 'A' error",
            compile_only=True,
            sucess=False
        ),
        Test(
            "Unclosed block",
            code="""
                if True{;
                    print: "ERROR";
            """,
            compile_only=True,
            sucess=False
        )
    )

    BOOLEAN_TEST = (
        Test(
            "Simple boolean",
            code="""
                .a = True;
                .b = False;

                print: .a + '0';
                print: .b + '0';

                print: True + '0';
                print: False + '0';
            """,
            output="1010"
        ),
        Test(
            "Boolean comparison",
            code="""
                .a = True;
                .b = False;

                .comparaison1 = .a == .b;
                print: .comparaison1 + '0';

                .comparaison2 = .a == True;
                print: .comparaison2 + '0';

                .comparaison3 = .b == False;
                print: .comparaison3 + '0';

                .comparaison4 = True == 1;
                print: .comparaison4 + '0';

                .comparaison5 = False == 0;
                print: .comparaison5 + '0';

                .comparaison6 = True == False;
                print: .comparaison6 + '0';
            """,
            output="011110"
        ),
        Test(
            "Boolean if",
            code="""
                .a = True;
                if .a{;
                    print: "IF TEST";
                }
                else{;
                    print: "ERROR";
                }
            """,
            output="IF TEST"
        )
    )

    TEST_INT_HEX = (
        Test(
            "Simple int and hex",
            code="""
                .a = 65;
                .b = 0x41;

                print: .a;
                print: .b;
            """,
            output="AA"
        ),
        # ---- test error ----
        Test(
            "Value too big (int)",
            code=".a = 300;",
            sucess=False
        ),
        Test(
            "Value too big (hex)",
            code=".a = 0x300;",
            sucess=False
        ),
        Test(
            "Bad hex value",
            code=".a = 0xG;",
            sucess=False
        )
    )

    TEST_CHAR = (
        Test(
            "Simple char",
            code="print: 'A';",
            output="A"
        ),
        Test(
            "Char in variables",
            code="""
                .a = 'A';
                print: .a;

                .b = 'B';
                print: .b;
            """,
            output="AB"
        ),
        # ----- error
        Test(
            "Char not autorize",
            code=".a = 'a'",
            sucess=False
        ),
        Test(
            "Bad len char",
            code=".a = 'AA'",
            sucess=False
        )
    )

    ADVENCED_VALUE_TEST = (
        Test(
            "Simple str",
            code="""
                ~a = "STRING";
                print: ~a;

                print: "STRING2";
            """,
            output="STRINGSTRING2"
        ),
        Test(
            "Simple list",
            code="""
                ~a = ['A', 'B', 'C'];
                print: ~a;

                print: ['1', '2', '3'];
            """,
            output="ABC123"
        ),
        Test(
            "F-string test",
            code="""
                ~str1 = F"AA{65}AA{'@'}";
                print: ~str1;

                .a = 'A';
                .b = '1';
                .c = 64;

                ~str2 = F"NEW FSTR{.a}{.b}{.c}";
                print: ~str2;
                """,
            output="AAAAA@NEW FSTRA1@"
        ),
        Test(
            "List with var",
            code="""
                .a = 'A';
                .b = 'B';
                .c = 'C';

                ~list1 = [.a, .b, .c];
                print: ~list1;

                ~list2 = [.a, '1', .b, '2', .c, '3'];
                print: ~list2;
            """,
            output="ABCA1B2C3"
        ),
        Test(
            "Index on str",
            code="""
                ~str1 = "STRING";
                print: ~str1[0];
                print: ~str1[3];

                print: ~str1[-16];

                .a = 1;
                print: ~str1[.a];
            """,
            output="SIGT"
        ),
        Test(
            "Index on list",
            code="""
                ~list1 = ['A', 'B', 'C'];
                print: ~list1[0];
                print: ~list1[2];

                .a = 1;
                print: ~list1[.a];

                print: ~list1[-19];
            """,
            output="ACBC"
        ),
        Test(
            "Str an list comparison",
            code="""
                ~str1 = "STRING";
                ~list1 = ['S', 'T', 'R', 'I', 'N', 'G'];
                print: ~str1 == ~list1;"""
        ),
        # ---- error ----
        Test(
            "Str not in advanced var",
            code='.a = "STRING";',
            sucess=False
        ),
        Test(
            "Simple value in advanced var",
            code="~a = 1;",
            sucess=False
        )
    )

    ESCAPE_CHARACTER = (
        Test(
            "Escape character on char",
            code=r"""
                .a = '\r';  // on the emulator it will replace by `\n`
                print: .a;

                .b = '\'';
                print: .b;

                .c = '\"';
                print: .c;

                .d = '\\';
                print: .d;

                .e = '"';   // not a escape char but for test
                print: .e;
            """,
            output="\n'\"\\\""
        ),
        Test(
            "Escape character on str",
            code=r"""
                ~a = "AA\rAA";  // on the emulator it will replace by `\n`
                print: ~a;

                ~b = "BB\'BB";
                print: ~b;

                ~c = "CC\"CC";
                print: ~c;

                ~d = "DD\\DD";
                print: ~d;

                ~e = "EE'EE";   // not a escape char but for test
                print: ~e;
            """,
            output="AA\nAABB'BBCC\"CCDD\\DDEE'EE"
        ),
        Test(
            "Some escape characters in str",
            code=r"""
                ~a = "\r\'\"\\";
                print: ~a;
            """,
            output="\n'\"\\"    # careful: the \r on emulator is replace by \n
        ),
        Test(
            "Escape character escaped at the end of str",
            code=r"""
                ~a = "AA\\";
                print: ~a;
            """,
            output="AA\\"
        )
    )

    REGISTER_TESTS = (
        Test(
            "Accumulator A test",
            code="""
                A = 65;
                print: A;

                A = '0';
                print: A;
            """,
            output="A0"
        ),
        Test(
            "Register X and Y test",    # this test can't have output because X and Y are not printable
            code="""
                X = 1;
                Y = 2;
            """,
            output=""
        ),
        # ---- error ----
        Test(
            "Print X test",
            code="print: X;",
            sucess=False
        ),
        Test(
            "Print Y test",
            code="print: Y;",
            sucess=False
        ),
        Test(
            "Set advanced var on A",
            code='A = "STR";',
            sucess=False
        ),
        Test(
            "Set advanced var on X",
            code='X = "STR";',
            sucess=False
        ),
        Test(
            "Set advanced var on Y",
            code='Y = "STR";',
            sucess=False
        )
    )

    GOTO_TEST = (
        Test(
            "Goto test 1",
            code="""
                goto: label1;
                print: "ERROR";
                #label1;
                print: "GOTO TEST 1";
            """,
            output="GOTO TEST 1"
        ),
        Test(
            "Advanced Goto test",
            code="""
                goto: label;

                // this code are susceptible to move address
                if True{;
                    print: "ERROR";
                }
                else {;
                    A = 65;
                }

                while False{;
                    print: 'E';
                }

                #label;
                print: "GOTO TEST 2";
            """,
            output="GOTO TEST 2"
        ),
        # ---- error ----
        Test(
            "Goto label not found",
            code="""
                goto: label_not_found;
                print: "ERROR";
            """,
            sucess=False
        )
    )

    TESTS = (
        Test(
            "Test print",
            code='print: "PRINT TEST";',
            compile_output="0400: A9 50 20 EF FF A9 52 20 EF FF A9 49 20 EF FF A9 4E 20 EF FF A9 54 20 EF FF A9 20 20 EF FF A9 54 20 EF FF A9 45 20 EF FF A9 53 20 EF FF A9 54 20 EF FF 00 ",
            output="PRINT TEST"
        ),
        Test(
            "Variable test",
            code="""
                .a = 'A';
                .b = 'B';
                print: .a;
                print: .b;

                .a = .b;
                print: .a;
                .b = 64;
                print: .b;
            """,
            compile_output="0400: A9 41 8D 00 03 A9 42 8D 01 03 AD 00 03 20 EF FF AD 01 03 20 EF FF AD 01 03 8D 00 03 AD 00 03 20 EF FF A9 40 8D 01 03 AD 01 03 20 EF FF 00 ",
            output="ABB@"
        ),
        Test(
            "Input test",
            code=".i = input:;print: .i;",
            stdin_test="A",
            output="A"
        ),
        Test(
            "If test",
            code="""
                if True{;
                    print: "IF TEST";
                }
                else{;
                    print: "ERROR";
                }

                .a = True == False;
                if .a{;
                    print: "ERROR";
                } elif .a == False{;
                    print: "ELIF TEST";
                }

                .b = 10;
                if .b == 9{;
                    print: "ERROR";
                } elif .b == 11{;
                    print: "ERROR";
                }
                else{;
                    print: "ELSE TEST";
                }
            """,
            output="IF TESTELIF TESTELSE TEST"
        ),
    Test(
        "while test",
        code="""
            while True{;
                print: "TEST WHILE";
                break;
            }
            .a = True;
            while .a{;
                print: "TEST WHILE 2";
                .a = False;
            }
        """,
        output="TEST WHILETEST WHILE 2"
    ),
    Test(
        "string test",
        code="""
            ~a = "STRING";
            print: ~a;

            if ~a == "STRING"{;
                print: "OK";
            }

            ~b = "STRING2";
            if ~a == ~b{;
                print: "ERROR";
            }
            else{;
                print: "OK2";
            }

            ~c = "ABC";

            print: ~c[0];

            .d = 1;
            print: ~c[.d];

            ~c[0] = '@';

            print: ~c;
        """,
        output="STRINGOKOK2AB@BC"
    ),
    Test(
        "quit test",
        code="""
            print: "OK";
            quit:;
            print: 'E';
        """,
        output="OK"
        )
    )

    IF_TEST = (
        Test(
            "Simple if test",
            code="""
                .a = True;
                if .a{;
                    print: "OK";
                }

                if True{;
                    print: "OK2";
                }

                .b = False;
                if .b{;
                    print: "ERROR";
                }

                if False{;
                    print: "ERROR2";
                }
            """,
            output="OKOK2"
        ),
        Test(
            "Condition test",
            code="""
                .a = True;
                if .a == True{;
                    print: "OK";
                }

                if .a == False{;
                    print: "ERROR";
                }

                .b = 'A';

                if .b == 'A'{;
                    print: "OK2";
                }
                if .b == 'B'{;
                    print: "ERROR2";
                }
            """,
            output="OKOK2"
        ),
        Test(
            "Else test",
            code="""
                .a = False;
                if .a{;
                    print: "ERROR";
                }
                else{;
                    print: "OK";
                }

                .b = True;
                if .b{;
                    print: "OK2";
                }
                else{;
                    print: "ERROR2";
                }
            """,
            output="OKOK2",
        ),
        Test(
            "Elif test",
            code="""
                .a = False;
                .b = True;

                if .a{;
                    print: "ERROR";
                }
                elif .b{;
                    print: "OK";
                }
                else{;
                    print: "ERROR2";
                }

                if False{;
                    print: "ERROR3";
                }
                elif False{;
                    print: "ERROR4";
                }
                elif True{;
                    print: "OK2";
                }
                else{;
                    print: "ERROR5";
                }
            """,
            output="OKOK2"
        ),
        Test(
            "Advanced structure condition",
            code="""
                .a = True;
                .b = False;

                if True{;
                    print: "OK";

                    if .a{;
                        print: "OK2";

                        if .b{;
                            print: "ERROR";
                        }
                        else{;
                            print: "OK3";

                            if False{;
                                print: "ERROR2";
                            }
                            elif False{;
                                print: "ERROR3";
                            }
                            else{;
                                print: "OK4";
                            }
                        }
                    }
                    else{;
                        print: "ERROR";
                    }
                }
            """,
            output="OKOK2OK3OK4"
        ),
        # ---- error ----
        Test(
            "Else without if",
            code="""
                else{;
                    print: "ERROR";
                }
            """,
            sucess=False
        ),
        Test(
            "Elif without if",
            code="""
                elif True{;
                    print: "ERROR";
                }
            """,
            sucess=False
        )
    )

    FOR_TEST = (
        Test(
            "Simple for test",
            code="""
                for .i in |0|10|1| {;
                    print: '0' + .i;
                }
                print: "OK";
            """,
            output="0123456789OK"
        ),
        Test(
            "For without counter",
            code="""
                for _ in |0|5|1| {;
                    print: 'A';
                }
                print: "OK";
            """,
            output="AAAAAOK"
        ),
        Test(
            "For with break",
            code="""
                for .i in |0|10|1| {;
                    print: '0' + .i;
                    if .i == 5{;
                        break;
                    }
                }
                print: "OK";
            """,
            output="012345OK"
        ),
        Test(
            "For with continue",
            code="""
                for .i in |0|10|1| {;
                    print: '0' + .i;
                    continue;
                    print: "ERROR";
                }
                print: "OK";
            """,
            output="0123456789OK"
        ),
        Test(
            "For with start > end",
            code="""
                for .i in |10|5|1| {;   // the counter go to 255 and restart to 0, and go to 5
                    print: .i;
                }
                print: "OK";
            """,
            output="\n\n !\"#$%'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_ABCDEFGHIJKLMNOPQRSTUVWXYZOK"
        ),
        # ---- advenced value ----
        Test(
            "Advanced value in for - 1",
            code="""
                ~string = "ABCDEFG";

                for .char in ~string {;
                    print: .char;
                }

                print: "OK";
            """,
            output="ABCDEFGOK"
        ),
        Test(
            "Advanced value in for - 2",
            code="""
                ~a = "AABCDABA";

                .counter = 0;

                for .char in ~a {;
                    if .char == 'A' {;
                            .counter = .counter + 1;
                        }
                    }

                print: "NUMBER OF A FIND IS ";
                print: '0' + .counter;
            """,
            output="NUMBER OF A FIND IS 4"
        ),
        Test(
            "Edit variable for iteration in for",
            code="""
                for .i in |0|10|1| {;
                    .i = 'A';
                    print: .i;
                }
                print: "OK";
            """,
            output="AAAAAAAAAAOK"
        ),
        Test(
            "Edit variable for iteration in for with advanced value",
            code="""
                ~string = "ABCDEFG";
                for .char in ~string {;
                    .char = 'A';
                    print: .char;
                }
            """,
            output="A" * 21 # because the string have a length of 21
        ),
        # ---- error ----
        Test(
            "For syntax error",
            code="""
                for in |0|10|1| {;
                    print: "ERROR";
                }
            """,
            sucess=False
        ),
        Test(
            "For with bad start end step",
            code="""
                for .i in |0|10|0 {;
                    print: "ERROR";
                }
            """,
            sucess=False
        ),
        Test(
            "For without block",
            code="""
                for .i in |0|10|1|;
                    print: "ERROR";
            """,
            sucess=False
        ),
        Test(
            "Immediate advanced value in for",
            code="""
                for .char in "STRING" {;
                    print: "ERROR";
                }
            """,
            sucess=False
        )
    )

    WHILE_TEST = (      # warning in this test, because while can be infinite...
        #Test(
        #    "While True",
        #    code="""
        #        while True{;
        #            print: 'A';
        #        }
        #    """,
        #),
        Test(
            "Simple while test",
            code="""
                .i = 0;
                .loop = True;
                while .loop {;
                    .i = .i + 1;
                    if .i == 5{;
                        .loop = False;
                    }
                    print: '0' + .i;
                }
            """,
            output="12345",
        ),
        Test(
            "Break in while",
            code="""
                while True{;
                    print: "TEST";
                    break;
                }
            """,
            output="TEST",
        ),
        Test(
            "Continue in while",
            code="""
                .a = True;

                while .a{;
                    .a = False;
                    print: "TEST1";
                    continue;
                    print: "ERROR";
                }
            """,
            output="TEST1",
        )
    )

    MATH_TEST = (
        # addition test ---
        Test(
            "Simple addition test",
            code="print: 65+1;",
            output="B"
        ),
        Test(
            "char addition test",
            code="print: 'A'+1;print: '!' + '#';",
            output="BD"
        ),
        # substraction test ---
        Test(
            "Simple substraction test",
            code="print: 65-1;",
            output="@"
        ),
        Test(
            "char substraction test",
            code="print: 'A'-1;",
            output="@"
        ),
        # multiplication test ---
        Test(
            "Simple multiplication test",
            code="print: 13*5;", # 13 * 5 = 65 'A'
            output="A"
        ),
        Test(
            "char multiplication test",
            code="print: '!'*2;", # 33 * 2 = 66 'B'
            output="B"
        ),
        # division test ---
        Test(
            "Simple division test",
            code="print: 130/2;", # 130 / 2 = 65 'A'
            output="A"
        ),
        Test(
            "char division test",
            code="print: 'Z'/2;", # 90 / 2 = 45 '-'
            output="-"
        ),
        # advenced test ---
        Test(
            "Different operation test", # warning: smart do operation in order, not priority
            code="""
                print: 65+3-2/2;
                print: 80+3-2/4*3;
            """,
            output="!<"
        ),
        Test(
            "Math operation with variable",
            code="""
                .a = 1;
                .b = 2;
                .c = 3;
                .d = 10;
                .e = 'A';

                print: .a + 'A';
                print: .b + 'A';
                print: 'A' - .c;
                print: .e + .a;
                print: .c * .d + .d;
                .x = .d / .b;
                print: .x + .e;
            """,
            output="BC>B(F"
        )
    )

    RUNTIME_ERROR_TEST = (
        Test(
            "Error keyword test",
            code="""
                print: "OK";
                error 'A';
                print: "KO";
            """,
            output="OKEA"
        ),
        Test(
            "Error keyword with variable",
            code="""
                .code_e = 'B';
                error .code_e;
                print: "KO";
            """,
            output="EB"
        ),
        Test(
            "Division by zero test",
            code="""
                .a = 1;
                .b = 0;
                .c = .a / .b;
                print: "KO";
            """,
            output="E/"
        ),
        Test(
            "Index error test",
            code="""
                .index = 30;
                ~str = "TEST";
                print: ~str[.index];
            """,
            output="EI"
        )
    )

    MODULES_TEST = (
        ModuleTest(
            "Simple module test",
            code_modules=[
                (
                    "test.sma",
                    'import "test/module1.sma";'
                ),
                (
                    "module1.sma",
                    'print: "MODULE TEST";'
                )
            ],
            output="MODULE TEST"
        ),
        ModuleTest(
            "Get function and var from module",
            code_modules=[
                (
                    "test.sma",
                    """
                    import "test/module2.sma";

                    function:;
                    print: .var1;
                    print: ~var2;

                    print: "OK";
                    """
                ),
                (
                    "module2.sma",
                    """
                    void function{;
                        print: "FUNCTION TEST";
                    }

                    .var1 = 'A';
                    ~var2 = "STRING";
                    """
                )
            ],
            output="FUNCTION TESTASTRINGOK"
        ),
        ModuleTest(
            "Recursive import",
            code_modules=[
                (
                    "test.sma",
                    """
                    import "test/module1.sma";

                    print: .var1;
                    print: .var2;
                    func:;
                    """
                ),
                (
                    "module1.sma",
                    """
                    import "test/module2.sma";

                    .var1 = 'A';
                    """
                ),
                (
                    "module2.sma",
                    """
                    .var2 = 'B';

                    void func{;
                        print: "MODULE2";
                    }
                    """
                ),
            ],
            output="ABMODULE2"
        ),
        # test error with modules:
        ModuleTest(
            "Module not found test",
            code_modules=[
                (
                    "test.sma",
                    'import "test/module_not_found.sma";'
                )
            ],
            sucess=False
        ),
        ModuleTest(
            "Module with error",
            code_modules=[
                (
                    "test.sma",
                    'import "test/module_error.sma";'
                ),
                (
                    "module_error.sma",
                    'print: "ERROR' # intentional syntax error
                )
            ],
            sucess=False
        ),
        ModuleTest(
            "Function with variable on module",
            code_modules=[
                (
                    "test.sma",
                    """
                        import "test/module_func.sma";

                        ~str = "STRING";
                        f:;
                        print: ~str;

                    """
                ),
                (
                    "module_func.sma",
                    """
                        void f{;
                            print: "FUNCTION MODULE";
                            .a = 'A';
                            print: .a;
                        }
                    """
                )
            ],
            output="FUNCTION MODULEASTRING"
        ),
        ModuleTest(
            "Function with variable on module - 2", # on this test, press only A
            code_modules=[
                (
                    "test.sma",
                   """
                       import "test/readkeys.sma";
                       ~str = "STRING";

                       readkeys: ~str, False;

                       print: ~str;

                   """
               ),
               (
                   "readkeys.sma",
                   """
                       void readkeys: *~line, .end {;
                       .counter = 0;
                       while .counter != 21 {;
                           ~line[.counter] = input:;

                           if ~line[.counter] == .end {;
                               break;
                           }

                           .counter++;
                       }
                   }
                   """
               )
           ],
           output="A" * 21,
           stdin_test="A" * 21
        )

        #ModuleTest(    # uncomment for set the test. But this test have a long output
        #    "Self import test",
        #    code_modules=[
        #        (
        #            "test.sma",
        #            'import "test/test.sma";'
        #        )
        #    ],
        #    sucess=False
        #)
    )

    FUNCTION_TEST = (
        Test(
            "Simple function test",
            code="""
                void f{;
                    print: "OK";
                }

                f:;
            """,
            output="OK"
        ),
        Test(
            "Var in function",
            code="""
                .a = 0;
                ~b = "";

                void f{;
                    .a = 'A';
                    ~b = "STRING";
                }
                f:;

                print: .a;
                print: ~b;
            """,
            output="ASTRING"
        ),
        Test(
            "Call function in function",    # this test don't do recursive function...
            code="""
                void f1{;
                    print: "F1";
                    f2:;
                }

                void f2{;
                    print: "F2";
                    f3:;
                }

                void f3{;
                    print: "F3";
                }

                f1:;
                print: "OK";
            """,
            output="F1F2F3OK"
        ),
        Test(
            "Return-function simple",
            code="""
                void f{;
                    print: "F";
                    return 'A';
                }

                .a = f:;
                print: .a;
                print: "OK";
            """,
            output="FAOK"
        ),
        Test(
            "Recursive function",
            code="""
                .n = 3;
                .r = 1;

                void factoriel{;
                    if .n == 1 {;
                        print: "OK";
                        }
                    else {;
                        .r = .r * .n;
                        .n = .n - 1;

                        factoriel:;
                        }

                    }

                factoriel:;
                print: '0' + .r;
            """,
            output="OK6"
        ),
        Test(
            "Return function with advanced value parameters",
            code="""
                void f: ~arg1{;
                print: ~arg1;
                return 1;
            }
            .x = f: "STR";
            """,
            output="STR"
        ),
        Test(
            "Advanced return function",
            code="""
                void f1{;
                    print: "F1";
                    return 'A';
                }

                void f2{;
                    print: "F2";
                    return f1:;
                }

                print: f2: + 1;
                print: 1 + f1:;
                print: "OK";
            """,
            output="F2F1BF1BOK"
        ),
        Test(
            "Function with parameters",
            code="""
                void f: .x {;
                    print: .x;
                }

                f: 'A';
                f: 'B';

                print: "OK";
            """,
            output="ABOK"
        ),
        Test(
            "Function with some parameters",
            code="""
                void f: .x, ~string, .a {;
                    print: .x;
                    print: ~string;
                    print: .x + .a;
                    print: .a + 65;
                }

                f: 'A', "STRING", 1;
                f: 'B', "STRING2", 2;
                print: "OK";
            """,
            output="ASTRINGBBBSTRING2DCOK"
        ),
        Test(
            "Function with parameter and return",
            code="""
                void sum: .a, .b {;
                    return .a + .b;
                }

                .x = sum: 'A', 1;
                print: .x;
                .y = sum: 2, 'B';
                print: .y;
                print: "OK";
            """,
            output="BDOK"
        ),
        # --- error ---
        Test(
            "Function with bad parameters 1",
            code="""
                void f {;
                    print: "ERROR";
                }

                f: 1;
            """,
            sucess=False
        ),
        Test(
            "Function with bad parameters 2",
            code="""
                void f: .x {;
                    print: "ERROR";
                }

                f:;
            """,
            sucess=False
        ),
        Test(
            "Invalid syntax with parameters 1",
            code="""
                void f .a {;
                    print: "ERROR";
                }
            """,
            sucess=False
        ),
        Test(
            "Invalid syntax with parameters 2",
            code="""
                void f: .a, {;
                    print: "ERROR";
                }
            """,
            sucess=False
        ),
        Test(
            "Invalid syntax with parameters 3",
            code="""
                void f: error {;
                    print: "ERROR";
                }
            """,
            sucess=False
        )
    )

    COMPILETIME_TEST = (  #test for thte compiletime keyword
        # define
        Test(
            "Define test",
            code="""
                compiletime define VALUE to 'A';
                print: VALUE;
            """,
            output="A"
        ),
        Test(
            "Define test for code",
            code="""
                compiletime define PRINT_A to print: 'A';
                PRINT_A;
            """,
            output="A"
        ),
        Test(
            "Redefine test",
            code="""
                compiletime define VALUE to 'A';
                print: VALUE;
                compiletime define VALUE to 'B';
                print: VALUE;
            """,
            output="AB"
        ),
        # debug mode
        Test(
            "Debug mode test",
            code="""
                compiletime debug True;

                .a = 'A';
                .é = 'B';   // set a character not printable (é)

                print: "OK";
            """,
            output=".A = 'A'\n.? = 'B'\nPRINT: \"OK\"\nOK"
        ),
        Test(
            "Debug mode with remove",
            code="""
                compiletime debug True;

                .a = 'A';
                ~b = "STRING";

                compiletime debug False;

                print: "OK";

                compiletime debug True;

                .c = 'C';

                compiletime debug False;

                print: "OK2";
            """,
            output=""".A = 'A'
?B = "STRING"
COMPILETIME DEBUG FALSE
OK.C = 'C'
COMPILETIME DEBUG FALSE
OK2"""
        ),
        # realloc
        Test(
            "Simple realloc test",
            code="""
                .a = 'A';
                compiletime realloc .a to .b;
                print: .b;
            """,
            output="A"
        ),
        Test(
            "Advanced value realloc",
            code="""
                ~a = "STRING";
                compiletime realloc ~a to ~b;
                print: ~b;
            """,
            output="STRING"
        ),
        Test(
            "Some realloc test",
            code="""
                .a = 'A';
                print: .a;
                compiletime realloc .a to .b;
                print: .b;
                compiletime realloc .b to .c;
                print: .c;
            """,
            output="AAA"
        ),
        Test(
            "Some advanced value realloc",
            code="""
                ~a = "STRING";
                print: ~a;
                compiletime realloc ~a to ~b;
                print: ~b;
                compiletime realloc ~b to ~c;
                print: ~c;
            """,
            output="STRINGSTRINGSTRING"
        ),
        # log
        Test(       # on log test, the log output can't be verrified...
            "Compiletime log test",
            code="""
                compiletime log "This is a log test for compiletime";
                print: "OK";
            """,
            output="OK"
        ),
        # thread
        Test(
            "Compiletime killthread",
            code="""
                thread nostack {;
                    while True{;
                        print: "A";
                    }
                }

                for .i in |0|10|1| {;
                    print: .i + '0';
                }

                compiletime killthread;

                print: "STOP THREAD";

                for .i in |0|10|1| {;
                    print: .i + '0';
                }
            """,
            output="A0A1A2A3A4A5A6A7A8A9AASTOP THREAD0123456789"
        ),
        Test(
            "compiletime start and stop some thread",
            """
                thread nostack {;
                    while True{;
                        print: "A";
                    }
                }

                for .i in |0|10|1| {;
                    print: .i + '0';
                }

                compiletime killthread;

                print: "STOP THREAD";

                for .i in |0|10|1| {;
                    print: .i + '0';
                }
            """ * 10,
            output="A0A1A2A3A4A5A6A7A8A9AASTOP THREAD0123456789" * 10
        ),
        # ---- error ----
        Test(
            "Expected keyword after compiletime",
            code="""
                compiletime;
                print: "ERROR";
            """,
            sucess=False
        ),
        # define
        Test(
            "Define syntax error 1",
            code="""
                compiletime define to 'A';
            """,
            sucess=False
        ),
        Test(
            "Define syntax error 2",
            code="""
                compiletime define VALUE 'A';
            """,
            sucess=False
        ),
        Test(
            "Define syntax error 3",
            code="""
                compiletime define VALUE to;
            """,
            sucess=False
        ),
        # debug
        Test(
            "compiletime debug error 1",
            code="""
                compiletime debug;
                print: "ERROR";
            """,
            sucess=False
        ),
        Test(
            "compiletime debug error 2",
            code="""
                compiletime debug a;
                print: "ERROR";
            """,
            sucess=False
        ),
        # realloc
        Test(
            "compiletime realloc error 1",
            code="""
                compiletime realloc;
                print: "ERROR";
            """,
            sucess=False
        ),
        Test(
            "compiletime realloc error 2",
            code="""
                .a = 'A';
                compiletime realloc .a;
                print: "ERROR";
            """,
            sucess=False
        ),
        Test(
            "compiletime realloc error 3",
            code="""
                .a = 'A';
                compiletime realloc .a to;
                print: "ERROR";
            """,
            sucess=False
        ),
        Test(
            "Compiletime realloc error var not defined",
            code="""
                compiletime realloc .a to .b;
                print: "ERROR";
            """,
            sucess=False
        ),
        Test(
            "Compiletime realloc error var exist",
            code="""
                .a = 'A';
                .b = 'B';
                compiletime realloc .a to .b;
                print: "ERROR";
            """,
            sucess=False
        ),
        Test(
            "Compiletime realloc error same variable",
            code="""
                .a = 'A';
                compiletime realloc .a to .a;
                print: "ERROR";
            """,
            sucess=False
        ),
        Test(
            "Compiletime invalid var name",
            code="""
                .a = 'A';
                compiletime realloc .a to b;
            """,
            sucess=False
        ),
        Test(
            "Compiletime realloc simple to advanced value error",
            code="""
                ~a = "STRING";
                compiletime realloc ~a to .b;
                print: "ERROR";

                .c = 'C';
                compiletime realloc .c to ~d;
                print: "ERROR2";
            """,
            sucess=False
        ),
        Test(
            "Unknow prefix for realloc",
            code="""
                .a = 'A';
                compiletime realloc .a to $b;
                print: "ERROR";
            """,
            sucess=False
        ),
        # log
        Test(
            "Compiletime log error missing string",
            code="""
                compiletime log ;
            """,
            sucess=False
        ),
        Test(
            "Compiletime log error bad value",
            code="""
                compiletime log error;
            """,
            sucess=False
        ),
        # kill thread
        Test(
            "Killthread but no thread running error",
            code="""
                print: "ERROR";
                compiletime killthread;
            """,
            sucess=False
        )
    )

    BUILT_IN = (
        Test(
            "asm_entry test",
            code="""
                asm_entry: "A9 41 20 EF FF";  // print 'A'
                asm_entry: "A9 42 20 EF FF";  // print 'B'

                print: "OK";
            """,
            output="ABOK"
        ),
        Test(
            "asm_entry replace - address",
            code="""
                print: "00000"; // change the address of the asm_entry
                asm_entry: "4C @adress+8| A9 41 20 EF FF "; // the 4C jump after the code for print A
                print: "OK";
            """,
            output="00000OK"
        ),
        Test(
            "asm_entry replace - var",
            code="""
                .a = '@';

                asm_entry: "AD @var_adress:.a| 20 EF FF"; // print the value of .a with the address.
                print: "OK";
            """,
            output="@OK"
        ),
        Test(
            "quit function test",
            code="""
                print: "OK";
                quit:;
                print: "ERROR";
            """,
            output="OK"
        ),
        Test(
            "wozm test",
            code="""
                print: "OK";
                wozm:;
                print: "ERROR";
            """,
            output="OK"
        ),
        Test(
            "restart test",
            code="""
                print: "OK";    // this code can't be run because infinite loop.
                restart:;
            """,
            compile_only=True,
            compile_output="0400: A9 4F 20 EF FF A9 4B 20 EF FF 4C 00 04 00 AD 11 D0 10 FB AD 10 D0 29 7F 60 "
        ),
        Test(
            "Input without return",
            code="""
                input:;
                print: "OK";
            """,
            stdin_test="A",
            output="OK"
        ),
        # --- error ---
        Test(
            "Bad hex on asm_entry",
            code='asm_entry: "A9 41 20 EF FG";',
            sucess=False
        ),
        Test(
            "Bad arg on quit",
            code="quit: 'A';",
            sucess=False
        ),
        Test(
            "Bad arg on wozm",
            code="wozm: 'A';",
            sucess=False
        ),
        Test(
            "Bad arg on input",
            code=".a = input: 'A';",
            sucess=False,
            stdin_test="E", # security if the compilation don't fail
        ),
        Test(
            "Bad arg on restart",
            code="restart: 'A';",
            sucess=False
        ),
        Test(
            "Bad replace on asm_entry - variable name",
            code="""
                asm_entry: "AD @var_adress:.a| 20 EF FF"; // the variable .a is not defined
                print: "ERROR";
            """,
            sucess=False
        ),
        Test(
            "Bad number on asm_entry - address",
            code="""
                asm_entry: "AD @adress+error| 20 EF FF";
                print: "ERROR";
            """,
            sucess=False
        )
    )

    VARIABLE_TEST = (
        Test(
            "Simple variable test",
            code="""
                .x = 1;
                .y = 2;
                print: '0' + .x;
                print: '0' + .y;
            """,
            output="12"
        ),
        Test(
            "Advanced variable test",
            code="""
                ~string = "STRING";
                print: ~string;
                print: ~string[0];
            """,
            output="STRINGS"
        ),
        Test(
            f"{compiller_data_run.MAX_VARIABLE_CREATED - 1} variable created",
            code="".join([f".var_{i} = 0;" for i in range(compiller_data_run.MAX_VARIABLE_CREATED - 1)]),
            output=""
        ),
        # --- error ---
        Test(
            "Variable prefix error",
            code="""
                a = 1;
            """,
            sucess=False
        ),
        Test(
            "Error max variable created",
            code="".join([f".var_{i} = 0;" for i in range(compiller_data_run.MAX_VARIABLE_CREATED + 1)]),
            sucess=False
        ),
        Test(
            "Error max variable created with advanced variable",
            code="".join([f"~str_{i} = \"\";" for i in range(compiller_data_run.MAX_VARIABLE_CREATED // 21)]) + "".join(f".var_{i} = 0;" for i in range(compiller_data_run.MAX_VARIABLE_CREATED % 21 + 1)),
            sucess=False
        )
    )

    TRY_TEST = (   # the test for try/except bloc
        Test(
            "Simple try test",
            code="""
                try{;
                    print: "TRY BLOCK";
                    error 'E';
                    print: "ERROR";
                }
                except{;
                    print: "EXCEPT BLOCK";
                }
                print: "END";
            """,
            output="TRY BLOCKEXCEPT BLOCKEND"
        ),
        Test(
            "Try block without error",
            code="""
                try{;
                    print: "TRY BLOCK";
                }
                except{;
                    print: "EXCEPT BLOCK";
                }
            """,
            output="TRY BLOCK"
        ),
        Test(
            "Try catch index error - 1",
            code="""
                .index = 30;
                ~str = "AAA";
                try{;
                    print: ~str[.index];
                    print: "ERROR";
                }
                except{;
                    print: "EXCEPT BLOCK";
                }
                print: "END";
            """,
            output="EXCEPT BLOCKEND"
        ),
        Test(
            "Try catch index error - 2",
            code="""
                .index = 30;
                ~str = "AAA";
                try{;
                    ~str[.index] = 'A';
                    print: "ERROR";
                }
                except{;
                    print: "EXCEPT BLOCK";
                }
                print: "END";
            """,
            output="EXCEPT BLOCKEND"
        ),
        Test(
            "Try catch divition by 0",
            code="""
                .a = 0;
                try{;
                    print: "TRY BLOCK";
                    .a = 10 / .a;
                    print: "ERROR";
                }
                except{;
                    print: "EXCEPT BLOCK";
                }
                print: "END";
            """,
            output="TRY BLOCKEXCEPT BLOCKEND"
        ),
        Test(
            "Error on except block",
            code="""
                try{;
                    print: "TRY";
                    error 'E';
                }
                except{;
                    print: "EXCEPT";
                    error 'E';
                }
                print: "ERROR";
            """,
            output="TRYEXCEPTEE"
        ),
        Test(
            "Try except block on try except",
            code="""
                try{;
                    print: '1';
                    try{;
                        print: '2';
                        error 'E';
                        }
                    except{;
                        print: '3';
                        }
                    print: '4';
                    error 'E';
                    }

                except{;
                    print: '5';
                    }

                print: '6';
            """,
            output="123456"
        ),
        # --- error ---
        Test(
            "Try without block",
            code="""
                try;
                print: "ERROR";
            """,
            sucess=False
        ),
        Test(
            "Except without block",
            code="""
                try{;
                    print: "TRY";
                }
                except;
            """,
            sucess=False
        ),
        Test(
            "Try missing except",
            code="""
                try{;
                    print: "TRY";
                }
            """,
            sucess=False
        ),
        Test(
            "Except missing try",
            code="""
                except{;
                    print: "EXCEPT";
                }
            """,
            sucess=False
        )
    )

    THREAD_TEST = (
        # --- no stack mode ---
        Test(
            "Simple thread",
            code="""
                thread nostack {;
                    print: "THREAD";
                    print: 'A';
                }
                print: "MAIN";
            """,
            output="THREADMAINA"
        ),
        Test(
            "Loop on thread",
            code="""
            thread nostack {;
                while True{;
                    print: '1';
                }
            }

            for .b in |0|255|1| {;
                print: '2';
            }
            """,
            output="12121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121212121211"
        ),
        # --- shared stack mode ---
        Test(
            "Simple thread with shared stack",
            code="""
                thread nostack {;
                    print: "THREAD";
                    print: 'A';
                }
                print: "MAIN";
            """,
            output="THREADMAINA"
        ),
        Test(
            "Call function on shared stack mode",
            code="""
                void f{;
                    print: 'A';
                }
                void g{;
                    print: 'B';
                }

                thread stack{;
                    for .i in |0|10|1| {;
                        f:;
                    }
                }
                for .k in |0|10|1| {;
                        g:;
                    }
            """,
            output="ABABABABABA"
        ),
        Test(
            "Call a function with long time",  # this test have probleme
            code="""
                void f{;
                    for .i in |0|10|1| {;
                        print: 'A';
                    }
                }
                void g{;
                    for .i in |0|10|1| {;
                        print: 'B';
                   }
                }

                thread stack{;
                    f:;
                }

                g:;
            """,
            output="A" * 10 + "B" * 10 # this test have probleme
        ),
        # --- error ---
        Test(
            "Too many thread",
            code="""
                thread nostack {;
                    print: "THREAD 1";
                }
                thread nostack {;
                    print: "THREAD 2";
                }
                print: "ERROR";
            """,
            sucess=False
        ),
        Test(
            "Call a function in a no shared stack",
            code="""
                void f{;
                    print: "FUNCTION";
                }

                thread nostack {;
                    f:;
                }
                print: "ERROR";
            """,
            sucess=False
        ),
        Test(
            "Syntax error on thread - 1",
            code="""
                thread;
                print: "ERROR";
            """,
            sucess=False
        ),
        Test(
            "Syntax error on thread - 2",
            code="""
                thread uknow_option{;
                    print: "ERROR";
                }
            """,
            sucess=False
        ),
        Test(
            "Syntax error on thread - 3",
            code="""
                thread {;
                    print: "ERROR";
                }
            """,
            sucess=False
        )
    )

    MOD_TEST = (
        Test(
            "Simple module test",
            code="""
                .modulo = 10 % 3;
                print: .modulo + '0';
            """,
            output="1"
        ),
        Test(
            "Modulo with variable test",
            code="""
                .a = 20;
                .b = 3;
                .modulo = .a % .b;
                print: .modulo + '0';
            """,
            output="2"
        ),
        # --- error ---
        Test(
            "Modulo by zero test",
            code="""
                .a = 0; // need a runtime value
                .modulo = 10 % .a;
                print: "ERROR";
            """,
            sucess=False
        ),
        Test(
            "Sintaxe error on modulo",
            code="""
                .modulo = 10 %;
                print: "ERROR";
            """,
            sucess=False
        )
    )

    SHEBANG_TEST = (
        Test(
            "Shebang test",
            code="""#!/usr/bin/smart_emulator
                print: "OK";
            """,
            output="OK"
        ),
        Test(
            "Empty shebang",
            code="""#!
                print: "OK";
            """,
            output="OK"
        ),
        # --- error ---
        Test(
            "Shebang no in first line - 1",
            code="""
                print: "ERROR";
#!/usr/bin/smart_emulator
            """,
            sucess=False
        ),
        Test(
            "Shebang no in first line - 2",
            code="""

#!/usr/bin/smart_emulator
                print: "ERROR";
            """,
            sucess=False
        )
    )

    PTR_FUNCTION = (
        Test(
            "Simple pointer on arg",
            code="""
                void f: *~arg {;
                    print: ~arg;
                    ~arg = "STRING2";
                }

                ~my_value = "STRING1";
                f: ~my_value;
                print: ~my_value;
            """,
            output="STRING1STRING2"
        ),
        Test(
            "Advenced pointer on arg",
            code="""
                void f: *.arg1, *.arg2, *~str1 {;
                    print: .arg1;
                    print: .arg2;
                    print: ~str1;

                    .arg1 = 'A';
                    .arg2 = 'B';
                    ~str1 = "STRING2";
                }

                .a = '1';
                .b = '2';
                ~my_str = "HELLO";
                f: .a, .b, ~my_str;

                print: .a;
                print: .b;
                print: ~my_str;
            """,
            output="12HELLOABSTRING2"
        ),
        Test(
            "Return function with ptr",
            code="""
                void f: *.x, *~str {;
                    print: .x;
                    print: ~str;

                    .x = 'A';
                    ~str = "NEW STRING";

                    return '@';
                }

                .a = '1';
                ~my_str = "HELLO";
                .c = f: .a, ~my_str;

                print: .a;
                print: ~my_str;
                print: .c;
            """,
            output="1HELLOANEW STRING@"
        ),
        Test(
            "Recurcive pointer",
            code="""
                void f1: *.arg1{;
                    .arg1 = 'A';
                }
                void f2: *.arg2{;
                    f1: .arg2;
                }

                .a = 0;
                f2: .a;
                print: .a;
            """,
            output="A"
        ),
        # --- error ---
        Test(
            "Set on ptr a value imediate",
            code="""
                void f: *.x, *~str {
                    .x = 1;
                    ~str = "STRING";
                    print: "ERROR";
                }
                f: 0, "HELLO";
            """,
            sucess=False
        )
    )


    GLOBAL_TESTS = SYNTAXE_ERROR_TEST + TESTS + MATH_TEST + RUNTIME_ERROR_TEST + MODULES_TEST + BOOLEAN_TEST + TEST_INT_HEX + TEST_CHAR + ADVENCED_VALUE_TEST + REGISTER_TESTS + GOTO_TEST + IF_TEST + WHILE_TEST + ESCAPE_CHARACTER + BUILT_IN + FUNCTION_TEST + TEST_LIB + FOR_TEST + COMPILETIME_TEST + VARIABLE_TEST + ERROR_VARIABLE_KEYWORD + TEST_COMPARATOR + TRY_TEST + THREAD_TEST + INCREMENT_DECREMENT + MOD_TEST + SHEBANG_TEST + PTR_FUNCTION

    try:
        for test in GLOBAL_TESTS:
            if isinstance(test, ModuleTest):
                test.run_modules()
            else:
                test.run()
    except StopTest as st:
        print(f"{Colors.BG_YELLOW}{st}{Colors.RESET}")

    if all_ok:
        print(f"{TEST_OK}{Colors.BG_GREEN}All tests without error!{Colors.RESET}\n({len(GLOBAL_TESTS)} tests run).")
    else:
        print(
            f"{TEST_ERROR}{Colors.BG_RED}Some tests failed!{Colors.RESET}",
            f"{Colors.RED}Error: {error_counter}/{len(GLOBAL_TESTS)}{Colors.RESET}",
        )

    print(f"\n{Colors.RED}{round(error_counter / len(GLOBAL_TESTS) * 100, 2)}%{Colors.RESET} | {Colors.GREEN}{round((len(GLOBAL_TESTS) - error_counter) / len(GLOBAL_TESTS) * 100, 2)}%{Colors.RESET}")

except KeyboardInterrupt:
    print(f"\n{Colors.BG_YELLOW}Test stopped by user\nKeyboard interrupt.{Colors.RESET}")

except Exception as e:
    print(
        f"{Colors.BG_RED}An error occurred during test: {e}{Colors.RESET}",
        traceback.format_exc(),
        sep="\n"
    )