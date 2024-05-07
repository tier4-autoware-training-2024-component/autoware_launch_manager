from ament_index_python.packages import get_package_share_directory
import re
import os

patterns = {
    "var": r"\$\((var) ([^\)]+)\)",
    "env": r"\$\((env) ([^\s]+)(?:\s+([^\)]+))?\)",
    "eval": "\$\((eval) ([^\)]+)\)",
    "find-pkg-share": r"\$\((find-pkg-share) ([^\)]+)\)",
}


def analyze_eval_string(input_string):
    list_of_strings = input_string.split(' ')
    if list_of_strings[0] == '$(eval':
        expression = ' '.join(list_of_strings[1:])[:-1] # remove the last ')'
        expression = clean_eval_variables(expression)
        result = str(eval(expression)) # remove the outer quotes
    else:
        result = input_string
    return result


def clean_eval_variables(string):
    """Remove quotes and spaces from a string, to obtain the 'value' of a variable."""
    string = string.replace("\\", "")
    if string.startswith('"') and string.endswith('"'):
        return string[1:-1]
    elif string.startswith("'") and string.endswith("'"):
        return string[1:-1]
    else:
        return string

def analyze_string(
    input_string: str, context: dict, local_context: dict, base_namespace: str
):
    """Resolve substitutions recursively in a given string.

    Args:
    context: The arugments and variables context of the current XML file, which is defined by the arg tag and will be passed to the included file
    local_context: The local variable context of the current XML file, which is defined by the let tag
    base_namespace: The current namespace of the XML file

    Returns:
    The string with all substitutions resolved.
    """

    def replace_match(match):
        # Determine type and execute corresponding logic
        if match.group(1) == "var":
            variable_name = analyze_string(
                match.group(2), context, local_context, base_namespace
            )  # Recursively resolve inner substitutions
            ## Check if the variable is in the local context
            var_value = local_context.get(variable_name, None)
            if var_value is None:
                ## Check if the variable is in the global context
                var_value = context.get(variable_name)
            return var_value
        elif match.group(1) == "env":
            var_name = analyze_string(
                match.group(2), context, local_context, base_namespace
            )  # Recursively resolve inner substitutions
            default_value = analyze_string(
                match.group(3) if match.group(3) is not None else "",
                context,
                local_context,
                base_namespace,
            )
            return os.getenv(var_name, default_value)
        elif match.group(1) == "eval":
            ### UNUSED_CODE: This code is not used in the current implementation, we will call analyze_eval_string instead 
            expression = analyze_string(
                match.group(2), context, local_context, base_namespace
            )
            ## Deal with different types of expressions, currently only support ones actually used in the launch files
            ## TODO: Refactor and suport more types of expressions
            expression = clean_eval_variables(expression)
            eval_result = str(eval(eval(expression))) # remove the outer quotes
            print(expression, eval_result)
            return eval_result

        elif match.group(1) == "find-pkg-share":
            package_name = analyze_string(
                match.group(2), context, local_context, base_namespace
            )  # Recursively resolve inner substitutions
            package_dir = get_package_share_directory(package_name)
            return package_dir

        return ""

    # Loop to ensure all substitutions are resolved
    for key, pattern in patterns.items():
        """
        1. Solve all variables.
        2. Solve all environment variables.
        3. Solve all eval expressions.
        4. Solve all find-pkg-share expressions.
        """
        if key == "eval":
            input_string = analyze_eval_string(input_string)
        else:    
            while True:
                old_string = input_string
                input_string = re.sub(pattern, replace_match, input_string)
                # Stop if no more changes are made
                if input_string == old_string:
                    break
    # solve for "\" in the string
    input_string = input_string.replace("\\", "")

    return input_string


def find_linked_path(path):
    if os.path.islink(path):
        linked_path = os.readlink(path)
        return linked_path
    else:
        return path
