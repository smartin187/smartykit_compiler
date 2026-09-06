# -*- coding: utf-8 -*-

"""
The Smart emulator (for Apple1/SmartyKit 6502).
Run Smart code on an emulator.
"""


import sys
from time import sleep
from pathlib import Path
import json
import os
from threading import Thread
import webbrowser

from compiller_tool import smart_info
from compiller_tool.color_tool import Colors
from compiller_tool.compiller_data_run import ALLOW_CHAR

from smart_compiller import compile_smart, SmartError, CompileError


if "--show-licence" in sys.argv:
    print(smart_info.LICENCE["licence"], smart_info.LICENCE["text"], sep="\n")
    sys.exit(0)

if "--help" in sys.argv:
    print(smart_info.SMART_HELP["smart_emulator"])
    sys.exit(0)
elif "--version" in sys.argv:
    print(smart_info.SMART_VERSION)
    sys.exit(0)

if __name__ == "__main__":
    if "--console" in sys.argv:
        GUI_MODE = False
        sys.argv.remove("--console")
    else:
        GUI_MODE = True
        import tkinter as tk
        from tkinter import scrolledtext, messagebox, filedialog
else:
    GUI_MODE = False

if GUI_MODE:

    if "--debug" in sys.argv:
        normal_speed = "Debug"
        sys.argv.remove("--debug")
    else:
        normal_speed = "1Mhz"
else:
    normal_speed = "Normal"

no_wozm = False     # used during testing: if true, no message box is shown if the program returns to the Woz monitor

class MessageUser:
    """Message for the user. Can be a graphic message if GUI_MODE else on the console."""
    def show_message_user(type_message:str, title:str, message:str, detail:str="") -> None:
        """Show a message for the user. If GUI_MODE is True, use messagebox, else, print on console."""
        if GUI_MODE:
            match type_message:
                case "error":
                    messagebox.showerror(title, message, detail=detail)
                case "warning":
                    messagebox.showwarning(title, message, detail=detail)
                case "info":
                    messagebox.showinfo(title, message, detail=detail)

                case _:
                    raise ValueError(f"Internal value error on smart emulator: unknown type_message {type_message}. Contact the developer if the problem persists.")

        else:
            head = f"{Colors.RED}Error{Colors.RESET}" if type_message == "error" else f"{Colors.YELLOW}Warning{Colors.RESET}" if type_message == "warning" else f"{Colors.BLUE}Info{Colors.RESET}" if type_message == "info" else ""
            input(f"{head}: {Colors.BOLD}{message}{Colors.RESET}\n{detail}\n{Colors.GREEN}Press enter to continue...{Colors.RESET}")

    def show_error(title:str, message:str, detail:str="") -> None:
        """Show an error message for the user. If GUI_MODE is True, use messagebox, else, print on console."""
        MessageUser.show_message_user("error", title, message, detail)

    def show_warning(title:str, message:str, detail:str="") -> None:
        """Show a warning message for the user. If GUI_MODE is True, use messagebox, else, print on console."""
        MessageUser.show_message_user("warning", title, message, detail)

    def show_info(title:str, message:str, detail:str="") -> None:
        """Show an info message for the user. If GUI_MODE is True, use messagebox, else, print on console."""
        MessageUser.show_message_user("info", title, message, detail)

on_test = False
open_from_asm = False

output_test = ""    # used only on test mode

def control_adress(address: int, type_jump: str) -> None:
    """If the address is outside the program, show a warning to the user and stop the program."""
    if address >= len(code):
        MessageUser.show_error("Error", "Address is outside the programme.", detail=f"Caused by a {type_jump} instruction.\nAddress outside: {hex(address + 0x400).upper()}")


