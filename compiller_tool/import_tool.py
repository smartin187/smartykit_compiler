# -*- coding: utf-8 -*-

import os
from pathlib import Path
import sys

from compiller_tool.smart_exception import ModuleError, CompileError
from compiller_tool.color_tool import Colors

compile_smarty = None

PATH_LIB = {
    "global":"/usr/lib/Smart-SmartyKit/global_lib/" if sys.platform == "linux" else os.path.join(os.environ["LOCALAPPDATA"], "Smart-SmartyKit\\lib\\global_lib\\"),
    "smart":"/usr/lib/Smart-SmartyKit/smart_lib/" if sys.platform == "linux" else os.path.join(os.environ["LOCALAPPDATA"], "Smart-SmartyKit\\lib\\smart_lib\\"),
    "base":"/usr/lib/Smart-SmartyKit/" if sys.platform == "linux" else os.path.join(os.environ["LOCALAPPDATA"], "Smart-SmartyKit\\lib\\")
}

class ModuleInfo:
    """A class used by compile_smarty to get the variable and function names + binary code."""
    def __init__(self, binary:str, variable:dict, function:dict, variable_address:int):
        self.binary = binary
        self.variables = variable
        self.function = function
        self.variable_addres = variable_address

def show_path_lib() -> None:
    """Show the path for the global and smart lib."""
    print(f"{Colors.GREEN}Lib path (for import from lib and smart):{Colors.RESET}",
        f"Global lib path: {PATH_LIB['global']}",
        f"Smart lib path: {PATH_LIB['smart']}",
        sep="\n"
    )


def control_lib() -> None:
    """Raise ModuleError if the path for the global and smart lib is missing."""
    if not Path(PATH_LIB["global"]).is_dir():
        raise ModuleError(f"Module error: global lib directory is missing. Path is '{PATH_LIB['global']}'")

    if not Path(PATH_LIB["smart"]).is_dir():
        raise ModuleError(f"Module error: smart lib directory is missing. Path is '{PATH_LIB['smart']}'")


def config_import(_compile_smarty) -> None:
    """Get the dependency from smart_compiller.py"""
    global compile_smarty
    compile_smarty = _compile_smarty

def get_module(path:str, start_adress:int, var_module:dict) -> ModuleInfo:
    """Return the ModuleInfo from a path."""
    try:
        module_info:ModuleInfo = compile_smarty(
            file=path,
            CODE_ADRESSE=start_adress,
            make_file=False,
            module_name=path,
            smart_var_module=var_module
        )

        module_info.binary = module_info.binary.split(":")[1].lstrip()

        return module_info

    except RecursionError:
        raise CompileError(f"Error during compiling module: max recursion. Maybe a module have import it?\n\nOn '{path}' module.")

def import_module(file_name:str, start_adress:int, no_error:bool=False, module_var:dict={}) -> ModuleInfo:
    """Import a module from name (path can be relative or absolute)."""
    path = os.path.abspath(file_name)

    if not Path(path).is_file():
        raise ModuleError(f"File '{path}' not exist!", no_error=no_error)

    return get_module(path, start_adress, var_module=module_var)



def import_lib(file_name:str, start_adress:int, no_error:bool=False, module_var:dict={}) -> ModuleInfo:
    """Import a module from the library. Path is :
    Linux: /usr/lib/Smart-SmartyKit/global_lib/...
    Windows: %LOCAL_APPDATA%/Smart-SmartyKit/lib/global_lib/"""

    control_lib()

    path = os.path.join(PATH_LIB["global"], file_name)

    if not Path(path).is_file():
        raise ModuleError(f"File '{path}' not exist!", no_error=no_error)

    return get_module(path, start_adress, var_module=module_var)

def import_smart(file_name:str, start_adress:int, no_error:bool=False, module_var:dict={}) -> ModuleInfo:
    """Import a module from the smart library. Path is :
    Linux: /usr/lib/Smart-SmartyKit/smart_lib/...
    Windows: %LOCAL_APPDATA%/Smart-SmartyKit/lib/smart_lib/"""

    control_lib()

    path = os.path.join(PATH_LIB["smart"], file_name)

    if not Path(path).is_file():
        raise ModuleError(f"File '{path}' not exist!", no_error=no_error)

    return get_module(path, start_adress, var_module=module_var)

def import_all(file_name:str, start_adress:int, module_var:dict) -> ModuleInfo:
    """Import a module from all the paths (file, lib, smart).
    The order is file, lib, smart."""
    try:
        return import_module(file_name, start_adress, no_error=True, module_var=module_var)
    except ModuleError:
        pass

    try:
        return import_lib(file_name, start_adress, no_error=True, module_var=module_var)
    except ModuleError:
        pass

    try:
        return import_smart(file_name, start_adress, no_error=True, module_var=module_var)
    except ModuleError:
        raise ModuleError(f"Module '{file_name}' not found in any path.")