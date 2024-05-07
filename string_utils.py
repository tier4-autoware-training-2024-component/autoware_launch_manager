from ament_index_python.packages import get_package_share_directory
import re
import os

patterns = {
    "var": r"\$\((var) ([^\)]+)\)",
    "env": r"\$\((env) ([^\s]+)(?:\s+([^\)]+))?\)",
    "eval": "\$\((eval) ([^\)]+)\)",
    "find-pkg-share": r"\$\((find-pkg-share) ([^\)]+)\)",
}


def clean_eval_variables(string):
    """Remove quotes and spaces from a string, to obtain the 'value' of a variable."""
    return string.replace('"', "").replace("'", "").strip()


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
                var_value = context.get(os.path.join(base_namespace, variable_name))
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
            expression = analyze_string(
                match.group(2), context, local_context, base_namespace
            )
            ## Deal with different types of expressions, currently only support ones actually used in the launch files
            ## TODO: Refactor and suport more types of expressions
            variables = expression.split("==")
            if len(variables) == 2:
                return str(
                    clean_eval_variables(variables[0])
                    == clean_eval_variables(variables[1])
                )
            variables = expression.split(">=")
            if len(variables) == 2:
                return str(
                    clean_eval_variables(variables[0])
                    >= clean_eval_variables(variables[1])
                )
            variables = expression.split("<")
            if len(variables) == 2:
                return str(
                    clean_eval_variables(variables[0])
                    < clean_eval_variables(variables[1])
                )
            variables = expression.split("+")
            if len(variables) == 2:
                return str(
                    clean_eval_variables(variables[0])
                    + clean_eval_variables(variables[1])
                )

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
        while True:
            old_string = input_string
            input_string = re.sub(pattern, replace_match, input_string)
            # Stop if no more changes are made
            if input_string == old_string:
                break

    return input_string


def find_linked_path(path):
    if os.path.islink(path):
        linked_path = os.readlink(path)
        return linked_path
    else:
        return path