if __name__ == "__main__":
    if len(sys.argv) != 2 and GUI_MODE:
        file_name = ""
        code = ""
        def open_smart() -> None:
            """Use filedialog to open a file."""
            global file_name, code, open_from_asm

            path = filedialog.askopenfilename(defaultextension="sma", filetypes=[("Smart source code", "*.sma"), ("Assembly", "*.asm")])


            if path:
                file_type = os.path.splitext(path)[1]

                if file_type == ".sma":
                    file_name = path
                elif file_type == ".asm":
                    asm_f = open(path, mode="r", encoding="UTF-8")

                    code = asm_f.read()

                    asm_f.close()

                    open_from_asm = True


                else:
                    MessageUser.show_error("Error", f"Unknown file type {file_type}.")

                window_start.destroy()

        window_start = tk.Tk()
        window_start.title("Smart emulator")

        text_info = tk.Label(window_start, text="Open a Smart code source (*.sma) or open an Assembly (*.asm).\nCareful: with assembly, the emulator can have errors...")
        text_info.pack()

        button_open = tk.Button(window_start, text="Open *.sma or *.asm", command=open_smart)
        button_open.pack()

        try:
            image_path = "./img/logo_smart_small.png" if not smart_info.FROZEN else sys._MEIPASS + "/logo_smart_small.png"

            logo_smart = tk.PhotoImage(file=image_path, width=200, height=200)

            label_logo = tk.Label(window_start, image=logo_smart)
            label_logo.pack()
        except Exception as e:
            messagebox.showwarning("Warning", "Impossible to load image `logo_smart_small.png`.", detail=f"Detail: {str(e)}")

        window_start.protocol("WM_DELETE_WINDOW", lambda:sys.exit(0))

        def about_smart() -> None:
            """Open a window for information about Smart Emulator."""
            def window_command() -> None:
                """Open a window for information about the command and flag of Smart Emulator."""
                window_command = tk.Toplevel(window_about)
                window_command.title("Command and flag of Smart Emulator")

                frame_info = tk.LabelFrame(window_command, text="Command and flag of Smart Emulator")
                frame_info.pack()

                clean_help = smart_info.SMART_HELP["smart_emulator"]
                for _, color in Colors.__dict__.items():
                    if isinstance(color, str):
                        clean_help = clean_help.replace(color, "")


                text_command = tk.Label(frame_info, text=clean_help, justify=tk.LEFT)
                text_command.pack()

                bouton_close = tk.Button(window_command, text="Close", command=window_command.destroy)
                bouton_close.pack()

            window_about = tk.Toplevel(window_start)
            window_about.title(f"About Smart Emulator {smart_info.SMART_VERSION}")

            text_info_1 = tk.Label(window_about, text=f"Smart {smart_info.SMART_VERSION}", font=("Arial", 14, "bold"))
            text_info_1.pack()

            text_info_2 = tk.Label(window_about, text="Smart programming is a small language for Apple 1, SmartyKit, or other processor MOS6502.")
            text_info_2.pack()

            text_info_3 = tk.Label(window_about, text=f"Open Source licence: {smart_info.LICENCE['licence']}", font=("Arial", 10, "bold"))
            text_info_3.pack()

            text_info_4 = tk.Label(window_about, text="Make with Python 3")
            text_info_4.pack()

            try:
                image_path = "./img/logo_smart_small.png" if not smart_info.FROZEN else sys._MEIPASS + "/logo_smart_small.png"

                logo = tk.PhotoImage(file=image_path)
                logo_label = tk.Label(window_about, image=logo)
                logo_label.pack()
            except Exception as e:
                messagebox.showwarning("Warning", "Impossible to load image `logo_smart_small.png`.", detail=f"Detail: {str(e)}")

            frame_bouton = tk.LabelFrame(window_about)
            frame_bouton.pack()

            bouton_command = tk.Button(frame_bouton, text="Command", command=window_command)
            bouton_command.grid(column=0, row=0, padx=10)

            bouton_github = tk.Button(frame_bouton, text="See GitHub repository", command=lambda:webbrowser.open(smart_info.GIT_HUB_LINK))
            bouton_github.grid(column=1, row=0, padx=10)

            bouton_licence = tk.Button(frame_bouton, text="See licence", command=lambda:MessageUser.show_info("Licence", smart_info.LICENCE["licence"], detail=smart_info.LICENCE["text"]))
            bouton_licence.grid(column=2, row=0, padx=10)

            window_about.wait_window()

        button_about = tk.Button(window_start, text="About Smart emulator", command=about_smart)
        button_about.pack()

        window_start.mainloop()


    else:
        file_name = sys.argv[1]

    if file_name == "--hex-entry":
        code = input("Enter the hex code : ")

    elif open_from_asm:pass

    else:
        try:
            code = compile_smart(file=file_name, argv=[], CODE_ADRESSE=1024, make_file=False, first_call=True)
        except SmartError as se:
            MessageUser.show_error("Error", "Error during compilation of the Smart code.", detail=f"Detail: {se.syntaxerror}")
            sys.exit(1)

        except CompileError as ce:
            MessageUser.show_error("Error", "Error during compilation of the Smart code.", detail=f"Detail: {ce.error}")
            sys.exit(1)

    asm_code = code


START_RAM = 0

stdin_6502 = {
    "stdin": False, # if a stdin is used
    "text": "",     # the text of stdin
    "read": 0       # the reading character
}

op_run = 0 # the number of opreation already run
max_op_run = 0 # the maximum opreation


if GUI_MODE:

    window_emulator = tk.Tk()
    window_emulator.title("Smart emulator")

    monitor = scrolledtext.ScrolledText(window_emulator, height=24, width=39, bg="#000000", fg="#0099FF", insertwidth=10, insertbackground="#B1B1B1", insertofftime=0)
    monitor.pack()
    monitor.focus_force()
    monitor.tag_configure("error", foreground="#FF0000")
    monitor.tag_configure("sys_message", foreground="#00FF00")

    def disable_edit(event:tk.Event) -> str:
        return "break"

    monitor.bind("<Key>", disable_edit)

    var_info_run = tk.StringVar(window_emulator)

    text_info_run = tk.Label(window_emulator, textvariable=var_info_run)
    text_info_run.pack()

    frame_option = tk.Frame(window_emulator)
    frame_option.pack()

def print_on_text(text:str, sys_message:bool=False, error:bool=False) -> None:
    """Insert the text into the scrolledtext.
    If error = True, use a tag to set the text to red."""
    global output_test
    text = text.replace("\r", "\n")


    if not sys_message:
        text = text.upper()
        if text not in ALLOW_CHAR:      # forbiden char
            return

    if GUI_MODE:
        if error:
            monitor.insert(tk.END, text, "error")
        elif sys_message:
            monitor.insert(tk.END, text, "sys_message")
        else:
            monitor.insert(tk.END, text)
        monitor.see(tk.END)
    elif on_test:
        output_test += text
    else:
        print(text, end="\n" if sys_message else "")

