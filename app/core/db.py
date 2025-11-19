from sqlalchemy import Column, Integer
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base, declared_attr

class PreBase:
    """Базовый класс для моделей с автоматическим именем таблицы."""
        
    @declared_attr
    def __tablename__(cls) -> str:
        """Возвращает имя таблицы из имени класса."""
        return cls.__name__.lower()
    
    id = Column(Integer, primary_key=True)