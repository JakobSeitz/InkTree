"""
Symbol classification helpers used for preprocessing (scaling heuristics).
"""


def get_small_symbols():
    """Symbols that typically sit on the baseline at x-height (no ascenders/descenders)."""
    return ['a', 'c', 'e', 'm', 'n', 'o', 'r', 's', 'u', 'v', 'w', 'x', 'z',
            '\\pi', '\\alpha', '\\gamma', '\\Delta', '\\infty']


def get_large_symbols():
    """Symbols with ascenders, descenders, or full cap-height — used as scale reference."""
    return ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
            'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
            'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
            'b', 'd', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'p', 'q', 't', 'y',
            '\\beta', '\\sigma', '\\theta', '\\lambda']


def get_allowed_symbols():
    """CROHME-compatible symbol set used to filter trace groups during preprocessing."""
    return {
        '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
        'a', '\\alpha', 'b', '\\beta', 'c', ',', '\\cos', 'd', '\\Delta',
        'e', '=', 'f', 'g', '\\gamma', '\\gt', '\\geq', 'h', 'i', '\\int',
        'j', 'k', 'l', '(', '[', '\\lt', '\\leq', '\\log', 'm', '-', 'n',
        '\\neq', 'o', 'p', '\\pi', '+', 'q', 'r', ')', ']', 's', '\\sin',
        '\\sqrt', 't', '\\tan', 'u', 'v', '|', 'w', 'x', 'y', 'z',
    }