if GUI_MODE:        # set the button for ram and code
    def see_memory() -> None:
        """Open a window to see the memory (RAM, accumulator, carry_flag)."""
        def update_memory() -> None:
            """Update the listbox for memory"""
            # RAM
            pos_listbox = RAM_info.yview()[0]

            selection = RAM_info.curselection()
            selected_index = selection[0] if selection else None

            RAM_info.delete(0, tk.END)

            new_ram = (f"{adress}       {ram[adress]}" for adress in ram)

            RAM_info.insert(0, "Address    Value")

            for adress in new_ram:
                RAM_info.insert(tk.END, adress)

            RAM_info.yview_moveto(pos_listbox)

            if selected_index is not None:
                RAM_info.selection_set(selected_index)

            # accumulator

            selection_acc = accumulator_info.curselection()
            selected_index_acc = selection_acc[0] if selection_acc else None

            accumulator_info.delete(0, tk.END)

            for ac in ("ACCUMULATOR    Value", f"A     " + accumulator["A"], f"X     " + accumulator["X"], f"Y     " + accumulator["Y"]):
                accumulator_info.insert(tk.END, ac)

            if selected_index_acc is not None:
                accumulator_info.selection_set(selected_index_acc)

            # flags
            pos_listbox_flags = flags_info.yview()[0]

            selection_flags = flags_info.curselection()
            selected_index_flags = selection_flags[0] if selection_flags else None

            flags_info.delete(0, tk.END)

            flags_info.insert(0, "Flag    Value")
            for flag_name, flag_value in flags.items():
                flags_info.insert(tk.END, f"{flag_name} = {flag_value}")

            flags_info.yview_moveto(pos_listbox_flags)

            if selected_index_flags is not None:
                flags_info.selection_set(selected_index_flags)

            stack_ptr_info.set(f"{stack_ptr} ({hex(stack_ptr)})")

            window_memory.after(100, update_memory)

        window_memory = tk.Toplevel(window_emulator)
        window_memory.title("Memory")

        text_info = tk.Label(window_memory, text="Information about memory.\nYou can edit memory with double click on the value.\nCareful: editing memory can cause errors.")
        text_info.grid(column=0, row=0, columnspan=3)

        frame_RAM = tk.LabelFrame(window_memory, text="RAM")

        def edit_ram(event:tk.Event) -> None:
            """Open a window to edit the RAM value."""
            def validate() -> None:
                """Edit RAM with the new value."""
                new_value = entry_value.get()

                if len(new_value) != 2 or not all(c in "0123456789abcdefABCDEF" for c in new_value):
                    MessageUser.show_error("Error", "Invalid value. Please enter a hexadecimal value with 2 characters.")
                    return

                ram[("0" * (4 - len(hex(adress)[2:]))) + hex(adress)[2:].upper()] = new_value.upper()

                window.destroy()

            adress = RAM_info.curselection()[0] - 1 + START_RAM
            window = tk.Toplevel(window_memory)
            window.title("Edit RAM")


            text_info = tk.Label(window, text=f"Enter the new value for the RAM.\nCareful: editing memory can cause errors.\nAddress: {hex(adress)}")
            text_info.pack()

            entry_value = tk.Entry(window, width=5)
            entry_value.pack()

            button_validate = tk.Button(window, text="Validate", command=validate)
            button_validate.pack()

        def edit_accumulator(event:tk.Event) -> None:
            """Open a window to edit the accumulator value."""
            def validate() -> None:
                """Edit accumulator with the new value."""
                new_value = entry_value.get()

                if len(new_value) != 2 or not all(c in "0123456789abcdefABCDEF" for c in new_value):
                    MessageUser.show_error("Error", "Invalid value. Please enter a hexadecimal value with 2 characters.")
                    return

                acc_index = accumulator_info.curselection()[0] - 1
                acc_keys = ["A", "X", "Y"]

                accumulator[acc_keys[acc_index]] = new_value.upper()

                window.destroy()

            acc_index = accumulator_info.curselection()[0] - 1
            acc_keys = ["A", "X", "Y"]
            acc_name = acc_keys[acc_index]

            window = tk.Toplevel(window_memory)
            window.title("Edit Accumulator")

            text_info = tk.Label(window, text=f"Enter the new value for the {acc_name} accumulator.\nCareful: editing memory can cause errors.")
            text_info.pack()

            entry_value = tk.Entry(window, width=5)
            entry_value.pack()

            button_validate = tk.Button(window, text="Validate", command=validate)
            button_validate.pack()

        scrollbar_RAM = tk.Scrollbar(frame_RAM)
        scrollbar_RAM.pack(side=tk.RIGHT, fill=tk.Y)

        RAM_info = tk.Listbox(frame_RAM, yscrollcommand=scrollbar_RAM.set)
        RAM_info.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_RAM.config(command=RAM_info.yview)
        RAM_info.bind("<Double-Button-1>", edit_ram)

        frame_RAM.grid(column=0, row=1)

        frame_accumulator = tk.LabelFrame(window_memory, text="Accumulator (register)")

        scrollbar_acc = tk.Scrollbar(frame_accumulator)
        scrollbar_acc.pack(side=tk.RIGHT, fill=tk.Y)

        accumulator_info = tk.Listbox(frame_accumulator, yscrollcommand=scrollbar_acc.set)
        accumulator_info.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_acc.config(command=accumulator_info.yview)
        accumulator_info.bind("<Double-Button-1>", edit_accumulator)

        frame_accumulator.grid(column=1, row=1)

        frame_flags = tk.LabelFrame(window_memory, text="Flags (6502)")

        def edit_flag(event:tk.Event) -> None:
            """Open a window to edit the flag value."""
            def validate() -> None:
                """Edit flag with the new value."""
                new_value = entry_value.get()

                if new_value not in ["0", "1"]:
                    MessageUser.show_error("Error", "Invalid value. Please enter 0 or 1.")
                    return

                flag_index = flags_info.curselection()[0] - 1
                flag_keys = list(flags.keys())

                flags[flag_keys[flag_index]] = int(new_value)

                window.destroy()

            flag_index = flags_info.curselection()[0] - 1
            flag_keys = list(flags.keys())
            flag_name = flag_keys[flag_index]

            window = tk.Toplevel(window_memory)
            window.title("Edit Flag")

            text_info = tk.Label(window, text=f"Enter the new value for the {flag_name} flag.\nValue must be 0 or 1.")
            text_info.pack()

            entry_value = tk.Entry(window, width=5)
            entry_value.pack()

            button_validate = tk.Button(window, text="Validate", command=validate)
            button_validate.pack()

        scrollbar_flags = tk.Scrollbar(frame_flags)
        scrollbar_flags.pack(side=tk.RIGHT, fill=tk.Y)

        flags_info = tk.Listbox(frame_flags, yscrollcommand=scrollbar_flags.set)
        flags_info.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_flags.config(command=flags_info.yview)
        flags_info.bind("<Double-Button-1>", edit_flag)

        frame_flags.grid(column=0, row=2)

        # stack ptr

        frame_ptr = tk.LabelFrame(window_memory, text="Stack pointer")
        frame_ptr.grid(column=1, row=2)

        stack_ptr_info = tk.StringVar(window_memory)

        test_info_ptr = tk.Label(frame_ptr, text="The Stack pointer (SP) is an offset from 0x100.\nThe SP can be between 0x00 and 0xFF.\nThe stack is on RAM from 0x100 to 0x1FF.\nTo edit the stack, edit the RAM from 0x100 to 0x1FF.")
        test_info_ptr.pack()

        label_stack_ptr = tk.Label(frame_ptr, textvariable=stack_ptr_info)
        label_stack_ptr.pack()

        def edit_stack_ptr() -> None:
            """Open a window to edit the stack pointer value."""
            def validate() -> None:
                """Edit the stack pointer with the new value."""
                global stack_ptr
                new_value = entry_value.get().strip()

                try:
                    value = int(new_value)
                except ValueError:
                    MessageUser.show_error("Error", "Invalid value. Please enter an integer between 0 and 255.")
                    return

                if not 0 <= value <= 255:
                    MessageUser.show_error("Error", "Invalid value. Please enter an integer between 0 and 255.")
                    return

                stack_ptr = value

                window.destroy()

            window = tk.Toplevel(window_memory)
            window.title("Edit Stack pointer")

            text_info = tk.Label(window, text="Enter the new value for the stack pointer.\nValue must be between 0 and 255.")
            text_info.pack()

            entry_value = tk.Entry(window, width=5)
            entry_value.insert(0, str(stack_ptr))
            entry_value.pack()

            button_validate = tk.Button(window, text="Validate", command=validate)
            button_validate.pack()

        button_edit_stack_ptr = tk.Button(frame_ptr, text="Edit stack pointer", command=edit_stack_ptr)
        button_edit_stack_ptr.pack()

        update_memory()


    button_RAM = tk.Button(frame_option, text="See memory", command=see_memory)
    button_RAM.grid(column=0, row=0)

    one_pause = False

    def window_code() -> None:
        """Open a window to see the code and see the step."""
        def update_code() -> None:
            """Update the listbox for code"""
            string_run.set(f"Address running: 0x{hex(0x400 + run_step)[2:].upper() if not end_run else 'End of code'}")

            pos_listbox = list_code.yview()[0]
            selection = list_code.curselection()
            selected_index = selection[0] if selection else None

            list_code.delete(0, tk.END)

            adress_conter = 0

            list_code.insert(0, "Address    Code")

            for i in code[1:]:
                list_code.insert(tk.END, f"{hex(0x400 + adress_conter)}      {i}")
                adress_conter += 1

            list_code.yview_moveto(pos_listbox)

            if 0 <= run_step < list_code.size():
                list_code.itemconfig(run_step, {'bg':'#0099FF', 'fg':'#000000'})

            if selected_index is not None:
                list_code.selection_set(selected_index)

            window_code.after(100, update_code)

        window_code = tk.Toplevel(window_emulator)
        window_code.title("See code")

        text_info = tk.Label(window_code, text="See code\nDouble click on a line to edit the code.\nCareful: editing code can cause errors.")
        text_info.pack()

        string_run = tk.StringVar(window_code, value="")

        text_run = tk.Label(window_code, textvariable=string_run)
        text_run.pack()

        frame_code = tk.Frame(window_code)
        frame_code.pack(expand=True, fill=tk.BOTH)

        scrollbar_code = tk.Scrollbar(frame_code)
        scrollbar_code.pack(side=tk.RIGHT, fill=tk.Y)

        list_code = tk.Listbox(frame_code, width=50, yscrollcommand=scrollbar_code.set)
        list_code.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        scrollbar_code.config(command=list_code.yview)

        def edit_code(event:tk.Event) -> None:
            """Open a window to edit the code."""
            def validate() -> None:
                """Edit code with the new value."""
                new_value = entry_value.get()

                if len(new_value) != 2 or not all(c in "0123456789abcdefABCDEF" for c in new_value):
                    MessageUser.show_error("Error", "Invalid value. Please enter a hexadecimal value with 2 characters.")
                    return

                code_index = list_code.curselection()[0] - 1

                if code_index < 0:
                    MessageUser.show_error("Error", "You can't edit this line.")
                    return

                code[code_index + 1] = new_value.upper()

                window.destroy()

            code_index = list_code.curselection()[0] - 1

            if code_index < 0:
                MessageUser.show_error("Error", "You can't edit this line.")
                return

            window = tk.Toplevel(window_code)
            window.title("Edit code")

            text_info = tk.Label(window, text=f"Enter the new value for the code.\nCareful: editing code can cause errors.\nAddress: {hex(0x400 + code_index)}")
            text_info.pack()

            entry_value = tk.Entry(window, width=5)
            entry_value.pack()


            button_validate = tk.Button(window, text="Validate", command=validate)
            button_validate.pack()

        list_code.bind("<Double-Button-1>", edit_code)

        update_code()

        frame_setting = tk.Frame(window_code)
        frame_setting.pack()

        str_var_pause = tk.StringVar(frame_setting, value="Pause")

        def pause_code() -> None:
            """If the code is not in pause, set the pause, else, remove the pause."""
            global one_pause

            if one_pause:
                str_var_pause.set("Pause")
            else:
                str_var_pause.set("Play")

            one_pause = not one_pause

        button_pause = tk.Button(frame_setting, textvariable=str_var_pause, command=pause_code)
        button_pause.grid(column=0, row=0)

        frame_goto = tk.LabelFrame(frame_setting, text="Go to")
        frame_goto.grid(column=1, row=0)

        text_goto = tk.Label(frame_goto, text="Enter the address to go to (hexadecimal):")
        text_goto.pack()

        frame_entry = tk.Frame(frame_goto)
        frame_entry.pack()

        entry_goto = tk.Entry(frame_entry, width=10)
        entry_goto.grid(column=0, row=0)

        def goto_adress() -> None:
            """Go to the step of the code with the address in entry_goto."""
            global run_step

            if end_run:
                MessageUser.show_error("Error", "The code is already run. You can't go to an address.")
                return

            try:
                adress = int(entry_goto.get(), base=16)
            except ValueError:
                MessageUser.show_error("Error", "Invalid hexadecimal value. Please enter a valid hexadecimal number.")
                return

            if 0x400 <= adress < 0x400 + len(code) - 1:
                run_step = adress - 0x400 + 1
            else:
                MessageUser.show_error("Error", f"Invalid address. Please enter a hexadecimal value between {hex(0x400)} and {hex(0x400 + len(code) - 1)}.")



        button_goto = tk.Button(frame_entry, text="Go", command=goto_adress)
        button_goto.grid(column=1, row=0)

    button_code = tk.Button(frame_option, text="See code", command=window_code)
    button_code.grid(column=1, row=0)


    def emulator_setting() -> None:
        """Open a window for the emulator settings"""
        def close_setting() -> None:
            """Destroy the window and set setting."""
            global normal_speed
            normal_speed = var_speed.get()

            window_setting.destroy()

        window_setting = tk.Toplevel(window_emulator)
        window_setting.title("Emulator settings")

        var_speed = tk.StringVar(window_setting, value=normal_speed)

        radio_speed_mos = tk.Radiobutton(window_setting, text="Run with a speed of 1Mhz\n(speed of MOS 6502)", variable=var_speed, value="1Mhz")
        radio_speed_mos.pack()

        radio_debug = tk.Radiobutton(window_setting, text="Run for debug", variable=var_speed, value="Debug")
        radio_debug.pack()

        radio_normal = tk.Radiobutton(window_setting, text="Run with max speed", variable=var_speed, value="Normal")
        radio_normal.pack()

        button_validate = tk.Button(window_setting, text="Validate", command=close_setting)
        button_validate.pack()


    button_setting = tk.Button(frame_option, text="Setting", command=emulator_setting)
    button_setting.grid(column=2, row=0)

    def pressed_key(event:tk.Event) -> str:
        """When a key is pressed, set it at address D010 and D011."""
        char = event.char.upper()

        if char not in ALLOW_CHAR:
            return "break"
        try:
            ram["D010"] = hex(ord(char))[2:].upper()
            ram["D011"] = "01"
        except:
            pass
        return "break"

    window_emulator.bind("<KeyPress>", pressed_key)
    monitor.bind("<KeyPress>", pressed_key)

