from rest_framework.permissions import BasePermission, SAFE_METHODS

from main.roles import is_editor


class IsPortfolioOwnerOrReadOnly(BasePermission):
    message = "Only the portfolio owner can change projects."

    def has_permission(self, request, view):
        return (
            request.method in SAFE_METHODS
            or request.user.is_superuser
        )


class IsPortfolioOwnerOrEditorOrReadOnly(BasePermission):
    """Keempat peran Tugas 4: lihat aturan lengkapnya di ``main.roles``."""

    message = "Anda tidak memiliki izin untuk melakukan tindakan ini."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        return request.method in ("PUT", "PATCH") and is_editor(request.user)
