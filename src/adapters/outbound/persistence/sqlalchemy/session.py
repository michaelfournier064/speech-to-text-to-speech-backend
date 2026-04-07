from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.adapters.outbound.persistence.sqlalchemy.base import Base


class SqlAlchemySessionFactory:
    def __init__(self, database_url: str) -> None:
        self._engine = create_engine(database_url, pool_pre_ping=True)
        self._session_maker = sessionmaker(bind=self._engine, expire_on_commit=False, class_=Session)

    def create_tables(self) -> None:
        Base.metadata.create_all(self._engine)

    def create_session(self) -> Session:
        return self._session_maker()