else:
    one_pause = False

ram = {}
accumulator = {}

run_step = 0
end_run = False

BASE_RAM = {("0" * (4 - len(hex(i)[2:]))) + hex(i)[2:].upper():"00" for i in range(0, 0x400)} | {"D010":"00", "D011":"00"}
BASE_ACCUMULATOR = {"A":"00", "X":"00", "Y":"00"}

BASE_FLAGS = {
    "C": 0,  # Carry
    "Z": 0,  # Zero
    "I": 0,  # Interrupt disable
    "D": 0,  # Decimal mode
    "B": 0,  # Break
    "V": 0,  # Overflow
    "N": 0   # Negative
}

flags = dict(BASE_FLAGS)

class EmulatorError(Exception):
    """Errro about the emulator, used by test.py"""
    pass

class EmulatorStdinError(EmulatorError):
    """Error when try to read a character on given stdin for test but the stdin is end."""
    pass

class EmulatorMaxOPError(EmulatorError):
    """Error when the maximum number of operations is reached. By default: 10000"""
    pass

def error_during_run() -> None:
    """Print an error message on the monitor."""
    print_on_text("\nError occurred during run...", True, True)

def set_flag_for_LD(byte_hex: str) -> None:
    v = int(byte_hex, 16) & 0xFF
    flags["Z"] = 1 if v == 0 else 0
    flags["N"] = 1 if (v & 0x80) else 0

