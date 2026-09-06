# 6502 Smart Compiler

![Logo](./img/logo_smart_small.png)

Smart Compiler is a project that aims to make programming on a Smarty Kit (an Apple-1 replica) simpler.

This repository contains a compiler for Smart code (a language created for the Smarty Kit) and an interpreter for that language (if you want to test a program without a Smarty Kit).

>Smart is in development. Some bugs are to fix. Report issues if you have problems. New features will be added soon...

## The Smart programming language

Smart is a very simple programming language. If you need more features, you should use BASIC instead, or write assembly directly.

_New features will be added soon..._

The advantage of Smart is that it is optimized for the Smarty Kit CPU.

Once your program is ready, you can either [compile it](#compile-smart-code) or [run it in the interpreter](#interpret-smart-code-emulator).

### Writing Smart code

Below is the complete list of Smart features and syntax.

#### Generic syntax

Smart instructions must be separated by semicolons `;`. Newlines and spaces can be added anywhere in your code.

##### Comments

Smart comments use two slashes: `//`. Everything that follows on the same line is ignored.

#### Value types

There are currently two value types: a hexadecimal value and a char (a single character).

_Simple value (on 1 byte):_

##### `bool` value

Can be `True` or `False` (upper case in first character).

##### `hex` value

This value is a 1-byte hexadecimal number, ranging from `00` to `FF`.

**You need to set `0x` before:**
- `0x00`
- `0x41`

##### `int` value

This value is between 0 and 255.


##### `char` value

This value is a 1-byte character. Here is the list of allowed characters:

`!"#$%'()*,+-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`

The character must be wrapped in single quotes.

Examples:
- `'A'`
- `'B'`
- `'1'`

---

_advanced value (on 21 bytes):_

##### `str` (string of `char`) and `list`

This value is saved on 21 bytes, so the max length of a `str` of `list` is 21 characters.

###### `str` value

It starts and ends with double quotes.

Allowed characters are the same as for [`char`](#char-value).

> **Only on print function**, the `str` can be longer than 21 **if the string is know at the compile time!**. For other `str`, the max length is 21.

**Escape characters**

One `str`, you have escape characters.

- `\r`: carriage return
- `\"`: for have a `"`

###### F-string

F-string is a mode for add simple value inside a `str` value.

F-string start with `F` and have `{}` for add a simple value.

`F"TEXT{SIMPLE_VALUE}TEXT"`

###### `list` value

`list` value is an other representation of `str` value.

`list` start with `[` and end with `]`. Inside, you can add simple value separated by `,`.

`[SIMPLE_VALUE,SIMPLE_VALUE]//max len of 21`

###### Index on `list` or `str`

See the documentation of [advanced variable](#indexing-on-advanced-variable-list-or-str) for indexing on `list` or `str` value.


#### Using registers

In Smart, you can directly modify the value of an accumulator register.

However, it is not recommended, because registers are used for many operations (your value may get overwritten...)

The three available accumulators are A, X, and Y.

To assign a value, use the syntax `RegisterName = Value`:
```Smart
A = 0x00;  // put the hex value into A
A = 'B'; // put the character B into A
```

Registers X and Y are rarely used directly, because they are normally used for loops...

#### compiletime keyword

The `compiletime` keyword is used to set a action during compilation.

##### `compiletime define`

The `compiletime define` keyword is used to define a constant, or code at compile time. The value can't be changed at runtime.

```Smart
compiletime define MY_CONSTANT to 'A';

print: MY_CONSTANT;

compiletime define MY_CODE to print: "HELLO";

MY_CODE;
```

> The define replace the name to the value. But the replace is not set on a line with `compiletime`...

###### Redefine

You can redefine a define, but you will have a warning...

```Smart
compiletime define MY_CONSTANT to 'A';
print: MY_CONSTANT; // A
compiletime define MY_CONSTANT to 'B'; // Warning: redefine MY_CONSTANT
print: MY_CONSTANT; // B
```

> But the define can't be changed at runtime.

##### `compiletime debug`

If you have problem with your code, you can use `compiletime debug` for print the line running at the run time.

For activate the debug, set:

```Smart
compiletime debug True;
// or
compiletime debug 1;
```

For remove the debug, set:

```Smart
compiletime debug False;
// or
compiletime debug 0;
```

> **Warning**: the debug value (True, False, 1 or 0) can't be a runtime value (variable, return-function...).

When debug is activated, for all lines running, the line is printed before the line is run.

> On SmartyKit or Apple 1, some character are not allowed. On the line printed, if a letter is lowercase, the letter will be printed as uppercase. If the character can't be printed, the character is replaced by `?`.

**Example:**
```Smart
compiletime debug True;
.a = 1;
.b = 2;
.é = 3; // the character 'é' can't be print
print: 'A';
```

The output will be:

```
.A = 1
.B = 2
.? = 3
PRINT: 'A'
A
```

> Note: the comment and the `;` are removed.

**Careful**: the hex generated with debug activated can be big! If you can, use debug only for some lines and next set `compiletime debug False;`. Moreover, the program will be slower...

If you use the [Smart Emulator](#interpret-smart-code-emulator), you can set the speed to maximum. See [Speeding up program execution](#speeding-up-program-execution).

##### `compiletime realloc`

The `compiletime realloc` is used for realloc a old variable to a new variable.

You can use when a variable is used in a time, but not used after. So you can realloc the variable to a new variable for save memory.

See [Variables](#variables) for more information about variable.

Syntax:
```Smart
.old_variable = value;
compiletime realloc .old_variable to .new_variable;
```

For example:
```Smart
.a = 1;
compiletime realloc .a to .b;
.b = 'A';
print: .b;
```

> Note: the address of new variable is the same to old variable. So if you don't change the value of new variable, the value of old variable is used.

Example:
```Smart
.a = 'A';
compiletime realloc .a to .b;
print: .b; // A
```

> You can't realloc a variable of a different type: simple value and advanced value.

For example, you can't do:
```Smart
.simple_value = 1;
compiletime realloc .simple_value to ~advenced_value; // ERROR

~advenced_value = "HELLO";
compiletime realloc ~advenced_value to .simple_value; // ERROR
```

##### `compiletime log`

You can set a message on the log of compiler.

For example it is helpful if you make a library and you want to give information:

```Smart
// your library
void function{;
    // code of function
}

.constent = 1;

compiletime log "Library was successfully compiled!";
```

On the output of compiler, you will have:
```log
SmartCompiller INFO: [Compiletime info]: Library was successfully compiled!
```

##### `compiletime checkversion`

This command check if the version of compiller is good for compile the code:

```Smart
compiletime checkversion 0.0.0;
```

If the version of compiller is smaller than the version test, the compiller show a error message and the user can choose to continue or not the compilation (`y/n` question).

> It can be helpful on library: you can control if the minimum version for your library is good for compile the code.

#### Variables

On Smart, they are 2 variables type: simple and advanced.

Simple variable can be used for [`bool` value](#bool-value), [`hex` value](#hex-value), [`int` value](#int-value), and [`char` value](#char-value).

Advanced value can be used for [`str` value](#str-string-of-char).

>Careful: advanced value need a lot of memory!

##### Simple variable

Simple variables must start with a dot `.`.


###### Syntax

The syntax is `.variable_name = value;`.

Variable names can contain lowercase letters, digits, and underscores `_`. A leading dot `.` is required, but dots cannot appear elsewhere in the name.

To use the value of a variable (for example, in a function), write the variable name (including the leading dot).

##### Advanced variable

The syntax is `~variable_name = "VALUE";`.

Variable names can contain lowercase letters, digits, and underscores `_`. A leading tilde `~` is required, but dots cannot appear elsewhere in the name.

To use the value of a variable (for example, in a function), write the variable name (including the leading tilde).

>Careful: advanced variable cannot be used for some operation (like math operation...).

###### Indexing on advanced variable (`list` or `str`)

For get a value from an index on advanced variable (`list` or `str`), use: `~var[index]`.

Index need to be a value between `0` and `20`, or `-21` and `-1` (for reverse index).

You can set a variable for the index, but the index can't be negative. If you need a negative index, you can do: `~var[21-.my_variable]` (because the length of `list` or `str` is 21).

You can also change value of an index on advanced variable:
```Smart
~var[index] = 'A';
```

#### Increment and decrement variable

You can set `++` or `--` after a variable for increment or decrement the variable.

```Smart
.my_variable = 1;
.my_variable++; // increment .my_variable to 2
.my_variable--; // decrement .my_variable to 1
```

You can increment or decrement on a simple variable or on an index of advanced variable (`list` or `str`).

> **Actually, the runtime value for index for increment or decrement is not implemented...**

```Smart
~str = "AAA";
~str[0]++; // increment the first char of ~str to 'B'
print: ~str; // print "BAA"
```

But you can't set a runtime value for index for increment/decrement:
```Smart
.x = 0;
~str = "AAA";
~str[.x]++; // error
```

#### Labels (anchors)

You can create labels (anchors) and later use the [`goto`](#goto) function to jump to a label.

##### Syntax

The syntax is: `#label_name;`.

You can then use [`goto`](#goto).

#### Operator

Operator are the mathematical operator and logic operator.

For all operator, all value are accepted. If the value is a char, the value used is the ASCII code.

**Warning**: `str` value are not accepted, except for `==` operator.

##### `+`

Add tow value.

>Note: if the result exceeds 255, the carry flag is set to 1.

##### `-`

Substract tow values.

##### `*`

Multiply tow values

##### `/`

Division integer of 2 values. The result is round for a integer result.

Set a [runtime error](#runtime-error) if division by 0.

##### `%` (modulo)

Return the modulo of 2 values.

Set a [runtime error](#runtime-error) if modulo by 0.

##### `==` (equality)

Compare 2 value, return True if value are equal False else.

>This value can be `str`. If it is the case, the `str` can't be compared to an other value type.

##### Example

```Smart
.x = 1 + 1;

.y = 10 == 10;

.z = 'A' == 65
```

#### Condition

You can use a conditional block with `if`.

```Smart
if condition{;
    // code
}
```

The condition is a value (int, char, boolean value...). If the value is not `0`, the block is run.

Then an `if` block, you can set a `elif` block. This condition is verified if the condition of `if` block is `False`.

```Smart
if False{;
    print: "IF CODE";
}
elif True{;
    print: "ELIF CODE";
}
```

>You can have several `elif` block.

Then an `if` or `elif` block, you can set a `else` block:

```Smart
if False{;
    print: "IF CODE";
}
else{;
    print: "ELSE CODE";
}
```

##### Example

```Smart
if True == True{;
    print: "THE CONDITION IS TRUE";
}
```

#### Loop

You can do loop in Smart.

Smart have the [`while` loop](#while-loop).

>Moreover, you can build your own loop with [goto](#goto) and [label](#labels-anchors).

>Note: you can also set a infinit loop with recursive function. It work, the perf are low...

On loop, you can use [`break`](#break) and [`continue`](#continue) keyword.

##### `while` loop

This loop is runing as long as the condition is `True`.

If you set `True` on the condition, you have an infinity loop.

###### Syntax

```Smart
while True{;
    print: "INFINIT LOOP";
}
// you can set any condition:
.my_variable = 1;
while 1 == .my_variable{;
    // ...
}
```

On `while` loop, you can use [`break`](#break) and [`continue`](#continue) keyword.

##### `for` loop

The for loop repeats a block of code from a start value to an end value with a step, or iterate on an advanced value (`str` or `list`).

> It the loop iterate on advanced value, the loop repeats 21 times (the length of advanced value is 21).

You can get the current value of the loop, or not use the current value of the loop.

**Repeat from start / end:**
```Smart
// if you need the current value of the loop:
for .variable in |start|end|step|{;
    // code
}
// if you don't need the current value of the loop (most speed):
for _ in |start|end|step|{;
    // code
}
```

You can also set a variable or expression for start, end, and step.

```Smart
.a = 0;
.b = 10;
.c = 1;

for .i in |.a + 1|.b * 2|.c|{;
    print: 'A';
}
```

**Iterate on advanced value:**
```Smart
~string = "ABCDEFG";
for .char in ~string {;
    print: .char;
}
```

###### If start is more than end

If the start value is more than the end value, **the loop is run!**.

The counter is incremented by step value, and when the counter is more than 255, the counter is set to 0. Finally, the counter is incremented, and when the counter is **equal** to end value, the loop is stop.

For example:

```Smart
for .i in |10|5|1|{;
    print: 'A';
}
```

The counter start to 10, is incremented to 255 and then to 0, and after is to 5.

###### If the counter is never equal to end value

**Careful**: if the counter is never equal to end value, the loop is infinite!

```Smart
for .i in |0|5|2|{;
    print: 'A';
}
```

This loop have not end!

**Examples:**
```Smart
// for loop with current value of the loop:
for .i in |0|10|1|{;
    print: '0' + .i;
}
// for loop without current value of the loop:
for _ in |0|10|1|{;
    print: 'A';
}
```

On `for` loop, you can use [`break`](#break) and [`continue`](#continue) keyword.

##### `break`

Use this keyword for go out of loop.

###### Syntax

```Smart
// on while
while True{;
    print: 'A';
    break;  // go out of loop.
    print: "THIS CODE WILL NOT RUN";
}

// on for
for .i in |0|10|1|{;
    print: 'A';
    break;  // go out of loop.
    print: "THIS CODE WILL NOT RUN";
}
```

##### `continue`

Use this keyword for restart the loop.

###### Syntax

```Smart
// on for:
for .i in |0|10|1|{;
    print: 'B';
    continue;  // restart the loop
    // the code after will not run
}

// on while:
while True{;
    print: 'A';
    continue;  // restart the loop
    // the code after will not run
}
```

#### Functions

Smart provides several built-in functions. You can build your own function.

The call syntax is: `functionname: argument;`.

Some functions do not take any arguments, but you still need to include the colon `:`.

They are return-function and function. If the function is a return-function, you can do:
```Smart
.variable = function_name:;
```

##### Smart built-in functions

###### `print`

This function prints a character to the screen.

The value can be a `char`. It can also be a `hex` or `int` (in which case the ASCII code is used), and you can also use a `str`.

**Example**

```Smart
print: 0x41;  // using hex, 0x41=65 (ASCII code for A)
print: '1'; // using a char
print: "HELLO WORLD";   // using a str

.my_variable = 0x42;
print: .my_variable; // B
print: 0x42 + 1;  // C
```

###### `input`

This function is a return-function. This function return a char value of pressed key.

Example:
```Smart
.key = input:;

print: .key
```

###### `goto`

This function jumps to a [label](#labels-anchors).

First define a label, then use this function to jump back to it.

Pass the label name as the argument.

This feature is mainly used to create loops.

**Example**

```Smart
#loop;

print: "INFINITE_LOOP!";

goto: loop;
```

###### `asm_entry`

Use this function for enter assembly code for MOS 6502.

**Warning:** if you use the [Smart Emulator](#interpret-smart-code-emulator), `asm_entry` can cause errors...

Example:
```Smart
asm_entry: "A9 41 20 EF FF";    // display A on monitor
```

**Replace on `asm_entry`:**

You can set special sequence on `asm_entry` for get the current address or the address of a variable.

_Current address:_

Set on the `asm_entry` the sequence `@adress` for get **the address of first byte of hex code**.

```Smart
print: "AAA";   // this code change the current adress

asm_entry: "A9 41 20 EF FF 4C @adress"; // make a infinite loop with print 'A'
```

With `@adress` sequence, you can set a offset on the address with `+` or `-`. The sequence is `@adress+offset|` or `@adress-offset|`:

```Smart
asm_entry: "A9 41 20 EF FF 4C @adress+2|"; // make a infinite loop with print 'A' without LDA on the loop.
```

> Don't forget the `|` after the offset!


_Address of variable:_

You can get the address of a variable with `@var_adress`. The sequence is `@var_adress:.var|` or `@var_adress:~advenced_var|`.

```Smart
.a = 'A';

asm_entry: "AD @var_adress:.a| 20 EF FF ";  // print .a

~b = "HELLO";
asm_entry: "AD @var_adress:~b| 20 EF FF ";  // print the first char of ~b

```

###### `wozm` (Woz Monitor)

This function stop program and return to Woz Monitor.

This function go to `FF1F`, the Woz Monitor `GETLINE`.

Not take any argument.

###### `quit`

This function exits the program.

It does not take any arguments.

> `quit` stop the program but not return to Woz Monitor. Use `wozm` if you want to return to Woz Monitor.

###### `restart`

This function restart the program (the program go to the first operation).

##### Build your own function

You can build your own function.

The syntax is:
```Smart
void name_of_function{;
    // function code
}
```

For use your function:
```Smart
name_of_function:;
```

If your function have parameters:
```Smart
void f: .arg1, .arg2{;
    // code of function
}

// call of function:
f: 1, 2;
```

A parameter of a function can also be a advanced value (`str` or `list`):

```
void f: ~arg1, ~arg2{;
    // code of function
}
// call of function:
f: "STR1", "STR2";
```

> Careful: with recursive function, the parameter of the function are shared with all call of the function.

On function with parameters, you can set the edit variable mode: at the end of the function run, the value of the parameter is set to the variable given in the call of function. Set `*` before the name of parameter on function:

```Smart
void f: *.arg1, *.arg2{;
    .arg1 = 'A';
    .arg2 = 'B';
}

.a = 0;
.b = 0;
f: .a, .b;

print: .a;
print: .b;
```

> Note: the value given must be a variable, not a direct value.

If your function is a return-function, you need the line:
```Smart
void returnfonction{;
    // code of function
    return 1;
}
```

> **Careful**: some bug are to fix with return function!

You can do a recursive function. Smart use the stack for the recursive function. You can have a max recursive of 128 (`256/2`).

> If you exceed the max recursive of 128, you will have stack overflow and the program can crash.

#### import modules

Smart can import a module. When you import it, you get the function and variable of module.

Use `import` keyword for import a module.

```Smart
import "module_name.sma";
```

The file "module_name.sma" is searched in 3 paths:
- The relative path were the compiller is run (the current path)
- The path of global library: on Linux: `/usr/lib/Smart-SmartyKit/global_lib/`, on Windows: `C:\users\you\AppData\Local\Smart-SmartyKit\lib\global_lib\`
- The path of Smart library: on Linux: `/usr/lib/Smart-SmartyKit/smart_lib/`, on Windows: `C:\users\you\AppData\Local\Smart-SmartyKit\lib\smart_lib\`

You can search a module only on a path, use the keyword `from`:
```Smart
import "module_name.sma" from "lib"; // the global library
import "module_name.sma" from "smart"; // the Smart library
import "module_name.sma" from "file"; // search only on the current path
```

##### Standard modules

Smart have some standard modules.

On the GitHub repository, the modules are in `./smart_lib/`. See the [`readme.md` for library](./smart_lib/readme.md).

For use this library, please copy it to the path for Smart library and global library.


If you like to add a standard module for Smart, you can set a pull request. See the [add your library to project](#add-your-library-to-project) for more information.



#### Runtime error

You can set a runtime error with keyword `error`. The value after `error` is the error code (can be `char`, `hex`, `int`).

```Smart
error 'A'; // the error code is 'A'
```

If an runtime error is set, the program displays `E` and next the error code.

>**The error code is displayed as ASCII code.** If your error code is `65` the error code is `A`.

>Warning: if the ASCII code can't be display by SmartyKit, the runtime error print only `E`.

>Note: the value of `error` keyword can be a `bool`, but the character of `0` and `1` ASCII are not visible...

The program is stopped when a runtime error is set.

>If you use runtime error, you can say what is your error code. For example: error `A` is "invalid value", error `B` is ...

##### Runtime error built-in

They are built-in runtime error for some operation:
- error `'/'`: division or `%` (modulo) by zero
- error `'I'`: index out of range (for advanced variables)

_Please do not use this error code for your runtime error: you can't know what error is it..._

##### `try` `except` block

You can catch a runtime error with a `try` `except` block. When a error occurred on `try`, the program go to the `except` block.

```Smart
try{;
    // code
}
except{;
    // code
}
```

For example:
```Smart
try{;
    print: "TRY BLOCK";
    error '1';
    print: "THIS CODE WILL NOT RUN";
}
except{;
    print: "EXCEPT BLOCK";
}
```

> Warning: if you call a function for `try` block, and this function have a runtime error, the program don't go to the `except` block...

#### Multi-threading

> Careful: this functionality is in development. Some bug will be fix...

You can have multi-threading with Smart.

You can have only the main thread and a second thread.

They have 2 type of thread: thread with shared stack and thread without stack.

**Without stack:**

The mose simple is the thread without stack. On this case, only the main thread can call a function. The second thread can't call a function.

**With shared stack:**

This mode is more complex, and some bug are to fix. The stack is shared between the 2 thread. When a thread call a function, the other thread is frozen while the function is running. When the function is finished, the other thread restart.

> Do not use a function with a long time of execution on shared stack, because the other thread is frozen...

Syntax:

_No stack mode_
```Smart
thread nostack {;
    // code of second thread
}

// main thread
```

When the thread is declared, it start.

For example:

```Smart
thread nostack {;
    while True{;
        print: "WAITING...\r";
    }
}
for .i in |0|10|1|{;
    print: .i + '0';
}
```

_Shared stack mode_
```Smart
void f{;
    print: "FUNCTION F\r";
}

void g{;
    print: "FUNCTION G\r";
}

thread stack{;
    while True{;
        f:;
    }
}

while True{;
    g:;
}
```

With shared stack, the second thread can call a function. **But when a thread call a function, the other thread are frozen.** When the function is finished, the other thread restart.

So you can use the shared stack mode, but use fast time function...


##### Performance

The performances of the multi-threading are not good on MOS6502. A lot of processor time is used for switch threads.

Moreover, the binary code can be very big.

> Use multi-threading only if you need it.

###### Processor time (approximate)

**No multi-threading**:
- 100% of processor (1MHz) for main thread

**Multi-threading**:

> For manage thread, need `16` time for all Smart operation (line of code and call function).

> A Smart operation: very variable, on average `8` time. Can be more if the operation have string.

_Approximate processor time:_
- ~ 70% (0,7MHz) for manage thread
- ~ 15% (0,15MHz) for main thread
- ~ 15% (0,15MHz) for second thread

## Compile Smart code

Once you have your code, the first option is to compile it so it can run on a Smarty Kit (code is theoretically compatible with an Apple 1).

To do so, download this repository and run:

`python3 main.py your_file.sma`

_Smart code typically uses the `*.sma` extension._

The compilation result is printed in the terminal, and it is also written to a file with the `*.asm` extension. In this example, the generated file is `your_file.asm`.

To use this code on the Smarty Kit, you can copy/paste it into the Woz Monitor (type `0400:` first if you want to start at address `0x0400`; otherwise, use a different address).

To run the program, type `0400R` in the Woz Monitor (assuming `0400` is the program address).

If your program is long, you can also use the [Smart interpreter](#interpret-smart-code-emulator) on your computer so you don't have to copy it by hand. The interpreter is also useful for debugging, or when your program is slow to execute.

## Interpret Smart code (emulator)

If your program is long to type in, or if you don't have a Smarty Kit, you can use the Smart interpreter.

Note that another option is to use a real Apple-1 emulator to get the exact same behavior.

The Smart interpreter lets you execute Smart code directly on your computer.

Download the code, then run in a terminal:

`python3 smart_emulator.py your_program.sma`

A window opens with the interpreter. Your code will run as if it were on a Smarty Kit.

### Debugging with the interpreter

You can also use the interpreter to debug your program. It allows you to inspect RAM contents as well as the accumulator state and the carry flag.

In the interpreter window, click `see memory` to view memory in real time.

### Speeding up program execution

On a Smarty Kit, execution speed is slow. With the interpreter, you can increase the speed: click `setting`, then uncheck `run with speed of 1Mhz`. Execution will become much faster.


## Information about memory

Smart uses RAM.
- `0x0300` to `0x0400`: variables
- `0x0000` to `0x02FF`: Smart system:
  - `0x0000`: main thread pointer (byte 1) - used only in threading mode
  - `0x0001`: main thread pointer (byte 2) - used only in threading mode
  - `0x0002`: used for math operations (`*` and `/`)
  - `0x0003` to `0x0017`: SaveStr (string storage, 21 bytes)
  - `0x0018` to `0x0030`: SaveStrCMP (string comparison storage, 21 bytes)
  - `0x0031`: SaveAToIndex (index storage for advanced variables)
  - `0x0047`: second thread pointer (byte 1) - used only in threading mode
  - `0x0048`: second thread pointer (byte 2) - used only in threading mode
  - _Other address to `0x02FF` are not used actually._

## Distribution of Smart

For publish Smart, the Python script are compiled with Pyinstaller.

See [build releases](./build_releases/readme.md) for more information.

See also [licence](#licence) for distribut Smart.

## Add your library to project

Smart have some standard library. If you like, you can make a new library and do a pull request at the GitHub repository. See the [documentation for library](./smart_lib/readme.md) for more information.

## Licence

Copyright (c) 2026 smartin178

**Apache License, Version 2.0**

> See [LICENCE](./LICENCE)

## VS Code extension

An extension for VS Code set a coloration for Smart language.

Go to the repository: [smart_smartykit_vscode_extension-cpmpr](https://github.com/smartin187/smart_smartykit_vscode_extension-cpmpr).


