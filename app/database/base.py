from datetime import datetime
from typing import Any, ClassVar

from sqlalchemy import inspect
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column

from app.database.utils import resolve_table_name


class Base(DeclarativeBase):
    """Базовый класс для всех SQLAlchemy моделей."""

    __repr_attrs__: ClassVar[list[str]] = []
    __repr_max_length__: ClassVar[int] = 25
    __auto_timestamps__: ClassVar[bool] = False
    __soft_delete__: ClassVar[bool] = True

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    if __auto_timestamps__:
        created_at: Mapped[datetime] = mapped_column(
            default=datetime.utcnow, nullable=False
        )
        updated_at: Mapped[datetime] = mapped_column(
            default=datetime.utcnow,
            onupdate=datetime.utcnow,
            nullable=False,
        )

    if __soft_delete__:
        is_active: Mapped[bool] = mapped_column(
            default=True,
            server_default='true',
            nullable=False,
            index=True,
        )

    @declared_attr.directive
    def __tablename__(cls):
        return resolve_table_name(cls.__name__)

    def __repr__(self) -> str:
        class_name = self.__class__.__name__
        id_str = f'#{self._id_str}' if self._id_str else ''

        attrs = []
        for attr_name in self.__repr_attrs__:
            if hasattr(self, attr_name):
                value = getattr(self, attr_name)
                formatted_value = self._format_repr_value(value)
                attrs.append(f'{attr_name}={formatted_value}')

        attrs_str = ', '.join(attrs)

        status = ''
        if hasattr(self, 'is_active') and not self.is_active:
           status = f' [DELETED]'

        parts = [class_name]
        if id_str:
            parts.append(id_str)
        if attrs_str:
            parts.append(attrs_str)
        if status:
            parts.append(status)

        return f"<{' '.join(parts)}>"


    def _format_repr_value(self, value: Any) -> str:
        """Форматирование значений для repr."""
        if value is None:
            return 'None'
        elif isinstance(value, str):
            if len(value) > self.__repr_max_length__:
                return f"'{value[:self.__repr_max_length__]}...'"
            return f"'{value}'"
        elif isinstance(value, (int, float, bool)):
            return str(value)
        elif isinstance(value, datetime)
            return value.strftime("%Y-%m-%d %H:%M")
        else:
            try:
                insp = inspect(value)
                if insp.identity:
                    return f'{value.__class__.__name__}({insp.identity[0]})'
            except:
                pass
        return f"'{str(value)}'" if len(str(value)) < 30 else f"'{str(value)[:27]}...'"

    @property
    def _id_str(self) -> str:
        """Строковое представление ID для отладки."""
        insp = inspect(self)
        if hasattr(insp, 'identity') and insp.identity:
            ids = insp.identity
            return '-'.join(str(id) for id in ids) if len(ids) > 1 else str(ids[0])

    def soft_delete(self) -> None:
        """Производит мягкое удаление записей, если активно."""
        if hasattr(self, 'is_active'):
            self.is_active = False
        else:
            raise AttributeError(
                f'{self.__class__.__name__} does not support soft delete'
            )

    def restore(self) -> None:
        """Восстанавливает запись после мягкого удаления."""
        if hasattr(self, 'is_active'):
            self.is_active = True
        else:
            raise AttributeError(
                f'{self.__class__.__name__} does not support soft delete'
            )