STACK_PTR = 0xFF

stack_ptr = STACK_PTR

_STOP_RUN = False

stop_run = _STOP_RUN

def set_on_stack(value: str) -> None:
    """Set a value on the stack.
    The stack is in memory at 0x100 - 0x1FF."""
    global stack_ptr

    adress_stack = 0x100 + stack_ptr
    hex_adress = hex(adress_stack)[2:].upper().zfill(4)

    ram[hex_adress] = value

    stack_ptr -= 1

    if stack_ptr < 0:
        global stop_run
        MessageUser.show_error("Error", "Stack overflow.", detail="The stack is full. You can't push more values on the stack.\n(the stack ptr is > 0).")
        stop_run = True

def get_from_stack() -> str:
    """Get the value from the stack pointer."""
    global stack_ptr

    stack_ptr += 1

    adress_stack = 0x100 + stack_ptr
    hex_adress = hex(adress_stack)[2:].upper().zfill(4)

    if stack_ptr > STACK_PTR:
        global stop_run
        MessageUser.show_error("Error", "Stack underflow.", detail="The stack is empty. You can't pop more values from the stack.\n(the stack ptr is > 0xFF).")
        stop_run = True

    return ram[hex_adress]



def run_smart() -> None:
    """Run smart code."""
    global code, ram, accumulator, flags, run_step, end_run, op_run

    code = code.split(" ")


    code = [x for x in code if x != ""]

    START = int(code[0][:-1], base=16)

    run_step = 1

    accumulator = dict(BASE_ACCUMULATOR)

    ram = dict(BASE_RAM)

    run_fail = False

    #return_ardess = 0

    while run_step < len(code):

        if max_op_run:
            op_run += 1
            if op_run >= max_op_run:
                raise EmulatorMaxOPError("Maximum operation run reached.")

        if stop_run:
            break

        if run_step < 0:
            MessageUser.show_error("Error", "Run step before 0x400.\nRun step is on variable address.\n", detail="This can be caused by a wrong jump or branch in the code.")
            run_fail = True
            break

        run = code[run_step]

        if one_pause:
            sleep(0.1)
            continue

        if " ".join(code[run_step:run_step + 7]) == "10 FB AD 10 D0 29 7F":     # special code:
            if not stdin_6502["stdin"]:
                if GUI_MODE:
                    var_info_run.set("The programme is waiting for a key...")
                    while ram["D011"] == "00":
                        sleep(0.1)        # wait for a key

                    var_info_run.set("")

                    ram["D011"] = "00"
                    accumulator["A"] = ram["D010"]

                else:
                    sys.stdout.write(Colors.BG_GREEN)
                    key = input()

                    sys.stdout.write(Colors.RESET + "\x1b[K")
                    sys.stdout.flush()


                    if len(key) != 1:
                        MessageUser.show_error("Error", "You must enter a single character.")

                    accumulator["A"] = hex(ord(key))[2:].upper().zfill(2)

            else:
                try:
                    accumulator["A"] = hex(ord(stdin_6502["text"][stdin_6502["read"]]))[2:].upper().zfill(2)
                    stdin_6502["read"] += 1

                except IndexError:
                    raise EmulatorStdinError("stdin end error")

            run_step += 7

        else:
            match run:# normal instruction:

                case "A9":     # A
                    accumulator["A"] = code[run_step + 1]
                    run_step += 2
                    set_flag_for_LD(accumulator["A"])

                case "A2" | "AE":
                    accumulator["X"] = code[run_step + 1] if run == "A2" else ram[code[run_step + 2] + code[run_step + 1]]
                    run_step += 2 if run == "A2" else 3
                    set_flag_for_LD(accumulator["X"])

                case "A0":
                    accumulator["Y"] = code[run_step + 1]
                    run_step += 2
                    set_flag_for_LD(accumulator["Y"])

                case "8D" | "9D":

                    if run == "9D":
                        offset = int(accumulator["X"], base=16)

                        base_adress = int(code[run_step + 2] + code[run_step + 1], base=16)

                        adress = hex(base_adress + offset)[2:].upper().zfill(4)

                    else:
                        adress = code[run_step + 2] + code[run_step + 1]

                    if 0x300 <= int(adress, base=16) >= 0x400:    # write on the program
                        try:
                            code[int(adress, base=16) - START + 1] = accumulator["A"]
                        except:
                            MessageUser.show_error("Error", "Write on unknown address.", detail="Detail: {}".format(hex(0x400 + int(adress, base=16) - START + 1)).upper())
                            run_fail = True
                            break
                    else:
                        ram[adress] = accumulator["A"]

                    run_step += 3

                case "B0":  # BCS
                    offset = int(code[run_step + 1], base=16)
                    if offset >= 0x80:
                        offset -= 0x100

                    if flags["C"] == 1:
                        run_step += 2 + offset
                    else:
                        run_step += 2


                case "E9" | "ED":   # subtract
                    if run == "E9":
                        value = code[run_step + 1]
                    else:
                        value = ram[code[run_step + 2] + code[run_step + 1]]


                    new_A = int(accumulator["A"], base=16) - int(value, base=16) - (1 - flags["C"])

                    if new_A < 0:
                        flags["C"] = 0
                        flags["V"] = 1  # Set Overflow flag
                        new_A += 256
                    else:
                        flags["C"] = 1

                    flags["Z"] = 1 if new_A == 0 else 0
                    flags["N"] = 1 if new_A & 0x80 else 0

                    accumulator["A"] = hex(new_A)[2:].upper().zfill(2)

                    run_step += 2 if run == "E9" else 3

                case "38":
                    flags["C"] = 1

                    run_step += 1

                case "AD" | "BD":

                    if run == "BD":
                        offset_lda = int(accumulator["X"], base=16)
                    else:
                        offset_lda = 0

                    base_adress = code[run_step + 2] + code[run_step + 1]

                    offset_adress = int(base_adress, base=16) + offset_lda

                    adress = hex(offset_adress)[2:].upper()
                    adress = ("0" * (4 - len(adress))) + adress

                    accumulator["A"] = ram[adress]

                    set_flag_for_LD(accumulator["A"])

                    run_step += 3

                case "20":
                    run_step += 1

                    if code[run_step] == "EF" and code[run_step + 1] == "FF":
                        print_on_text(chr(int(accumulator["A"], base=16)))

                        run_step += 2

                    else:
                        return_adress = START + run_step + 1

                        hex_return_adress = hex(return_adress)[2:].upper().zfill(4)

                        set_on_stack(hex_return_adress[2:])
                        set_on_stack(hex_return_adress[:2])

                        adress_call = int(code[run_step + 1] + code[run_step], base=16) - START + 1

                        if adress_call + 0x400 >= 0x400 + len(code):
                            MessageUser.show_error("Error", "Unknown address for call.", detail=f"On JSR (jump to subroutine), the address is outside the programme.\nAddress outside: {hex(adress_call + 0x400).upper()}")
                            run_fail = True
                            break

                        run_step = adress_call

                case "AA":  # transfer A to X
                    accumulator["X"] = accumulator["A"]
                    run_step += 1


                case "00":
                    break

                case "60":
                    adress = get_from_stack() + get_from_stack()    # the 2 bytes of address
                    run_step = int(adress, base=16) - START + 1

                case "4C" | "6C":   # JMP
                    if run == "4C":
                        goto = code[run_step + 2] + code[run_step + 1]
                    else:
                        goto_ptr = code[run_step + 2] + code[run_step + 1]
                        goto_1 = ram[goto_ptr]
                        goto_2 = ram[hex(int(goto_ptr, base=16) + 1)[2:].upper().zfill(4)]
                        goto = goto_2 + goto_1

                    if goto == "FF1F":  # routine Get Line of woz monitor
                        if not no_wozm:
                            MessageUser.show_warning("Warning", "The code jumps to the routine Get Line of Woz monitor.", detail="The programme has returned to Woz monitor.\nThe emulator is stopping...")
                        break

                    run_step = int(goto, base=16) - START + 1

                    control_adress(run_step, "JMP (jump)")

                case "18":
                    flags["C"] = 0

                    run_step += 1

                case "69":
                    add = code[run_step + 1]

                    new_A = int(accumulator["A"], base=16) + int(add, base=16)

                    if new_A >= 256:
                        flags["C"] = 1
                        flags["V"] = 1  # Set Overflow flag
                        new_A -= 256
                    else:
                        flags["C"] = 0

                    # Set Zero and Negative flags
                    flags["Z"] = 1 if new_A == 0 else 0
                    flags["N"] = 1 if new_A & 0x80 else 0

                    accumulator["A"] = hex(new_A)[2:].upper().zfill(2)

                    run_step += 2

                case "8E":   # store X
                    adress = code[run_step + 2] + code[run_step + 1]

                    ram[adress] = accumulator["X"]

                    run_step += 3

                case "C9" | "CD":       # compare A
                    value = code[run_step + 1] if run == "C9" else ram[code[run_step + 2] + code[run_step + 1]]

                    result = int(accumulator["A"], base=16) - int(value, base=16)

                    flags["C"] = 1 if result >= 0 else 0
                    flags["Z"] = 1 if result == 0 else 0
                    flags["N"] = 1 if result & 0x80 else 0

                    run_step += 2 if run == "C9" else 3

                case "D0":       # BNE
                    offset = int(code[run_step + 1], base=16)

                    if offset >= 0x80:
                        offset -= 0x100

                    if flags["Z"] == 0:
                        run_step += 2 + offset
                    else:
                        run_step += 2

                case "30":       # BMI
                    offset = int(code[run_step + 1], base=16)

                    if offset >= 0x80:
                        offset -= 0x100

                    if flags["N"] == 1:
                        run_step += 2 + offset
                    else:
                        run_step += 2

                case "10":       # BPL
                    offset = int(code[run_step + 1], base=16)

                    if offset >= 0x80:
                        offset -= 0x100

                    if flags["N"] == 0:
                        run_step += 2 + offset
                    else:
                        run_step += 2

                case "F0":       # BEQ
                    offset = int(code[run_step + 1], base=16)

                    if offset >= 0x80:
                        offset -= 0x100


                    if flags["Z"] == 1:
                        run_step += 2 + offset
                    else:
                        run_step += 2

                case "90":       # BCC
                    offset = int(code[run_step + 1], base=16)
                    if offset >= 0x80:
                        offset -= 0x100

                    if flags["C"] == 0:
                        run_step += 2 + offset
                    else:
                        run_step += 2

                case "6D":
                    RAM_adress = code[run_step + 2] + code[run_step + 1]


                    add = ram[RAM_adress]

                    new_A = int(accumulator["A"], base=16) + int(add, base=16)

                    if new_A >= 256:
                        flags["C"] = 1
                        flags["V"] = 1  # Set Overflow flag
                        new_A -= 256
                    else:
                        flags["C"] = 0


                    flags["Z"] = 1 if new_A == 0 else 0
                    flags["N"] = 1 if new_A & 0x80 else 0

                    accumulator["A"] = hex(new_A)[2:].upper().zfill(2)

                    run_step += 3

                case "CA":
                    accumulator["X"] = hex((int(accumulator["X"], base=16) - 1) % 256)[2:].upper().zfill(2)

                    flags["Z"] = 1 if accumulator["X"] == "00" else 0
                    flags["N"] = 1 if int(accumulator["X"], base=16) & 0x80 else 0

                    run_step += 1

                case "88":
                    accumulator["Y"] = hex((int(accumulator["Y"], base=16) - 1) % 256)[2:].upper().zfill(2)

                    flags["Z"] = 1 if accumulator["Y"] == "00" else 0
                    flags["N"] = 1 if int(accumulator["Y"], base=16) & 0x80 else 0

                    run_step += 1

                case "E8":
                    accumulator["X"] = hex((int(accumulator["X"], base=16) + 1) % 256)[2:].upper().zfill(2)

                    flags["Z"] = 1 if accumulator["X"] == "00" else 0
                    flags["N"] = 1 if int(accumulator["X"], base=16) & 0x80 else 0

                    run_step += 1

                case "C8":
                    accumulator["Y"] = hex((int(accumulator["Y"], base=16) + 1) % 256)[2:].upper().zfill(2)

                    flags["Z"] = 1 if accumulator["Y"] == "00" else 0
                    flags["N"] = 1 if int(accumulator["Y"], base=16) & 0x80 else 0

                    run_step += 1

                case "8A":  # transfer X to A
                    accumulator["A"] = accumulator["X"]

                    run_step += 1

                case "E0":
                    value = code[run_step + 1]

                    flags["C"] = 1 if int(accumulator["X"], base=16) >= int(value, base=16) else 0
                    flags["Z"] = 1 if accumulator["X"] == value else 0
                    flags["N"] = 1 if int(accumulator["X"], base=16) & 0x80 else 0

                    run_step += 2

                case _:
                    MessageUser.show_error("Error", f"Unknown assembly : {run}, at {run_step} step.")
                    run_fail = True
                    break



        if normal_speed == "1Mhz":
            sleep(0.0025)
        elif normal_speed == "Debug":
            sleep(1.5)

    end_run = True

    print_on_text("\n\nEnd of run", True)

    if run_fail:
        error_during_run()

