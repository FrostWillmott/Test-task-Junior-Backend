from rest_framework.pagination import CursorPagination


class DefaultCursorPagination(CursorPagination):
    """Пагинация по умолчанию на основе курсора."""

    ordering = ("-timestamp", "-id")
