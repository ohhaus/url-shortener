from datetime import datetime
from typing import Any, ClassVar

from sqlalchemy import inspect
from sqlalchemy.orm import DeclarativeBase, declared_attr

from app.database.utils import resolve_table_name


class Base(DeclarativeBase):
    """Базовый класс для всех SQLAlchemy моделей."""

    __repr_attrs__: ClassVar[list[str]] = []
    __repr_max_length__: ClassVar[int] = 25

    @declared_attr.directive
    def __tablename__(cls):
        return resolve_table_name(cls.__name__)

    def __repr__(self) -> str:
        """Минималистичный repr для отладки."""
        class_name = self.__class__.__name__
        pk = getattr(self, '_pk_str', '')
        pk_str = f'#{pk}' if pk else ''

        attrs = []
        for attr_name in self.__repr_attrs__:
            if hasattr(self, attr_name):
                value = getattr(self, attr_name)
                formatted_value = self._format_repr_value(value)
                attrs.append(f'{attr_name}={formatted_value}')

        attrs_str = ', '.join(attrs)
        parts = filter(None, [class_name, pk_str, attrs_str])
        return f"<{' '.join(parts)}>"

    def _format_repr_value(self, value: Any) -> str:
        """Упрощенное форматирование."""
        if value is None:
            return 'None'
        elif isinstance(value, str):
            if len(value) > self.__repr_max_length__:
                return f"'{value[:self.__repr_max_length__]}...'"
            return f"'{value}'"
        elif isinstance(value, (int, float, bool)):
            return str(value)
        elif isinstance(value, datetime):
            return value.strftime("%Y-%m-%d %H:%M")
        else:
            return f"'{str(value)}'"

    @property
    def _pk_str(self) -> str:
        """Универсальное получение первичного ключа."""
        insp = inspect(self)
        if hasattr(insp, 'identity') and insp.identity:
            return str(insp.identity[0])
        return ''