if __name__ == "__main__":
    if GUI_MODE:
        menu_window = tk.Menu(window_emulator)
        window_emulator.config(menu=menu_window)

        menu_save = tk.Menu(menu_window, tearoff=0)
        menu_window.add_cascade(label="Save...", menu=menu_save)

        def save_monitor() -> None:
            """Save the text of monitor in a *.txt file."""
            file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])

            if file_path:
                Path(file_path).write_text(monitor.get("1.0", tk.END), encoding="utf-8")

        menu_save.add_command(label="Save monitor (as *.txt)", command=save_monitor)

        def export_memory() -> None:
            """Export RAM, accumulator and carry flag in a *.json file."""
            file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("Json files", "*.json")])

            if file_path:
                data = {"RAM": ram, "accumulator": accumulator, "carry_flag": flags["C"]}

                Path(file_path).write_text(json.dumps(data, indent=4), encoding="utf-8")

        menu_save.add_command(label="Save memory (as *.json)", command=export_memory)

        def save_asm() -> None:
            """Save the assembly code in a *.asm file."""
            file_path = filedialog.asksaveasfilename(defaultextension=".asm", filetypes=[("Assembly files", "*.asm")])

            if file_path:
                Path(file_path).write_text(asm_code, encoding="utf-8")

        menu_save.add_command(label="Save assembly (as *.asm)", command=save_asm)

        def start_run() -> None:
            """Call run_smart."""
            try:
                run_smart()
            except IndexError:
                MessageUser.show_error("Error", "Error with address.")
                error_during_run()

            except KeyError as e:
                MessageUser.show_error("Error", "Unknown address RAM", detail=f"Address: 0x{str(e)[1:-1]}")
                error_during_run()

            except Exception as e:
                MessageUser.show_error("Error", "Error during run.", detail=f"Detail: {str(e)}")
                error_during_run()

            if stop_run:
                error_during_run()

        thread_run = Thread(target=start_run, daemon=True)
        thread_run.start()


        window_emulator.mainloop()

    else:
        run_smart()



def start_test(test_code:str, max_op:int, stdin:str | None = None) -> str:
    """Used by test.py to test a functionality."""
    global code, ram, accumulator, flags, run_step, end_run, output_test, no_wozm, stack_ptr, stop_run, op_run, max_op_run

    # reset value:
    run_step = 0
    end_run = False
    no_wozm = True
    stack_ptr = STACK_PTR
    stop_run = _STOP_RUN
    max_op_run = max_op
    op_run = 0

    ram = dict(BASE_RAM)
    accumulator = dict(BASE_ACCUMULATOR)
    flags = dict(BASE_FLAGS)

    code = test_code

    output_test = ""

    stdin_6502["read"] = 0
    if stdin is None:
        stdin_6502["stdin"] = False
        stdin_6502["text"] = ""

    else:
        stdin_6502["stdin"] = True
        stdin_6502["text"] = stdin

    run_smart()

    return output_test