def dict_to_markdown(data, level=0):
    """Konwertuje słownik na format Markdown"""
    result = []
    indent = "  " * level
    
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                result.append(f"{indent}**{key}:**")
                result.append(dict_to_markdown(value, level + 1))
            else:
                result.append(f"{indent}- **{key}:** {value}")
    
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, (dict, list)):
                result.append(dict_to_markdown(item, level))
            else:
                result.append(f"{indent}- {item}")
    
    else:
        result.append(f"{indent}{data}")
    
    return "\n".join(filter(None, result))

# Użycie
markdown = dict_to_markdown(data)
print(markdown)
