from main.roles import is_editor


def user_roles(request):
    """Menyediakan ``is_editor`` di semua template, berdampingan dengan ``user``
    dari ``django.contrib.auth.context_processors.auth``."""
    return {"is_editor": is_editor(request.user)}
