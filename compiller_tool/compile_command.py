# -*- coding: utf-8 -*-

"""
This module is for the compiletime keyword
"""
import logging
from compiller_tool.smart_exception import SmartError

from compiller_tool.compiller_data_run import reset_define
from compiller_tool import compiller_data_run
from compiller_tool.string_tool import good_variable_name, get_str
from compiller_tool.color_tool import Colors
from compiller_tool.smart_info import SMART_VERSION

define = {}     # the define are stored in this dict

reset_define(define)

def get_line_debug(line:str) -> str:
    """Return the line for the debug if debug mode is enabled. Return '' if debug mode is disabled."""
    if compiller_data_run.debug_max:

        line_debug = []

        line = line.upper().strip()

        for char in line:
            if char in compiller_data_run.BASE_ALLOW_CHAR:
                line_debug.append(char)
            else:
                line_debug.append("?")

        # make hex program:
        hex_programm = []
        for char in line_debug:
            hex_programm.append(f"A9 {hex(ord(char))[2:].upper()} 20 EF FF ")

        hex_programm.append(f"A9 0D 20 EF FF ") # set a \r at the end

        return "".join(hex_programm)

    return ""

def compiletime_command(line:str, smart_var:dict, thread_mode:list[bool, str, bool, bool]) -> None:
    """This function is used to process the compiletime command."""

    line = line[len("compiletime "):].strip()

    if line.startswith("define "):   # define a code to replace
        new_define = line[len("define "):].strip()

        if new_define.count(" to ") != 1:
            raise SmartError("Invalid compiletime command: expected a name and a value after 'define' keyword.")

        name, value = new_define.split(" to ")

        name = name.strip()
        value = value.strip()

        if name in define:
            logging.warning(f"Redefining compiletime define '{name}' from '{define[name]}' to '{value}'.")

        define[name] = value

    elif line.startswith("debug "):  # set the debug mode
        debug_value = line[len("debug "):].strip()

        if debug_value in ("True", "1"):
            compiller_data_run.debug_max = True
            logging.info("Debug mode is enabled; All lines will be printed during execution.")
        elif debug_value in ("False", "0"):
            compiller_data_run.debug_max = False
            logging.info("Debug mode is disabled.")
        else:
            raise SmartError("Invalid compiletime command: expected 'True' or 'False' or 1 or 0 after 'debug' keyword.")

    elif line.startswith("realloc "):  # realloc a variable (= rename a variable)
        realloc_value = line[len("realloc "):].strip()

        try:
            old_var, new_var = realloc_value.split(" to ")
        except:
            raise SmartError("Invalid syntax after 'realloc': expected oldvar to newvar.")

        prefix_old = old_var.strip()[0]
        prefix_new = new_var.strip()[0]

        if prefix_old != prefix_new:
            raise SmartError(f"Invalid variable type for realloc: '{old_var}' and '{new_var}' have different types (simple and advanced).")

        try:
            base_name_old = old_var.replace(" ", "")[1:]
            base_name_new = new_var.replace(" ", "")[1:]
        except:
            raise SmartError("Invalid syntax for name of variable in realloc.")

        if len(base_name_old) == 0 or len(base_name_new) == 0:
            raise SmartError("Invalid syntax for name of variable in realloc: empty variable name.")

        if not good_variable_name(base_name_old):
            raise SmartError(f"Invalid syntax '{base_name_old}' for realloc (expected variable name).")
        elif not good_variable_name(base_name_new):
            raise SmartError(f"Invalid syntax '{base_name_new}' for realloc (expected variable name).")

        if base_name_old not in smart_var:
            raise SmartError(f"Variable '{base_name_old}' not found for realloc.")

        if base_name_new == base_name_old:
            raise SmartError(f"Variable '{base_name_new}' is the same as '{base_name_old}', you can't set a realloc.")

        var_object = smart_var[base_name_old]

        var_object.name = base_name_new

        smart_var[base_name_new] = var_object
        del smart_var[base_name_old]

    elif line.startswith("log "):  # set a log on the compiller log
        log_str = line[len("log "):].strip()

        logging.info(f"{Colors.BOLD}[Compiletime info]{Colors.RESET}: {get_str(log_str)}")

    elif line.replace(" ", "") == "killthread":  # stop second thread
        if not thread_mode[0]:
            raise SmartError("Erorr: 'killthread' was used but no thread are active.")

        logging.warning("A thread was stopped by the 'killthread' compiletime command. Use this command with carfull.")
        thread_mode[0] = False

    elif line.startswith("checkversion "): # control the minimum version for compile
        base_version = line[len("checkversion "):].replace(" ", "")
        try:
            major, minor, patch = map(int, base_version.split("."))
        except:
            raise SmartError(f"Invalid syntax after 'checkversion': expected x.y.z, not '{base_version}'.")

        smart_major, smart_minor, smart_patch = map(int, SMART_VERSION[1:].split("."))

        if (smart_major, smart_minor, smart_patch) < (major, minor, patch):
            logging.error(f"Error: Smart version required is {major}.{minor}.{patch}, but current version is {SMART_VERSION}. Please update Smart. You can continue compilation, but risk of error.")
            if input("Continue ? (y/N): ").replace(" ", "").lower() != "y":
                raise SmartError(f"Compilation stopped due to version check.")

            logging.warning("Compilation continue, but the version of compiller is not compatible with required version. Please update Smart.")

        else:
            logging.info(f"Compiletime checkversion ok: the current version of Smart ({SMART_VERSION}) is compatible with the required version ({major}.{minor}.{patch}).")

    else:
        raise SmartError("Expected keyword after 'compiletime'.")



