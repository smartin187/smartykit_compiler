# -*- coding: utf-8 -*-

"""
The compiller for smart.

Function: compile_smart to start compiling a smart code.
"""

from pathlib import Path
import os
import logging
import re
import traceback

from compiller_tool.string_tool import split_code, replace_code, in_code, good_variable_name, get_char_from_str, get_bloc, get_int_adress_from_str, get_hex_from_int, adress_for_RAM, get_str, get_char, control_hex
from compiller_tool.color_tool import ColoredFormatter
from compiller_tool.smart_exception import CompileError, SmartError, config_exception, confirm_user
from compiller_tool.smart_info import GIT_HUB_LINK
from compiller_tool.hex_function import build_asm_entry, config_hex_function, make_error, imediate_value
from compiller_tool.smart_try_except import control_except
from compiller_tool.compiller_data_run import PROGRESS_BAR_LEN, PROGRESS_BAR_CHAR
from compiller_tool import compiller_data_run
from compiller_tool import import_tool
from compiller_tool import smart_obj
from compiller_tool import color_tool
from compiller_tool import compile_command

from compiller_tool.asm_tool import verryfing_adress_conter_no_print, get_adress # use only for debug, not needed for compilation

logging.basicConfig(
    format="SmartCompiller %(levelname)s: %(message)s",
    level=logging.INFO
)

for handler in logging.root.handlers:
    handler.setFormatter(ColoredFormatter('SmartCompiller %(levelname)s: %(message)s'))
    handler.terminator = ""

FUNCTION_PATTERN = "^[a-z_][a-z0-9_]*.*:"

code_line = None

line_of_instruction = None

need_input = False

