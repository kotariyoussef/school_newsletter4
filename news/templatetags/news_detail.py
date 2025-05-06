from django import template
from os.path import basename

register = template.Library()

@register.filter
def split(value, arg):
    """
    Split a string by the specified delimiter and return a list.
    Usage: {{ value|split:"delimiter" }}
    """
    return value.split(arg)

@register.filter
def filename(value):
    """
    Extract the filename from a file path or URL.
    Usage: {{ filepath|filename }}
    """
    return basename(value)

@register.filter
def file_extension(value):
    """
    Get the file extension from a file path or URL.
    Usage: {{ filepath|file_extension }}
    """
    try:
        return value.split('.')[-1].lower()
    except (IndexError, AttributeError):
        return ""

@register.filter
def get_icon_class(extension):
    """
    Return the appropriate Font Awesome icon class based on file extension.
    Usage: {{ file_extension|get_icon_class }}
    """
    if not extension:
        return "fas fa-file"
        
    extension = extension.lower()
    
    if extension in ['pdf']:
        return "fas fa-file-pdf"
    elif extension in ['doc', 'docx']:
        return "fas fa-file-word"
    elif extension in ['xls', 'xlsx', 'csv']:
        return "fas fa-file-excel"
    elif extension in ['ppt', 'pptx']:
        return "fas fa-file-powerpoint"
    elif extension in ['zip', 'rar', '7z', 'tar', 'gz']:
        return "fas fa-file-archive"
    elif extension in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg']:
        return "fas fa-file-image"
    elif extension in ['mp3', 'wav', 'ogg', 'flac', 'aac']:
        return "fas fa-file-audio"
    elif extension in ['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm']:
        return "fas fa-file-video"
    elif extension in ['txt', 'md', 'rtf']:
        return "fas fa-file-alt"
    elif extension in ['html', 'htm', 'xml', 'js', 'css', 'py', 'java', 'c', 'cpp', 'php']:
        return "fas fa-file-code"
    else:
        return "fas fa-file"