import inspect

def validate_datatype(argument_name, argument_value, expected_type, mandatory=False):
    if mandatory and argument_value is None:
        raise ValueError(f"Argument '{argument_name}' is mandatory.")
    
    if argument_value is None:
        return argument_value # None is okay if not mandatory.
    
    if not isinstance(argument_value, expected_type):
        raise ValueError(f"Argument '{argument_name}' should be of type '{expected_type.__name__}'"
                         f"but found '{type(argument_value).__name__}' with value '{argument_value}'.")
    
    
    return argument_value
    