def compile_smart(
        file:str="",
        argv:list[str] | tuple[str]=[],
        CODE_ADRESSE:int=0x400,
        make_file:bool=True,
        function_mode:dict[
            str,
            bool | str | list | dict | smart_obj.SmartFunction | None
        ]={"function_mode":False, "source_code":"", "global_function":[], "global_function_replace":[], "global_var":{}, "smart_func":None, "if_mode":False, "global_goto":{}, "goto_replace":[], "while_mode":False},
        bin_outpout_file:bool=False,
        module_name:str="*", # module name is '*' if main module.
        smart_var_module:dict[str, smart_obj.SmartObj]={}, # the address of first free adress of variable for module
        regroup_bytes:int=-1, # for rendering the code. -1 for 1 line of hex, other value to regroup bytes into lines.
        first_call:bool=False,
        try_mode:bool=False,
        thread_mode:list[bool, str, bool, bool]=[False, "", False, False]
    ) -> str:
    """Start compiling from a file."""
    global line_of_instruction, code_line
    logging.info("Starting compiller...")

    module_mode = module_name != "*"
    class SmartBuiltIn:
        """Set the built-in functions of Smart.
        Warning: some functions are not in this class because they are assembly functions (print, goto...)"""

        input_code = "AD 11 D0 10 FB AD 10 D0 29 7F 60 "
        @staticmethod
        def smartInput() -> tuple[str, int]:
            """Add an input function. Return a tuple with hex code and length of hex code."""
            global need_input
            need_input = True
            return "20 !  smart_input", 3

        BUILT_IN_NAME_RETURN = ["input"]
        BUILT_IN_NAME_NORETURN = ["print", "quit", "goto", "asm_entry"]

        BUILT_IN_NAME = BUILT_IN_NAME_RETURN + BUILT_IN_NAME_NORETURN

    def line_of_instruction(nb_instruction:int) -> tuple[int, str]:
        """Return the line number and the content of the instruction."""
        nb = 0
        line_counter = 0

        for line in code_line:

            nb += line.count(";")

            line_counter += 1

            if nb_instruction + 1 <= nb:
                return (line_counter + 1, code_line[line_counter-1])

        return (line_counter + 1, code_line[line_counter-1])

    config_exception(line_of_instruction)

    def smart_error(msg:str, _line_conter:int=-1, set_error:bool=True) -> None:
        """Raise SmartError with the line of the instruction."""
        if _line_conter == -1:
            _line_conter = line_counter

        raise SmartError(msg, _line_conter, set_error=set_error)

    def get_start_end(start_number:str, end:str, step:str, no_var_for:bool, adress_iterrator:str, advenced_value_mode:bool=False) -> str:
        """Return the hex code for the for loop. The code is used to increment the counter. Return start_loop_for."""
        nonlocal address_counter, code_compile, adress_var, smart_var
        for i in range(3):  # the address for counting
            compiller_data_run.not_used_for += 1
            make_variable(smart_obj.ReservedAdress(adress_var), name=f"NotUsedRAMFor{compiller_data_run.not_used_for}")

        adress_start_number = adress_for_RAM(adress_var - 1)
        adress_end = adress_for_RAM(adress_var - 2)
        adress_step = adress_for_RAM(adress_var)

        code_compile += set_on_A_value(step)   # load the step
        code_compile += f"8D {adress_step} "     # save at the first RAM for step
        address_counter += 3

        code_compile += set_on_A_value(start_number)   # load the start number
        code_compile += f"8D {adress_start_number} "     # save at the second RAM for start number
        address_counter += 3

        code_compile += set_on_A_value(end)   # load the end number
        code_compile += f"8D {adress_end} "     # save at the third RAM for end number
        address_counter += 3

        # start loop

        start_loop_for = adress_for_RAM(CODE_ADRESSE + address_counter)

        code_compile += f"AD {adress_start_number} "   # load the start on A
        address_counter += 3

        if not no_var_for:
            code_compile += f"8D {adress_iterrator} "     # save the start on the iterator RAM
            address_counter += 3
        elif advenced_value_mode:
            code_compile += f"AA "  # transfer the offset for iteration to X
            address_counter += 1

        code_compile += f"CD {adress_end} "     # compare with the end
        address_counter += 3

        code_compile += "D0 03 "  # branch if A != end
        address_counter += 2
        code_compile += "4C ! smart:break "  # if not branch, exit loop.
        address_counter += 3

        # increment start:
        if not advenced_value_mode:
            code_compile += f"18 6D {adress_step} 8D {adress_start_number} "     # increment the start number by step
            address_counter += 7
        else:
            code_compile += f"18 69 01 8D {adress_start_number} "     # increment the start number by 1 (because advanced value)
            address_counter += 6

        return start_loop_for

    def code_ptr_func(function_name: str, function_arg: list[str]) -> tuple[str, int]:
        """Build the code for the function argument pointer."""

        code_compile = ""
        address_counter = 0

        # set the ptr argument
        for i, parameter in enumerate(function_name_usr[function_name].parameters):
            if parameter.ptr_function:
                ptr_return = function_arg[i]

                if not ptr_return.startswith(".") and not ptr_return.startswith("~"):
                    raise SmartError(f"Function {function_name} need a pointer argument. Need a variable name (simple variable or advenced variable), not '{ptr_return}' for this argument.")

                var_return = get_variable(ptr_return[1:])

                if isinstance(var_return, smart_obj.SmartVariable):
                    code_compile += f"AD {adress_for_RAM(parameter.ram_adress)} " # LDA parameter
                    address_counter += 3

                    code_compile += f"8D {adress_for_RAM(var_return.ram_adress)} " # STA variable
                    address_counter += 3
                else:
                    base_adress_var = var_return.ram_adress
                    base_adress_parameter = parameter.ram_adress

                    if var_return.size != parameter.size:  # actually, all advenced obj have size=21, but suceptible to change
                        raise SmartError(f"Variable {var_return.name} have diferent size of {parameter.size}.")

                    for offset in range(var_return.size):

                        code_compile += f"AD {adress_for_RAM(base_adress_parameter + offset)} " # LDA parameter
                        address_counter += 3

                        code_compile += f"8D {adress_for_RAM(base_adress_var + offset)} " # STA variable
                        address_counter += 3

        return code_compile, address_counter

    def set_on_A_value(value:str, recursiv_value:bool=False, forbiden_math:bool=False, test_value_mode:bool=False, add_adress:bool=True) -> str:
        """Return the value for set one A.
        arg: test_value_mode: if True, not print the error message on console (but raise SmartError).
        """
        global counter_adress_value
        nonlocal address_counter

        set_error_exception = not test_value_mode

        def control_math() -> None:
            """If forbiden_math is True, raise SmartError if there is math in the value."""
            if forbiden_math:
                smart_error(f"Math is forbidden for this value: '{value}'", set_error=set_error_exception)

        def set_branch(value:str, operator:str, branche:str) -> str:
            """Return the hex code for a branch comparison."""
            global counter_adress_value
            try:
                value_1, value_2 = split_code(value, operator, max_split=1)

                if is_a_simple_value(value_1) and is_a_simple_value(value_2):

                    hex_value_1 = set_on_A_value(value_1, recursiv_value=True)

                    hex_value_2 = set_on_A_value(value_2, recursiv_value=True)

                    if not imediate_value(hex_value_2):

                        asm = f"{hex_value_1}CD {hex_value_2[3:]}"      # address value

                    else:
                        asm = f"{hex_value_1}C9 {hex_value_2[3:]}"      # immediate value
                        counter_adress_value -= 1

                    asm += f"{branche} 04 A9 01 D0 02 A9 00 "

                    counter_adress_value += 9

                    return asm

                elif (not is_a_simple_value(value_1)) and (not is_a_simple_value(value_2)):

                    # load at SaveStr (smart system) value 1:

                    adress_v_1 = int(compiller_data_run.SYS_ADRESS["SaveStr"].split(" ")[1] + compiller_data_run.SYS_ADRESS["SaveStr"].split(" ")[0], base=16)

                    hex_value_1 = set_on_ram_str(value_1, adress_v_1, add_adress=False)

                    counter_adress_value += hex_value_1.count(" ")


                    asm = hex_value_1

                    adress_v_2 = int(compiller_data_run.SYS_ADRESS["SaveStrCMP"].split(" ")[1] + compiller_data_run.SYS_ADRESS["SaveStrCMP"].split(" ")[0], base=16)

                    hex_value_2 = set_on_ram_str(value_2, adress_v_2, add_adress=False)

                    counter_adress_value += hex_value_2.count(" ")

                    asm += hex_value_2


                    # compare with value 2
                    for i in range(smart_obj.SIZE_ADVANCED_OBJ):
                        asm += f"AD {adress_for_RAM(adress_v_1 + i)} CD {adress_for_RAM(adress_v_2 + i)} F0 03 4C !smart:adress_false "

                    counter_adress_value += 11 * smart_obj.SIZE_ADVANCED_OBJ

                    # set A to 1 and goto after A9 00 if not branch
                    asm += f"A9 01 4C {adress_for_RAM(CODE_ADRESSE + address_counter + counter_adress_value + 7)} "

                    counter_adress_value += 5

                    asm = asm.replace("!smart:adress_false", adress_for_RAM(CODE_ADRESSE + counter_adress_value + address_counter))

                    asm += "A9 00 "       # BNE set to this code
                    counter_adress_value += 2

                    return asm

                else:
                    smart_error(f"Can't compare advanced value with value: `{value}`", set_error=set_error_exception)


            except SmartError as se:
                smart_error(str(se), se.nbline, set_error=set_error_exception)


        def eval_value() -> str:
            """Return asm value."""
            global counter_adress_value
            nonlocal address_counter, code_compile

            if in_code("*", value):
                control_math()
                try:
                    value_1, value_2 = split_code(value, "*", max_split=1)

                    asm = ""

                    hex_value_1 = set_on_A_value(value_1, recursiv_value=True)

                    asm += hex_value_1 + f"8D {compiller_data_run.SYS_ADRESS['MathOP']}A9 00 "  # save value 1 on ram and set A to 00.
                    counter_adress_value += 5

                    value_2_tmp = set_on_A_value(value_2, recursiv_value=True)

                    hex_value_2 = "A2" + value_2_tmp[2:] if value_2_tmp.startswith("A9") else "AE" + value_2_tmp[2:]

                    asm += hex_value_2

                    asm += "CA "    # decrement X
                    counter_adress_value += 1

                    asm += f"18 6D {compiller_data_run.SYS_ADRESS['MathOP']}"   # add to A hex_value_2
                    asm += "E0 00 D0 F7 "   # continue or not the loop

                    counter_adress_value += 8

                    return asm

                except SmartError as se:
                    smart_error(str(se), se.nbline, set_error=set_error_exception)

                except:
                    smart_error(f"Error with math '*' : '{value}'", set_error=set_error_exception)

            elif in_code("/", value):
                control_math()
                try:
                    value_1, value_2 = split_code(value, "/", max_split=1)

                    asm = ""

                    hex_value_2 = set_on_A_value(value_2, recursiv_value=True)

                    asm += hex_value_2 + f"8D {compiller_data_run.SYS_ADRESS['MathOP']}"  # save value 2 on ram
                    counter_adress_value += 3

                    # control division by 0

                    error_code, _ = make_error("'/'", try_mode, add_to_adress_conter=False)

                    control_code = "C9 00 D0 !smart:len_error {}".format(error_code)

                    control_code = control_code.replace("!smart:len_error", get_hex_from_int(error_code.count(" ")))

                    counter_adress_value += control_code.count(" ")

                    asm += control_code

                    if hex_value_2 == "A9 00 ":       # division by 0
                        confirm_user(f"Division by 0: {value}. It make an runtime error `E/`! Continue compilation ? ", line_counter=line_counter)

                    hex_value_1 = set_on_A_value(value_1, recursiv_value=True)

                    asm += hex_value_1

                    asm += f"CD {compiller_data_run.SYS_ADRESS['MathOP']}"
                    asm += "90 0A "
                    counter_adress_value += 5

                    asm += "A2 00 E8 "    # set X to 00, and increment X on loop.
                    counter_adress_value += 3

                    asm += f"38 ED {compiller_data_run.SYS_ADRESS['MathOP']}"      # substract to A hex_value_2
                    asm += f"CD {compiller_data_run.SYS_ADRESS['MathOP']}B0 F6 "   # continue or not the loop

                    counter_adress_value += 9

                    asm += "8A "
                    counter_adress_value += 1

                    return asm

                except SmartError as se:
                    smart_error(str(se), se.nbline, set_error=set_error_exception)

                except:
                    print(traceback.format_exc())
                    smart_error(f"Error with math '/' : '{value}'", set_error=set_error_exception)

            elif in_code("%", value):
                control_math()
                try:
                    value_1, value_2 = split_code(value, "%", max_split=1)

                    asm = ""

                    hex_value_2 = set_on_A_value(value_2, recursiv_value=True)

                    asm += hex_value_2 + f"8D {compiller_data_run.SYS_ADRESS['MathOP']}"  # save value 2 on ram
                    counter_adress_value += 3

                    # control division by 0

                    error_code, _ = make_error("'/'", try_mode, add_to_adress_conter=False)

                    control_code = "C9 00 D0 !smart:len_error {}".format(error_code)

                    control_code = control_code.replace("!smart:len_error", get_hex_from_int(error_code.count(" ")))

                    counter_adress_value += control_code.count(" ")

                    asm += control_code

                    if hex_value_2 == "A9 00 ":       # division by 0
                        confirm_user(f"Division by 0 (on % (modulo) operator): {value}. It make an runtime error `E/`! Continue compilation ? ", line_counter=line_counter)

                    hex_value_1 = set_on_A_value(value_1, recursiv_value=True)

                    asm += hex_value_1

                    asm += f"CD {compiller_data_run.SYS_ADRESS['MathOP']}"
                    asm += "90 0A "
                    counter_adress_value += 5

                    asm += "A2 00 E8 "    # set X to 00, and increment X on loop.
                    counter_adress_value += 3

                    asm += f"38 ED {compiller_data_run.SYS_ADRESS['MathOP']}"      # substract to A hex_value_2
                    asm += f"CD {compiller_data_run.SYS_ADRESS['MathOP']}B0 F6 "   # continue or not the loop

                    counter_adress_value += 9

                    return asm

                except SmartError as se:
                    smart_error(str(se), se.nbline, set_error=set_error_exception)

                except:
                    print(traceback.format_exc())
                    smart_error(f"Error with math '%' : '{value}'", set_error=set_error_exception)



            elif in_code("+", value):    # addition
                control_math()
                try:
                    value_1, value_2 = split_code(value, "+", max_split=1)

                    hex_value_1 = set_on_A_value(value_1, recursiv_value=True)

                    counter_adress_value += 1       # add for the OP code 18

                    hex_value_2 = set_on_A_value(value_2, recursiv_value=True)

                    if not imediate_value(hex_value_2):     # address value
                        asm = f"{hex_value_1}18 6D {hex_value_2[3:]}"

                    else:
                        asm = f"{hex_value_1}18 69 {hex_value_2[3:]}"       # immediate value

                    return asm

                except SmartError as se:
                    smart_error(str(se), se.nbline, set_error=set_error_exception)

                except:
                    smart_error(f"Error with math '+' : '{value}'", set_error=set_error_exception)

            elif in_code("-", value):    # subtraction
                control_math()
                try:
                    value_1, value_2 = split_code(value, "-", max_split=1)

                    hex_value_1 = set_on_A_value(value_1, recursiv_value=True)

                    counter_adress_value += 1       # add for the OP code 18

                    hex_value_2 = set_on_A_value(value_2, recursiv_value=True)

                    if not imediate_value(hex_value_2):
                        asm = f"{hex_value_1}38 ED {hex_value_2[3:]}"       # address value

                    else:
                        asm = f"{hex_value_1}38 E9 {hex_value_2[3:]}"      # immediate value

                    return asm

                except SmartError as se:
                    smart_error(str(se), se.nbline, set_error=set_error_exception)

                except:
                    smart_error(f"Error with math '-' : '{value}'", set_error=set_error_exception)

            elif in_code("==", value):
                return set_branch(value, "==", "D0")

            elif in_code("!=", value):
                return set_branch(value, "!=", "F0")

            elif in_code(">=", value):
                return set_branch(value, ">=", "90")

            elif in_code("<", value):
                return set_branch(value, "<", "10")

            elif value.startswith(".."):   # a value from return function
                adress_return = adress_for_RAM(int(value[2:-1]))

                counter_adress_value += 3

                return f"AD {adress_return} "

            elif value.startswith("."):
                variable = value[1:]


                counter_adress_value += 3


                return f"AD {adress_for_RAM(get_variable(variable).ram_adress)} "

            elif value.startswith("~"):       # advanced variable, need index
                try:
                    advenced_var_name = value[1:].split("[", 1)[0]

                    obj_var = get_variable(advenced_var_name)

                    index_mode, index_var = obj_var.get_index(value, test_mode=test_value_mode)

                    if index_mode:
                        index_adress_var = obj_var.get_adress_from_index(index_var)

                        counter_adress_value += 3

                        return f"AD {adress_for_RAM(index_adress_var)} "

                    else:

                        # save A at smart sys
                        asm = f"8D {compiller_data_run.SYS_ADRESS['SaveAToIndex']}"
                        counter_adress_value += 3

                        asm += set_on_A_value(index_var, recursiv_value=True, test_value_mode=test_value_mode) + "AA "
                        counter_adress_value += 1

                        start_adress_var = obj_var.get_adress_from_index(0)

                        hex_start_adress_var = adress_for_RAM(start_adress_var)

                        # test index out of range on runtime error
                        test_index = "C9 15 "    # CMP #0x15
                        counter_adress_value += 2

                        test_index += "90 !smart:len_error_index "     # branch if index > 21
                        counter_adress_value += 2

                        error_code, _ = make_error("'I'", try_mode, add_to_adress_conter=False)
                        test_index = test_index.replace("!smart:len_error_index", get_hex_from_int(error_code.count(" ")))

                        test_index += error_code
                        counter_adress_value += error_code.count(" ")

                        asm += test_index

                        asm += f"BD {hex_start_adress_var} "    # LDA $start_adress_var,X

                        counter_adress_value += 3

                        return asm


                except:
                    smart_error(f"Invalid value for '{value}': can't use an advanced variable for this operation.", set_error=set_error_exception)


            elif value.startswith("True"):
                counter_adress_value += 2
                return "A9 01 "

            elif value.startswith("False"):
                counter_adress_value += 2
                return "A9 00 "

            elif value.startswith("0x"):
                hex_value = value[2:]

                control_hex(hex_value)

                counter_adress_value += 2


                return "A9 " + hex_value + " "


            elif value[0] in "0123456789":
                if len(value) > 3:
                    smart_error(f"Invalid value: {value}", set_error=set_error_exception)

                try:
                    value_int = int(value)
                except:
                    smart_error(f"Invalid int value: {value}", set_error=set_error_exception)

                if value_int > 255:
                    smart_error(f"Invalid value: {value_int}, max int value is 255", set_error=set_error_exception)

                value_int_to_hex = hex(value_int)[2:].upper()

                value_hex = ("0" if len(value_int_to_hex) == 1 else "") + value_int_to_hex

                counter_adress_value += 2

                return "A9 " + value_hex + " "

            elif value.startswith("'"):
                counter_adress_value += 2

                ascii_code = get_char(value)

                return "A9 " + ("0" * (2-len(ascii_code))) + ascii_code + " "

            elif value.startswith("\""):
                smart_error(f"Smart forbidden value: '{value}'", set_error=set_error_exception)


            else:
                smart_error(f"Smart value error: {value}", set_error=set_error_exception)

        asm_v = ""

        if not recursiv_value:
            counter_adress_value = 0

            # for return function:
            data_function = value
            for operator in compiller_data_run.OPERATOR:
                data_function = data_function.replace(operator, "+")

            parts = data_function.split("+")

            for part in parts:
                if in_code(":", part):

                    func_name_value, func_arg_value = part.split(":", 1)

                    func_arg_value = func_arg_value.replace(" ", "")

                    if func_arg_value:
                        func_arg_value_list = func_arg_value.split(",")
                    else:
                        func_arg_value_list = []

                    if func_name_value in SmartBuiltIn.BUILT_IN_NAME_RETURN:
                        if func_name_value == "input":
                            hex_code_input, delta_adress = SmartBuiltIn.smartInput()
                            counter_adress_value += delta_adress
                            asm_v += hex_code_input


                            # save on RAM value return:
                            compiller_data_run.not_used_ram += 1
                            var_obj = smart_obj.SmartVariable(f"!smart_return_value{compiller_data_run.not_used_ram}", adress_var)
                            var_adress = var_obj.ram_adress

                            make_variable(var_obj)

                            asm_v += f"8D {adress_for_RAM(var_adress)} "

                            counter_adress_value += 3

                            value = value.replace(part, f"..{var_adress} ")

                            continue

                    elif func_name_value in SmartBuiltIn.BUILT_IN_NAME_NORETURN:
                        smart_error(f"Built in function {func_name_value} is not a return-function.", set_error=set_error_exception)

                    else:

                        if func_name_value in function_name_usr:
                            if not function_name_usr[func_name_value].return_value:
                                smart_error(f"Function '{func_name_value}' is not a return-function.", set_error=set_error_exception)

                        else:
                            smart_error(f"Function '{func_name_value}' not exist.", set_error=set_error_exception)

                        # set the argument:
                        hex_code = ""

                        function_parameters = function_name_usr[func_name_value].parameters
                        if len(func_arg_value_list) != len(function_parameters):
                            smart_error(f"Function '{func_name_value}' take {len(function_parameters)} parameters, but {len(func_arg_value_list)} was given.")

                        for i, parameter in enumerate(function_parameters):

                            if isinstance(parameter, smart_obj.SmartVariable):
                                adress_parameter = parameter.ram_adress

                                hex_code += set_on_A_value(func_arg_value_list[i], recursiv_value=True, test_value_mode=test_value_mode)

                                hex_code += f"8D {adress_for_RAM(adress_parameter)} "
                                counter_adress_value += 3

                            elif isinstance(parameter, smart_obj.SmartStr):
                                adress_parameter = parameter.ram_adress

                                hex_code += set_on_ram_str(func_arg_value_list[i], adress_parameter, add_adress=False)

                                counter_adress_value += hex_code.count(" ")

                            else:
                                smart_error(f"Unknown type of parameters for function '{func_name_value}'.")



                        text_code = f"!smart_call_func|{func_name_value}"

                        function_replace.append(text_code)

                        counter_adress_value += 3

                        asm_v += hex_code + text_code

                        # save on RAM value return:
                        compiller_data_run.not_used_ram += 1
                        var_obj = smart_obj.SmartVariable(f"!smart_return_value{compiller_data_run.not_used_ram}", adress_var)
                        var_adress = var_obj.ram_adress

                        make_variable(var_obj)

                        asm_v += f"8D {adress_for_RAM(var_adress)} "

                        counter_adress_value += 3

                        hex_code_ptr, delta_adress_ptr = code_ptr_func(func_name_value, func_arg_value_list)

                        asm_v += hex_code_ptr
                        counter_adress_value += delta_adress_ptr

                        value = value.replace(part, f"..{var_adress} ")


        asm_v += eval_value()

        if add_adress and not recursiv_value:
            address_counter += asm_v.count(" ") + asm_v.count("!smart_call_func|") * 3

        return asm_v


    def is_a_simple_value(value:str) -> bool:
        """Return True if the value is a value to set on A (uses 1 byte), False otherwise (if the value is a str, uses 21 bytes)."""
        try:
            set_on_A_value(value, test_value_mode=True, add_adress=False)
            return True
        except SmartError:
            return False

    def set_on_ram_str(string_or_variable:str, start_adress:int, add_adress:bool=True) -> str:
        """Return the hex code to set a string in RAM."""
        nonlocal address_counter

        string_or_variable = replace_code(string_or_variable, " ", "")

        if string_or_variable.startswith("~"):   # advanced variable
            var_name = string_or_variable[1:]

            code_hex_copy = ""

            for i in range(smart_obj.SIZE_ADVANCED_OBJ):
                code_hex_copy += f"AD {adress_for_RAM(get_variable(var_name).ram_adress + i)} 8D {adress_for_RAM(start_adress + i)} "

            if add_adress:
                address_counter += 6 * smart_obj.SIZE_ADVANCED_OBJ

            return code_hex_copy

        elif string_or_variable.startswith("\""):   # str value

            str_value = get_str(string_or_variable, line_counter)


            len_str = len(str_value)

            if len_str > smart_obj.SIZE_ADVANCED_OBJ:
                smart_error(f"String too long: '{str_value}', max length is {smart_obj.SIZE_ADVANCED_OBJ} for set on RAM (variable).")

            for i in range(smart_obj.SIZE_ADVANCED_OBJ - len_str):
                str_value += "\0"

            code_str = ""

            for char in str_value:
                char_code = hex(ord(char))[2:].upper()
                char_code = ("0" if len(char_code) == 1 else "") + char_code

                code_str += f"A9 {char_code} 8D {adress_for_RAM(start_adress)} "

                start_adress += 1

            if add_adress:
                address_counter += 105

            return code_str

        elif string_or_variable.startswith("F\""):      # F-string
            str_value = get_str(string_or_variable[1:], line_counter)

            code_str = ""

            len_counter = 0

            f_bloc_len = 0

            char_counter = 0

            while char_counter < len(str_value):
                char = str_value[char_counter]
                if f_bloc_len:
                    f_bloc_len -= 1
                    continue

                if char == "{":
                    f_bloc = str_value[char_counter + 1:].split("}", 1)[0]

                    code_str += set_on_A_value(f_bloc, add_adress=False) + f"8D {adress_for_RAM(start_adress)} "

                    f_bloc_len = len(f_bloc)
                    char_counter += f_bloc_len + 2

                    len_counter -= 1

                else:

                    char_code = hex(ord(char))[2:].upper()
                    char_code = ("0" if len(char_code) == 1 else "") + char_code

                    code_str += f"A9 {char_code} 8D {adress_for_RAM(start_adress)} "

                    char_counter += 1

                start_adress += 1
                len_counter += 1

            if len_counter > smart_obj.SIZE_ADVANCED_OBJ:
                smart_error(f"F-string too long: '{str_value}', max length is {smart_obj.SIZE_ADVANCED_OBJ}.")

            if add_adress:
                address_counter += code_str.count(" ")

            return code_str


        elif string_or_variable.startswith("["):    # list
            if not string_or_variable.endswith("]"):
                smart_error(f"Syntax error: on '{string_or_variable}', bracket '[' was never closed")

            list_value = string_or_variable[1:-1].split(",")

            len_list = len(list_value)

            if len_list > smart_obj.SIZE_ADVANCED_OBJ:
                smart_error(f"List too long: '{string_or_variable}', max length is {smart_obj.SIZE_ADVANCED_OBJ}.")

            for i in range(smart_obj.SIZE_ADVANCED_OBJ - len_list):
                list_value.append("0")

            code_list = ""

            for element in list_value:
                element = element.strip()
                code_list += f"{set_on_A_value(element)}8D {adress_for_RAM(start_adress)} "

                start_adress += 1

            if add_adress:
                address_counter += 3 * smart_obj.SIZE_ADVANCED_OBJ

            return code_list

        logging.critical(f"Error with set_on_ram_str: '{string_or_variable}'.")
        smart_error(f"Unknown string or variable: '{string_or_variable}'.")

    def get_variable(var_name:str, special_name:bool=False) -> smart_obj.SmartObj:
        """This function returns the smart variable (SmartObj) from the name of variable.
        The smart obj can be SmartVariable, SmartStr...

        If the variable doesn't exist or the name is invalid, raise SmartError.
        If special_name=True, don't raise SmartError if name is invalid (use for reserved address).
        """
        if not good_variable_name(var_name) and not special_name:
            smart_error(f"Invalid syntax: '{var_name}', expected a variable name.")

        if var_name not in smart_var:
            smart_error(f"Name error : name '{var_name}' is not defined.")

        return smart_var[var_name]

    def make_variable(var_obj:smart_obj.SmartObj, name:str | None = None, add_adress_advenced_value:bool=False) -> None:
        """Store a Smart object (can be SmartVariable, SmartStr...) in smart_var.
        If the Smart memory is full, raise SmartError.
        """
        nonlocal adress_var
        var_name = var_obj.name if name is None else name

        logging.info(f"Building new Smart object: {var_name} at {hex(adress_var)}")

        if add_adress_advenced_value:
            adress_var += 1 if not isinstance(var_obj, smart_obj.AdvancedObj) else var_obj.size
        else:
            adress_var += 1

        if var_name in smart_var:
            raise SmartError(f"Variable '{var_name}' already exist. You can't name a new object with this name.")

        smart_var[var_name] = var_obj

        if adress_var >= compiller_data_run.MAX_VARIABLE_CREATED + compiller_data_run.START_ADRESS_VAR:
            smart_error(f"Smart memory is full. You can't make more {compiller_data_run.MAX_VARIABLE_CREATED} bytes for variables.\nThe variable '{var_name}' can't be created...\n{color_tool.Colors.YELLOW}You can use compiletime realloc for reuse space of a variable.{color_tool.Colors.RESET}")



    import_tool.config_import(compile_smart)
    config_hex_function(set_on_A_value)

    def hex_parameters(function_name_usr:dict, function_name:str, function_arg:list) -> str:
        """Return the hex code for the parameters of the function."""
        nonlocal address_counter

        hex_code = ""

        function_parameters = function_name_usr[function_name].parameters
        if len(function_arg) != len(function_parameters):
            smart_error(f"Function '{function_name}' take {len(function_parameters)} parameters, but {len(function_arg)} was given.")

        for i, parameter in enumerate(function_parameters):
            if isinstance(parameter, smart_obj.SmartVariable):
                adress_parameter = parameter.ram_adress

                hex_code += set_on_A_value(function_arg[i])


                hex_code += f"8D {adress_for_RAM(adress_parameter)} "
                address_counter += 3

            elif isinstance(parameter, smart_obj.SmartStr):
                adress_parameter = parameter.ram_adress

                hex_code += set_on_ram_str(function_arg[i], adress_parameter)

            else:
                smart_error(f"Unknown type of parameters for function '{function_name}'.")

        return hex_code

    def increment_decrement_var(line:str, offset_mode:dict[str, bool | str]={"offset":False, "offset_value":""}) -> None:
        """Add to code_compile the hex code for increment or decrment a variable:
        .x++;
        .x--;
        """
        nonlocal code_compile, address_counter
        var_name = line[:-2]

        operator = line[-1]

        if not good_variable_name(var_name):
            smart_error(f"Syntaxe error: excepted a variable name, not '{var_name}'")

        adress_var_increment = get_variable(var_name).ram_adress

        if offset_mode["offset"]:
            try:
                adress_var_increment += int(offset_mode["offset_value"])
            except ValueError:
                print(offset_mode["offset_value"])
                smart_error(f"Not implemented yet: index need to be constent for increment.")

        increment_adress = adress_for_RAM(adress_var_increment)

        code_compile += f"AE {increment_adress} " # LDX adress
        address_counter += 3

        code_compile += "E8 " if operator == "+" else "CA " # increment or decrement X
        address_counter += 1

        code_compile += f"8E {increment_adress} "  # store X (save at variable adress)
        address_counter += 3


    # -----------

    ACUMULATOR_REGISTER = "AXY"

    # -----------

    on_loop = False

    if "while_mode" in function_mode:
        if function_mode["while_mode"]:
            on_loop = True


    last_if = False     # True if the last operation is if on Smart (for else).

    if not module_mode:
        smart_var:dict[str, smart_obj.SmartVariable] = {} if not function_mode["function_mode"] else function_mode["global_var"]
    else:
        smart_var = smart_var_module

    adress_var = compiller_data_run.START_ADRESS_VAR + len(smart_var)

    line_counter = 0

    adress_str = hex(CODE_ADRESSE)[2:].upper() + ": "

    code_compile:str = "0" * (6 - len(adress_str)) + adress_str if not function_mode["function_mode"] else ""

    go_to:dict[str, smart_obj.SmartGoto] = {} if not function_mode["if_mode"] else function_mode["global_goto"]

    if function_mode["function_mode"]:
        return_line = False     # becomes True when it is the return line (if a line comes after the return line, raise SmartError)

    function_name_usr: dict[str, smart_obj.SmartFunction] = function_mode["global_function"] if function_mode["function_mode"] else {}

    go_to_replace = [] if not function_mode["if_mode"] else function_mode["goto_replace"]
    function_replace = function_mode["global_function_replace"] if function_mode["function_mode"] else []

    address_counter = 0

    if function_mode["function_mode"]:
        code_line = function_mode["source_code"].split("\n")
        code_start = function_mode["source_code"]
    else:
        try:
            sma = open(file, "r", encoding="UTF-8")

            code_start = sma.read()

            sma.close()

            if first_call:
                if code_start.startswith("#!"):
                    logging.info("Shebang detected, skip first line.")

                    if "\n" not in code_start:
                        logging.warning("Shebang detected, but no new line found.")
                        code_start = ""
                    else:
                        code_start = code_start.split("\n", 1)[1]

            code_start = code_start.replace("\t", "        ")

            code_line = code_start.split("\n")
        except FileNotFoundError:
            raise CompileError(f"File not found: '{file}'")

    #control syntax warning:
    for i, line in enumerate(code_line):
        line_controle = line.replace(" ", "").replace("\t", "")

        if line_controle:
            line_controle = split_code(line_controle, "//")[0]

        if not(line_controle == "" or line_controle.endswith(";") or line_controle.endswith("}")):
            i += 1
            compiller_data_run.warning_endline = (True, i, module_name)

            logging.warning(f"Syntax warn: at line {i}, can't identify end. Maybe you have forget ';'?")
            break

    code = ""

    for line in code_line:
        line_tmp = line.split("//")[0].strip() + "\n"
        code += line_tmp

    code = split_code(code.replace("\n", ""), ";")

    logging.info("Building asm")

    jump_line = 0

    if code_start.replace(" ", "").replace("\n", "").replace("\t", "") == "":
        logging.warning("Smart file is empty!")

    on_try_bloc = False
    after_try_bloc = False

    for line in code:
        if jump_line:
            jump_line -= 1
            line_counter += 1
            continue

        if line == "" or line.replace(" ", "") == "":
            line_counter += 1
            logging.warning("Empty line detected.")
            continue

        if function_mode["function_mode"]:
            if return_line:
                smart_error("On function {}, value was return before the end of function.".format(function_mode["smart_func"].name))

        if not line.startswith("compiletime"):
            for define, value in compile_command.define.items():
                line = line.replace(define, value)

        line_debug = compile_command.get_line_debug(line)   # if the debug mode is enabled, print the line before running.
        if line_debug:
            code_compile += line_debug
            address_counter += line_debug.count(" ")

        if line[0] in ACUMULATOR_REGISTER:
            line = replace_code(line, " ", "")
            read_line = line.split("=", 1)


            r = read_line[0]

            if len(read_line) != 2:
                smart_error(f"Smart syntax error:\nline {line_counter}")

            if r == "A":
                value_accumulator = set_on_A_value(read_line[1])
            else:
                value_accumulator = set_on_A_value(read_line[1], forbiden_math=True)

            code_compile += value_accumulator if r == "A" else "A2" + value_accumulator[2:] if r == "X" else "A0" + value_accumulator[2:]

            logging.info("Build asm command: set on accumulator value")

        elif line[0] == "#":
            name = line[1:]

            if (" " in name or "\n" in name) or (name in ACUMULATOR_REGISTER):
                smart_error(f"Invalid name for goto : '{name}'")

            hex_adress = hex(CODE_ADRESSE + address_counter)[2:].upper()


            hex_adress = "0" * (4-len(hex_adress)) + hex_adress


            go_to[name] = smart_obj.SmartGoto(name, hex_adress)

            logging.info("Build asm command: goto")


        elif line.startswith("."):      # variable

            line = replace_code(line, " ", "")[1:]

            if line.endswith("++") or line.endswith("--"): # ------
                increment_decrement_var(line)


            else:

                try:
                    var_name, value = line.split("=", 1)
                except ValueError:
                    smart_error(f"Error with variable `{line}`: expected '='")

                if not good_variable_name(var_name):
                    smart_error(f"Bad variable name : '{var_name}'")

                if var_name not in smart_var: # make new variable

                    make_variable(smart_obj.SmartVariable(var_name, adress_var))

                value_RAM = set_on_A_value(value)

                code_compile += f"{value_RAM}8D {adress_for_RAM(get_variable(var_name).ram_adress)} "

                address_counter += 3

                logging.info(f"Build asm command: using RAM for variable '{var_name}'")

        elif line.startswith("~"):      # advanced variable
            line = replace_code(line, " ", "")[1:]

            if line.endswith("++") or line.endswith("--"):
                operator_increment = line[-2:]
                increment_mode = True
                var_name = line[:-2]
            else:
                increment_mode = False

                try:
                    var_name, value = line.split("=", 1)
                except ValueError:
                    smart_error(f"Error with variable `{line}`: expected '='")



            if var_name.endswith("]"):     # an index for str value

                var_name = var_name.split("[", 1)[0]

                index_mode = True
            else:
                index_mode = False

                if increment_mode:
                    smart_error(f"Invalid syntax: can't increment or decrement a str variable.")

            if not good_variable_name(var_name):
                smart_error(f"Bad variable name : '{var_name}'")

            if var_name not in smart_var: # make new variable
                if index_mode:
                    smart_error(f"Used index in undefined variable: `{var_name}`")

                make_variable(smart_obj.SmartStr(var_name, adress_var), add_adress_advenced_value=False)

                #compiller_data_run.not_used_ram += 1

                for i in range(smart_obj.SIZE_ADVANCED_OBJ - 1):
                    compiller_data_run.not_used_ram += 1
                    make_variable(smart_obj.ReservedAdress(adress_var), name=f"NotUsedRAM{i + compiller_data_run.not_used_ram}")

                compiller_data_run.not_used_ram += 1


            if not index_mode:  # set a str value on variable
                try:
                    code_compile += set_on_ram_str(value, get_variable(var_name).ram_adress)
                except SmartError as se:
                    smart_error(f"{str(se)}\t\tOn str variable (~), need str value, not `{value}`.")

            else:   # set a value at index:
                index_mode_const, index_var = get_variable(var_name).get_index(line)
                # ^ if the index is a number literal, otherwise it is a variable or expression

                if increment_mode:
                    increment_decrement_var(var_name + operator_increment, {"offset":True, "offset_value":index_var[:-2]})
                else:

                    if index_mode_const:
                        code_compile += f"{set_on_A_value(value)}8D {adress_for_RAM(get_variable(var_name).ram_adress + index_var)} "
                        address_counter += 3
                    else:
                        code_compile += f"{set_on_A_value(index_var)}AA "     # save on X index delta
                        address_counter += 1

                        # -------- control index for runtime error
                        test_index = "C9 15 "    # CMP #0x15
                        address_counter += 2

                        test_index += "90 !smart:len_error_index "     # branch if index > 21
                        address_counter += 2

                        error_code, _ = make_error("'I'", try_mode, add_to_adress_conter=False)
                        test_index = test_index.replace("!smart:len_error_index", get_hex_from_int(error_code.count(" ")))

                        test_index += error_code
                        address_counter += error_code.count(" ")

                        code_compile += test_index

                        # --------

                        code_compile += set_on_A_value(value)

                        code_compile += f"9D {adress_for_RAM(get_variable(var_name).ram_adress)} "
                        address_counter += 3


        elif line.lstrip().startswith("if"):
            line_2 = replace_code(line, " ", "")[2:]

            if not line_2.endswith("{"):
                smart_error("On if bloc, expected '{'")
            else:
                line_2 = line_2[:-1]

            code_compile += set_on_A_value(line_2)

            bloc_code, bloc_line = get_bloc(line_counter, code, error_message="On if bloc")

            jump_line = bloc_line - line_counter - 1

            compiller_data_run.not_used_call_else += 1
            make_variable(smart_obj.ReservedAdress(adress_var), name=f"NotUsedRAMCallElse{compiller_data_run.not_used_call_else}")


            call_else_adress = adress_for_RAM(get_variable(f"NotUsedRAMCallElse{compiller_data_run.not_used_call_else}", special_name=True).adress) + " "

            adress_var += 1

            code_compile += f"C9 00 D0 08 A9 01 8D {call_else_adress}4C {{}} A9 00 8D {call_else_adress}"
            address_counter += 17

            code_if = compile_smart(
                make_file=False,
                function_mode={"function_mode":True, "source_code":bloc_code, "global_function":function_name_usr, "global_function_replace":function_replace, "global_var":smart_var, "smart_func":None, "if_mode":True, "global_goto":go_to, "goto_replace":go_to_replace, "while_mode":function_mode["while_mode"] if "while_mode" in function_mode else False},
                CODE_ADRESSE=CODE_ADRESSE + address_counter,
                thread_mode=thread_mode
            )

            new_adress = code_if.count(" ") + code_if.count("!smart_call_func|") * 3 + code_if.count("!smart_tmp:goto|") * 3 - code_if.count("!smart_tmp:goto|")

            hex_adress_if = adress_for_RAM(CODE_ADRESSE + address_counter + new_adress)

            code_compile = code_compile.format(hex_adress_if)

            address_counter += new_adress
            code_compile += code_if

            last_if = True

            line_counter += 1    # increment the line counter because of 'continue'
            continue

        elif line.lstrip().startswith("elif"):

            if not last_if:
                smart_error("'elif bloc' was used but 'if bloc' was not created.")

            line_2 = replace_code(line, " ", "")[4:]

            if not line_2.endswith("{"):
                smart_error("On elif bloc, expected '{'")
            else:
                line_2 = line_2[:-1]


            bloc_code, bloc_line = get_bloc(line_counter, code, error_message="On elif bloc")

            jump_line = bloc_line - line_counter - 1

            code_compile += f"AD {call_else_adress}C9 01 D0 !smart_tmp:elif "
            address_counter += 7

            value_tmp = set_on_A_value(line_2)

            code_compile += value_tmp

            delta_branch = hex(value_tmp.count(" ") + value_tmp.count("!smart_call_func|") * 3 + 9)[2:].upper()

            code_compile = code_compile.replace("!smart_tmp:elif", delta_branch)

            code_compile += f"C9 00 D0 08 A9 01 8D {call_else_adress}4C {{}} A9 00 8D {call_else_adress}"

            address_counter += 17

            code_elif = compile_smart(
                make_file=False,
                function_mode={"function_mode":True, "source_code":bloc_code, "global_function":function_name_usr, "global_function_replace":function_replace, "global_var":smart_var, "smart_func":None, "if_mode":True, "global_goto":go_to, "goto_replace":go_to_replace, "while_mode":function_mode["while_mode"] if "while_mode" in function_mode else False},
                CODE_ADRESSE=CODE_ADRESSE + address_counter,
                thread_mode=thread_mode
            )

            new_adress = code_elif.count(" ") + code_elif.count("!smart_call_func|") * 3 + code_elif.count("!smart_tmp:goto|") * 3 - code_elif.count("!smart_tmp:goto|")

            hex_adress_elif = adress_for_RAM(CODE_ADRESSE + address_counter + new_adress)

            code_compile = code_compile.format(hex_adress_elif)

            address_counter += new_adress
            code_compile += code_elif

            last_if = True

            line_counter += 1    # increment the line counter because of 'continue'
            continue

        elif line.lstrip().startswith("else"):
            if not last_if:
                smart_error("'else bloc' was used but 'if bloc' was not created.")

            line_2 = replace_code(line, " ", "")[4:]

            if not line_2.endswith("{"):
                smart_error("On else bloc, expected '{'")

            bloc_code, bloc_line = get_bloc(line_counter, code, error_message="On else bloc")

            jump_line = bloc_line - line_counter - 1

            code_compile += f"AD {call_else_adress}C9 00 D0 03 4C {{}} "
            address_counter += 10

            code_else = compile_smart(
                make_file=False,
                function_mode={"function_mode":True, "source_code":bloc_code, "global_function":function_name_usr, "global_function_replace":function_replace, "global_var":smart_var, "smart_func":None, "if_mode":True, "global_goto":go_to, "goto_replace":go_to_replace, "while_mode":function_mode["while_mode"] if "while_mode" in function_mode else False},
                CODE_ADRESSE=CODE_ADRESSE + address_counter,
                thread_mode=thread_mode
            )

            new_adress = code_else.count(" ") + code_else.count("!smart_call_func|") * 3 + code_else.count("!smart_tmp:goto|") * 3 - code_else.count("!smart_tmp:goto|")

            hex_adress_else = adress_for_RAM(CODE_ADRESSE + address_counter + new_adress)

            code_compile = code_compile.format(hex_adress_else)

            address_counter += new_adress
            code_compile += code_else

        elif line.lstrip().startswith("try"):
            line = line.replace(" ", "")
            if not line.endswith("{"):
                smart_error("On try bloc, '{' expected.")

            bloc_code, bloc_line = get_bloc(line_counter, code, error_message="On try bloc")

            jump_line = bloc_line - line_counter - 1

            code_try = compile_smart(
                make_file=False,
                function_mode={"function_mode":True, "source_code":bloc_code, "global_function":function_name_usr, "global_function_replace":function_replace, "global_var":smart_var, "smart_func":None, "if_mode":True, "global_goto":go_to, "goto_replace":go_to_replace, "while_mode":function_mode["while_mode"] if "while_mode" in function_mode else False},
                CODE_ADRESSE=CODE_ADRESSE + address_counter,
                try_mode=True,
                thread_mode=thread_mode
            )

            new_adress = code_try.count(" ") + code_try.count("!smart_call_func|") * 3 + code_try.count("!smart_tmp:goto|") * 3 - code_try.count("!smart_tmp:goto|")

            address_counter += new_adress

            adress_except = adress_for_RAM(CODE_ADRESSE + address_counter + 3)  # + 3 because after try bloc JMP

            code_try = code_try.replace("!  smart_error_try ", f"4C {adress_except} ")

            code_try += f"4C ! smart_end_try "
            address_counter += 3

            code_compile += code_try

            on_try_bloc = True
            after_try_bloc = True

        elif line.lstrip().startswith("except"):
            line = line.replace(" ", "")
            if not line.endswith("{"):
                smart_error("On except bloc, '{' expected.")

            if not on_try_bloc:
                smart_error("'except bloc' was used but 'try bloc' was not created.")

            on_try_bloc = False

            bloc_code, bloc_line = get_bloc(line_counter, code, error_message="On except bloc")

            jump_line = bloc_line - line_counter - 1

            code_except = compile_smart(
                make_file=False,
                function_mode={"function_mode":True, "source_code":bloc_code, "global_function":function_name_usr, "global_function_replace":function_replace, "global_var":smart_var, "smart_func":None, "if_mode":True, "global_goto":go_to, "goto_replace":go_to_replace, "while_mode":function_mode["while_mode"] if "while_mode" in function_mode else False},
                CODE_ADRESSE=CODE_ADRESSE + address_counter,
                thread_mode=thread_mode
            )

            new_adress = code_except.count(" ") + code_except.count("!smart_call_func|") * 3 + code_except.count("!smart_tmp:goto|") * 3 - code_except.count("!smart_tmp:goto|")

            address_counter += new_adress
            code_compile += code_except
            code_compile = code_compile.replace("! smart_end_try ", adress_for_RAM(CODE_ADRESSE + address_counter) + " ")

        elif line.lstrip().startswith("thread"):

            line = line.strip()
            line = line.replace(" ", "")
            line = line[len("thread"):]

            if not line.endswith("{"):
                smart_error("On thread bloc, '{' expected.")

            line = line[:-1]

            shared_stack_mode = False  # if True, both threads can call functions but the synchronization between them is not active
            match line.replace(" ", ""):
                case "stack":
                    shared_stack_mode = True

                case "nostack":
                    shared_stack_mode = False

                case _:
                    smart_error(f"Unknown thread mode '{line.replace(" ", "")}' on thread.")

            if thread_mode[0]:
                smart_error("Thread error: you can't have more 2 threads.")

            bloc_code, bloc_line = get_bloc(line_counter, code, error_message="On thread bloc")

            jump_line = bloc_line - line_counter - 1

            code_thread = compile_smart(
                make_file=False,
                function_mode={"function_mode":True, "source_code":bloc_code, "global_function":function_name_usr, "global_function_replace":function_replace, "global_var":smart_var, "smart_func":None, "if_mode":True, "global_goto":go_to, "goto_replace":go_to_replace, "while_mode":function_mode["while_mode"] if "while_mode" in function_mode else False},
                CODE_ADRESSE=CODE_ADRESSE + address_counter + 10,
                thread_mode=[True, "second", True, shared_stack_mode]
            )

            # on the main ptr, set a first address
            code_compile += f"A9 !smart_adress_main_thread_1 8D {compiller_data_run.SYS_ADRESS['main_thread_ptr_1']} "  # first byte
            code_compile += f"A9 !smart_adress_main_thread_2 8D {compiller_data_run.SYS_ADRESS['main_thread_ptr_2']} "  # second byte
            address_counter += 10

            new_adress = code_thread.count(" ") + code_thread.count("!smart_call_func|") * 3 + code_thread.count("!smart_tmp:goto|") * 3 - code_thread.count("!smart_tmp:goto|")

            address_counter += new_adress
            code_compile += code_thread

            thread_mode[0] = True
            thread_mode[1] = "main"
            thread_mode[2] = False

            main_adress_1, main_adress_2 = adress_for_RAM(CODE_ADRESSE + address_counter).split(" ")
            code_compile = code_compile.replace("!smart_adress_main_thread_1", main_adress_1)
            code_compile = code_compile.replace("!smart_adress_main_thread_2", main_adress_2)



        elif line.lstrip().startswith("while"):
            line_2 = replace_code(line, " ", "")[5:]

            if not line_2.endswith("{"):
                smart_error("On while bloc, expected '{'")
            else:
                line_2 = line_2[:-1]

            while_adress = adress_for_RAM(CODE_ADRESSE + address_counter) + " "

            code_compile += set_on_A_value(line_2)

            bloc_code, bloc_line = get_bloc(line_counter, code, error_message="On while bloc")

            jump_line = bloc_line - line_counter - 1

            code_compile += "C9 00 D0 03 4C {} "
            address_counter += 7

            code_while = compile_smart(
                make_file=False,
                function_mode={"function_mode":True, "source_code":bloc_code, "global_function":function_name_usr, "global_function_replace":function_replace, "global_var":smart_var, "smart_func":None, "if_mode":True, "global_goto":go_to, "goto_replace":go_to_replace, "while_mode":True},
                CODE_ADRESSE=CODE_ADRESSE + address_counter,
                thread_mode=thread_mode
            )

            new_adress = code_while.count(" ") + code_while.count("!smart_call_func|") * 3 + code_while.count("!smart_tmp:goto|") * 3 - code_while.count("!smart_tmp:goto|")

            address_counter += new_adress
            code_compile += code_while

            code_compile += "4C " + while_adress
            address_counter += 3

            end_adress = adress_for_RAM(CODE_ADRESSE + address_counter)

            code_compile = code_compile.format(end_adress).replace("! smart:break", end_adress)
            code_compile = code_compile.replace("! smart:continue ", while_adress)

        elif line.lstrip().startswith("for "):  # loop
            line_2 = replace_code(line, " ", "")[3:]

            if not line_2.endswith("{"):
                smart_error("On for bloc, expected '{'")
            else:
                line_2 = line_2[:-1]

            var_name, count = line_2.split("in", 1)
            var_name = var_name.strip()

            if var_name == "_":     # if the for loop variable is not used
                no_var_for = True
                adress_iterrator = None

            else:
                no_var_for = False

                if not good_variable_name(var_name[1:]):
                    smart_error(f"Invalid name for variable: '{var_name}'")

                if len(smart_var) >= 256: # to replace
                    smart_error("Memory error : maximum variable are 256.")

                var_name = var_name[1:]

                adress_iterrator = adress_for_RAM(adress_var)
                make_variable(smart_obj.SmartVariable(var_name, adress_var))

            count = count.strip()

            if count.startswith("|"):   # a number count
                start_number, end, step = count[1:-1].split("|")

                start_loop_for = get_start_end(start_number, end, step, no_var_for, adress_iterrator)

            else:
                count = count.replace(" ", "")

                if count.startswith("[") or count.startswith('"'):
                    smart_error("On for loop, need variable name, not immediate value. Please set your value in variable before the for loop...")

                if not count.startswith("~"):   # advanced variable
                    smart_error("On for loop, need an advanced variable.")

                if no_var_for:
                    smart_error("On for loop, need a variable for iteration of advanced value.")

                try:
                    adress_advenced_value = get_variable(count[1:]).ram_adress
                except KeyError:
                    smart_error(f"Variable {count[1:]} was not found on for loop.")

                start_loop_for = get_start_end("0", "21", "1", True, adress_iterrator, advenced_value_mode=True)


                # set the simple value on the variable
                code_compile += f"BD {adress_for_RAM(adress_advenced_value)} "      # set on A the value with offset
                address_counter += 3

                code_compile += f"8D {adress_iterrator} "  # set on the iterator the simple value
                address_counter += 3

            # code on loop

            bloc_code_for, bloc_line = get_bloc(line_counter, code, error_message="On for bloc")

            jump_line = bloc_line - line_counter - 1

            code_for = compile_smart(
                make_file=False,
                function_mode={"function_mode":True, "source_code":bloc_code_for, "global_function":function_name_usr, "global_function_replace":function_replace, "global_var":smart_var, "smart_func":None, "if_mode":True, "global_goto":go_to, "goto_replace":go_to_replace, "while_mode":True},
                CODE_ADRESSE=CODE_ADRESSE + address_counter,
                thread_mode=thread_mode
            )

            new_adress = code_for.count(" ") + code_for.count("!smart_call_func|") * 3 + code_for.count("!smart_tmp:goto|") * 3 - code_for.count("!smart_tmp:goto|")

            address_counter += new_adress
            code_compile += code_for

            code_compile += f"4C {start_loop_for} "
            address_counter += 3

            code_compile = code_compile.replace("! smart:break", adress_for_RAM(CODE_ADRESSE + address_counter))
            code_compile = code_compile.replace("! smart:continue ", start_loop_for + " ")

        elif line.lstrip().startswith("break"):
            if not on_loop:
                smart_error("Error: 'break' keyword can only be used inside a loop.")

            code_compile += "4C ! smart:break "     # set space on placeholder for counting address
            address_counter += 3

        elif line.lstrip().startswith("continue"):
            if not on_loop:
                smart_error("Error: 'continue' keyword can only be used inside a loop.")

            code_compile += "4C ! smart:continue "     # set space on placeholder for counting address
            address_counter += 3

        elif line.lstrip().startswith("error "):        # runtime error
            try:
                error_value = line.split(" ", 1)[1]

            except IndexError:
                smart_error(f"Expected value after `error`: '{line}'")

            hex_code_error, len_code_error = make_error(error_value, try_mode)

            code_compile += hex_code_error
            address_counter += len_code_error

        elif line.lstrip().startswith("void"):      # make function
            if function_mode["function_mode"]:
                smart_error(f"Error with function: impossible to create new function on function.")

            func_name = line.split(" ", 1)[1]

            if func_name[-1] != "{":
                smart_error("On function " + func_name + ", expected '{'")

            func_name = func_name[:-1]

            parameters_obj = []

            if ":" in func_name:    # the function has parameters
                func_name, parameters = func_name.split(":", 1)

                parameters_list = parameters.replace(" ", "").split(",")

                for parameter in parameters_list:
                    if parameter.startswith("*"): # set a ptr
                        parameter = parameter[1:]
                        ptr_mode = True
                    else:
                        ptr_mode = False

                    if parameter.startswith("."):
                        var_name_parameter = parameter[1:]
                        if not good_variable_name(var_name_parameter):
                            smart_error(f"Invalid syntax, expected a variable name: '{var_name_parameter}'.")

                        parameter_obj = smart_obj.SmartVariable(var_name_parameter, adress_var, ptr_function=ptr_mode)

                        make_variable(parameter_obj)
                        parameters_obj.append(parameter_obj)

                    elif parameter.startswith("~"):
                        var_name_parameter = parameter[1:]
                        if not good_variable_name(var_name_parameter):
                            smart_error(f"Invalid syntax, expected a variable name: '{var_name_parameter}'.")

                        parameter_obj = smart_obj.SmartStr(var_name_parameter, adress_var, ptr_function=ptr_mode)

                        make_variable(parameter_obj, add_adress_advenced_value=False)
                        parameters_obj.append(parameter_obj)

                        #compiller_data_run.not_used_ram += 1

                        for i in range(smart_obj.SIZE_ADVANCED_OBJ - 1):
                            compiller_data_run.not_used_ram += 1
                            make_variable(smart_obj.ReservedAdress(adress_var), name=f"NotUsedRAM{i + compiller_data_run.not_used_ram}")

                        #compiller_data_run.not_used_ram += 1

                    else:
                        smart_error(f"Expected a variable name, not '{parameter}'")

            if not good_variable_name(func_name):
                smart_error(f"Invalid name for {func_name}")

            logging.debug(f"Building function '{func_name}'")

            func_code, funciton_line = get_bloc(line_counter, code, error_message="On function '" + func_name + "'")

            function_name_usr[func_name] = smart_obj.SmartFunction(func_name, func_code, parameters_obj)

            jump_line = funciton_line - line_counter - 1

            logging.debug(f"'{func_name}' has been created.")

        elif line.lstrip().startswith("return "):        # return value

            if not(function_mode["function_mode"]) or function_mode["if_mode"]:
                smart_error("Smart syntax error: 'return' key word can't be used outside function.")

            try:
                value_return = replace_code(line.strip().split(" ", 1)[1], " ", "")
            except:
                smart_error(f"Smart syntax error: '{line}'")

            # return value

            code_compile += set_on_A_value(value_return)

            function_mode["smart_func"].return_value = True

            return_line = True

        elif line.lstrip().startswith("import "):
            if function_mode["function_mode"]:
                if function_mode["if_mode"]:
                    smart_error("Can't import a module on a bloc.")
                else:
                    smart_error("Can't import a module on function.")


            line_import = split_code(line, " ")[1:]

            try:

                if len(line_import) == 1:   # search in all directories
                    if not(line_import[0].startswith('"') and line_import[0].endswith('"')):
                        smart_error("Need a str value for path, in import.")
                    name_import = line_import[0][1:-1]
                    import_info = import_tool.import_all(name_import, CODE_ADRESSE + address_counter, module_var=smart_var)


                elif len(line_import) == 3: # search in a specific directory (smart, lib or path of code)
                    line_from = split_code("".join(line_import), "from")

                    if len(line_from) != 2:
                        smart_error("Syntax error: expected 'from'.")

                    name_import, type_import = line_from

                    if not(name_import.startswith('"') and name_import.endswith('"')):
                        smart_error("Need a str value for path, in import.")
                    else:
                        name_import = name_import[1:-1]


                        if type_import == '"file"':
                            import_info = import_tool.import_module(name_import, CODE_ADRESSE + address_counter, module_var=smart_var)

                        elif type_import == '"lib"':
                            import_info = import_tool.import_lib(name_import, CODE_ADRESSE + address_counter, module_var=smart_var)

                        elif type_import == '"smart"':
                            import_info = import_tool.import_smart(name_import, CODE_ADRESSE + address_counter, module_var=smart_var)

                        else:
                            smart_error('Unknow import type. Must be "file", "lib", "smart"')

            except SmartError as se:
                smart_error("Error on module '{}':\n\t{}".format(name_import, (str(se)[1:-1].replace(",", "\n\t"))))
            except import_tool.ModuleError as me:
                if me.recursion:
                    raise CompileError(f"Compile fail: error with module, maybe a module import self... (error in {me.module_name})")
                else:
                    smart_error("Error during importing module:\n" + str(me))

            adress_delta = import_info.binary.count(" ")

            code_compile += import_info.binary
            address_counter += adress_delta

            function_name_usr |= import_info.function

            for var_name in import_info.variables:
                smart_var[var_name] = import_info.variables[var_name]

            adress_var = len(import_info.variables) + compiller_data_run.START_ADRESS_VAR

            address_counter += 2

            new_adress_module = adress_for_RAM(CODE_ADRESSE + address_counter) + " "

            code_compile = code_compile.replace("!smart_module_goto", new_adress_module)

        elif line.lstrip().startswith("compiletime "):  # a compile command
            compile_command.compiletime_command(line, smart_var, thread_mode)

        elif re.match(FUNCTION_PATTERN, line):     # function

            line = replace_code(line, " ", "")

            function_name, function_arg = line.split(":", 1)

            function_arg = split_code(function_arg, ",")

            if not good_variable_name(function_name):
                smart_error(f"Syntax error: '{function_name}'")

            if function_name == "print":
                if len(function_arg) != 1:
                    smart_error("print function take 1 arg")

                if function_arg[0] in ACUMULATOR_REGISTER:
                    if function_arg[0] != "A":
                        smart_error(f"print need 'A' register, not '{function_arg[0]}'")

                    code_compile += "20 EF FF "

                    address_counter += 3


                elif function_arg[0][0] == "\"":
                    smart_str = function_arg[0]


                    value_str = get_str(smart_str, line_counter)

                    for char in get_char_from_str(value_str):
                        code_compile += set_on_A_value(f"'{char}'") + "20 EF FF "

                        address_counter += 3

                elif is_a_simple_value(function_arg[0]):
                    code_compile += set_on_A_value(function_arg[0])
                    code_compile += "20 EF FF "
                    address_counter += 3

                elif not is_a_simple_value(function_arg[0]):    # the value is str

                    string_adress = get_int_adress_from_str(compiller_data_run.SYS_ADRESS["SaveStr"])

                    set_ram_str = set_on_ram_str(function_arg[0], string_adress)

                    code_compile += set_ram_str

                    for deltal in range(string_adress, string_adress + smart_obj.SIZE_ADVANCED_OBJ):
                        code_compile += f"AD {adress_for_RAM(deltal)} 20 EF FF "


                    address_counter += 6 * smart_obj.SIZE_ADVANCED_OBJ

                logging.info("Build smart function as asm command: print")


            elif function_name == "quit":
                if len(function_arg) != 0:
                    smart_error("Function 'quit' not take arg.")

                code_compile += "00 "
                address_counter += 1

                logging.info("Build smart function as asm command: quit")

            elif function_name == "restart":
                if len(function_arg) != 0:
                    smart_error("Function 'restart' not take arg.")

                code_compile += f"4C {adress_for_RAM(CODE_ADRESSE)} "
                address_counter += 3

                logging.info("Build smart function as asm command: restart")

            elif function_name == "goto":
                if len(function_arg) != 1:
                    smart_error("Function 'goto' take 1 arg.")

                name = function_arg[0]

                goto_tmp = f"!smart_tmp:goto|{name}"

                go_to_replace.append(goto_tmp)

                code_compile += "4C " + goto_tmp

                address_counter += 3

                logging.info("Build smart function as asm command: goto")

            elif function_name == "asm_entry":

                code_tmp = build_asm_entry(function_arg, line_counter, get_str, address_counter, smart_var, CODE_ADRESSE)

                code_compile += code_tmp

                address_counter += code_tmp.count(" ")

            elif function_name in SmartBuiltIn.BUILT_IN_NAME_RETURN:
                logging.warning(f"'{function_name}' function is a return-function, but was used as a function.")

                match function_name:
                    case "input":
                        hex_code_input, adress_delta = SmartBuiltIn.smartInput()

                        code_compile += hex_code_input

                        address_counter += adress_delta

            elif function_name == "wozm":   # return to woz monitor
                if len(function_arg) != 0:
                    smart_error("Function 'wozm' not take arg.")

                code_compile += "4C 1F FF " # the address of woz monitor get line
                address_counter += 3

                logging.info("Build smart function with use Woz monitor: wozm")

            elif function_name in function_name_usr:

                if thread_mode[0] and thread_mode[1] != "main" and not(thread_mode[3]):
                    smart_error("Can't call a function on second thread: the shared stack mode is not enabled.")

                if function_name_usr[function_name].return_value:
                    logging.warning(f"Function '{function_name}' is a return-function but was used as a function.")

                # set the parameters:
                code_compile += hex_parameters(function_name_usr, function_name, function_arg)
                # use a goto

                address_counter += 3

                text_code = f"!smart_call_func|{function_name}"

                function_replace.append(text_code)

                code_compile += text_code

                hex_code_ptr, delta_adress_ptr = code_ptr_func(function_name, function_arg)

                code_compile += hex_code_ptr
                address_counter += delta_adress_ptr



            else:
                smart_error(f"Function '{function_name}' not exist.")

        else:
            smart_error("Smart invalid syntax")

        line_counter += 1

        last_if = False

        after_try_bloc = control_except(after_try_bloc, on_try_bloc, line_counter)

        # --- thread ---

        if thread_mode[0]:
            if thread_mode[2]:
                # save the address of next operation
                next_operation_adress_1, next_operation_adress_2 = adress_for_RAM(CODE_ADRESSE + address_counter + 13).split(" ")
                code_compile += f"A9 {next_operation_adress_1} 8D {compiller_data_run.SYS_ADRESS['main_thread_ptr_1' if thread_mode[1] == 'main' else 'second_thread_ptr_1']} " # first byte of address
                code_compile += f"A9 {next_operation_adress_2} 8D {compiller_data_run.SYS_ADRESS['main_thread_ptr_2' if thread_mode[1] == 'main' else 'second_thread_ptr_2']} " # second byte of address

                address_counter += 10

                # go to the other thread
                code_compile += f"6C {compiller_data_run.SYS_ADRESS['main_thread_ptr_1' if not thread_mode[1] == 'main' else 'second_thread_ptr_1']} "
                address_counter += 3

            else:
                thread_mode[2] = True

        if not(compiller_data_run.double_space_error) and not verryfing_adress_conter_no_print(address_counter, code_compile):

            compiller_data_run.double_space_error = True

            if verryfing_adress_conter_no_print(address_counter, code_compile) is None:
                logging.error(f"{color_tool.Colors.RED}Error: double space on code_compile.\n\tYou can report to `{GIT_HUB_LINK}`.{color_tool.Colors.RESET}")

            else:
                logging.error(f"""Address counter (offset from the start of program) is not good
    If the programme fail, please report this error to the developer.
    {color_tool.Colors.BG_YELLOW}Fail detail:{color_tool.Colors.RESET}
    \tNormal adress: {hex(get_adress(code_compile)).upper()} + {hex(CODE_ADRESSE).upper()}
    \tError adress: {hex(address_counter).upper()} + {hex(CODE_ADRESSE).upper()}

    \t{color_tool.Colors.GREEN}You can report to `{GIT_HUB_LINK}`.{color_tool.Colors.RESET}
    """)


            if input("Continue ? (y/N): ").lower() != "y":
                raise CompileError("User quit: error with adress counter.")


        # progress bar
        advencement = int(line_counter / len(code) * PROGRESS_BAR_LEN)
        print(f"[{PROGRESS_BAR_CHAR['completed'] * advencement}{PROGRESS_BAR_CHAR['not_completed'] * (PROGRESS_BAR_LEN - advencement)}]", end="\r")

    # ------------------------------- End compile loop ----------------------------------------------

    control_except(after_try_bloc, on_try_bloc, line_counter)

    if function_mode["if_mode"]:
        pass

    elif module_mode:
        code_compile += "4C !smart_module_goto"

    elif function_mode["function_mode"]:
        code_compile += "60 "

    else:
        code_compile += "00 "



    # compile function:

    if not function_mode["function_mode"]:
        for function in function_name_usr:

            code = function_name_usr[function].source_code_function

            smart_func = function_name_usr[function]

            function_thread_mode = thread_mode if thread_mode[3] else [False, "", False, False]

            function_name_usr[function].code_compile_f = compile_smart(
                make_file=False,
                function_mode={"function_mode":True, "source_code":code, "global_function":function_name_usr, "global_function_replace":function_replace, "global_var":smart_var, "smart_func":smart_func, "if_mode":False},
                CODE_ADRESSE=CODE_ADRESSE + address_counter + 1,
                thread_mode=function_thread_mode
            )

        # set the function:

        for f in function_name_usr:

            function_name_usr[f].function_adress = address_counter

            code_func = function_name_usr[f].code_compile_f

            code_compile += code_func

            address_counter += code_func.count(" ") + 3 * code_func.count("!smart_call_func|")

        # call function
        for i in range(2):
            for function in function_replace:

                function_name_tmp = function.split("|")[1]

                adress_func = CODE_ADRESSE + function_name_usr[function_name_tmp].function_adress + 1

                hex_adress_function = adress_for_RAM(adress_func)

                code_compile = code_compile.replace(function, f"20 {hex_adress_function} ")

                function_name_usr[function_name_tmp].called_function = True


    if (not function_mode["function_mode"]) and (not module_mode):
        for name, f in function_name_usr.items():
            if not f.called_function:
                logging.warning(f"Function '{name}' was never called.")

    if need_input and not function_mode["function_mode"]:
        input_adress = address_counter + CODE_ADRESSE + 1

        hex_input_adress = hex(input_adress)[2:].upper()
        hex_input_adress = "0" * (4 - len(hex_input_adress)) + hex_input_adress

        code_compile += SmartBuiltIn.input_code
        address_counter += SmartBuiltIn.input_code.count(" ")

        code_compile = code_compile.replace("!  smart_input", f"{hex_input_adress[2:]} {hex_input_adress[:2]} ")

    # set the goto:

    if not function_mode["if_mode"]:
        for goto in go_to_replace:
            goto_name = goto.split("|")[1]

            try:
                adress = go_to[goto_name].adress

            except KeyError:
                smart_error(f"'{name}' is not defined for goto !")

            code_compile = code_compile.replace(goto, f"{adress[2:]} {adress[:2]} ")

    if compiller_data_run.need_error and not(function_mode["function_mode"]) and not(function_mode["if_mode"]):

        code_compile = code_compile.replace("!  smart_runtime_error", adress_for_RAM(code_compile.count(" ") + CODE_ADRESSE - 1) + " ") # use count instead of address_counter to avoid errors
        code_compile += "20 EF FF 00 "

        address_counter += 4

    if not function_mode["function_mode"]:

        if "!" in code_compile and not module_mode and not function_mode["if_mode"]:
            confirm_user("Error: a placeholder was not used, the compilation failed. Do you want to print the code with placeholder for debug?", error_message="Placeholder error!")

        if bin_outpout_file:
            code_bin = "".join(chr(int(byte, base=16)) for byte in code_compile.split(" ")[1:-1])   # code_bin can have errors with UTF-8, used for print only

            hex_bytes = [b for b in code_compile.split(" ")[1:-1] if b]     # used for file
            data = bytes(int(b, 16) for b in hex_bytes)

        else:
            if regroup_bytes == -1:
                code_bin = code_compile

            else:

                start = int(code_compile.split(":")[0], base=16)

                hex_opcode = code_compile.split(": ")[1]

                hex_opcode = hex_opcode[:-1]        # to remove space at end

                code_bytes = hex_opcode.split(" ")

                lines = [code_bytes[i:i+regroup_bytes] for i in range(0, len(code_bytes), regroup_bytes)]

                if len(lines[-1]) != regroup_bytes:
                    lines[-1] += ["00"] * (regroup_bytes - len(lines[-1]))

                lines_str = [f"{hex(start + i * regroup_bytes)[2:].upper().zfill(4)}: {' '.join(line)}" for i, line in enumerate(lines)]


                code_bin = " \n".join(lines_str)


        logging.info("Build completed!")

        if make_file:
            print(f"\n\n{code_bin}\n\n")

            if bin_outpout_file:
                Path(os.path.splitext(argv[1])[0] + ".bin").write_bytes(data)
                logging.info(f"bin file saved as {os.path.splitext(argv[1])[0]}.bin")

            else:
                Path(os.path.splitext(argv[1])[0] + ".hex").write_text(code_bin, encoding="UTF-8")

                logging.info(f"hex file saved as {os.path.splitext(argv[1])[0]}.hex")

        logging.info("Build end.")

        logging.info(f"Memory info: Smart memory: 256 bytes, used by programme: {len(smart_var)} bytes, using {len(smart_var) / 256 * 100}% of Smart memory. Programme size: used {address_counter} bytes from {hex(CODE_ADRESSE)}") # replace len by a real counter

    if module_mode:
        return import_tool.ModuleInfo(code_compile, smart_var, function_name_usr, adress_var)

    else:

        return code_compile