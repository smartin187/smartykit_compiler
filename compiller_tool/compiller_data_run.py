# -*- coding: utf-8 -*-

"""
Has data during the compilation.
Has constants for the address.

Has:
- warning_endline: tuple to know if there is a warning if a line does not end with ';'.
- the number of addresses reserved for str values.
"""

from compiller_tool import color_tool

# constent -------------------------------

SYS_ADRESS = {
    "main_thread_ptr_1": "00 00", # the pointer of main thread operation (used only in threading mode).
    "main_thread_ptr_2": "01 00", # the second byte of ptr
    "MathOP":"02 00 ",
    "SaveStr":"03 00 ",     # SaveStr starts at EB 00 and has a length of 21 (end at 0x19 00)
    "SaveStrCMP":"18 00 ",  # SaveStrCMP starts at 0x19 00 and has a length of 21 (end at 0x32 00) - Used to save a str for compare (if, ==...)
    "SaveAToIndex":"31 00 ",   # SaveAToIndex starts at 0x32 00
    "second_thread_ptr_1": "47 00", # the pointer of second thread operation (used only in thread mode).
    "second_thread_ptr_2": "48 00" # the second byte of ptr
}

SMART_ERRORS = {     # the error codes for Smart
    "Index out of range": "I",
    "Division by zero": "/"
}

# placeholder with double space
SMART_PLACEHOLDER = (
    "!  smart_input",
    "!  smart_runtime_error",
    "!  smart_error_try"
)

BASE_ALLOW_CHAR = "!\"#$%'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_ "   # the allowed chars without \n and \r

ALLOW_CHAR = BASE_ALLOW_CHAR + "\n\r"

MAX_VARIABLE_CREATED = 256  # the maximum number of bytes for variables.

START_ADRESS_VAR = 0x300

OPERATOR = ("+", "-", "*", "/", "==", "!=", ">", "<", "<=", ">=")

PROGRESS_BAR_LEN = 25   # the length of the progress bar during compilation. Do not set a large value
PROGRESS_BAR_CHAR = {
    "completed":f"{color_tool.Colors.BG_GREEN} {color_tool.Colors.RESET}",
    "not_completed":" "
}

class EscapeChar:
    """The escape characters for str and char values."""
    ESCAPE_CHAR = {"\\r":"\r", "\\\"":"\"", "\\'":"'"}        # the escape characters for str and char (\r...)
    DOUBLE_SLASH = "\\\\"
    PLACE_HOLDER_SLASH = "`smart_double_slash"                  # set ` because this character is not used in str / char value.


# base value -------------------------------

_WARNING_ENDLINE = (False, )     # if a line does not end by ; } or // in the line or the last line
# format: [0]: warning end line ; [1] : line of error ; [2]: module of error ('*' if main module)

_NOT_USED_RAM = 0    # the number of unused RAM bytes for str values

_NEED_ERROR = False   # if a runtime error is needed

_DOUBLE_SPACE_ERROR = False # if a double space in the code is detected.

_NOT_USED_CALL_ELSE = 0

_DEBUG_MAX = False  # if debug is True, the running line is printed in the binary.

_NOT_USED_FOR = 0

# -------------------------------

_define_dict = None

def reset_define(define_dict:dict) -> None:
    """Add the define_dict to reset_data"""
    global _define_dict
    _define_dict = define_dict

def reset_data() -> None:
    """Reset the data.
    Used for test.py (because tests are run one after the other)."""
    global warning_endline, not_used_ram, need_error, double_space_error, not_used_call_else, debug_max, not_used_for
    warning_endline = _WARNING_ENDLINE
    not_used_ram = _NOT_USED_RAM
    need_error = _NEED_ERROR
    double_space_error = _DOUBLE_SPACE_ERROR
    not_used_call_else = _NOT_USED_CALL_ELSE
    debug_max = _DEBUG_MAX
    not_used_for = _NOT_USED_FOR

    # reset value of compiletime keyword
    _define_dict.clear()

# variable -------------------------------

warning_endline = _WARNING_ENDLINE

not_used_call_else = _NOT_USED_CALL_ELSE

not_used_ram = _NOT_USED_RAM

not_used_for = _NOT_USED_FOR

need_error = _NEED_ERROR

double_space_error = _DOUBLE_SPACE_ERROR

debug_max = _DEBUG_MAX
