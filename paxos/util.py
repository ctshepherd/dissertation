def title(s):
    """capitalizes only first character of a string"""
    if len(s) < 2:
        return s.capitalize()
    return s[0].capitalize() + s[1:]
