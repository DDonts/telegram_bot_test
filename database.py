from sqlalchemy import create_engine, Column, String, Integer, update, exists, select, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from settings import DB_FILEPATH

Session = sessionmaker()

engine = create_engine(f"sqlite:///{DB_FILEPATH}")

Session.configure(bind=engine)

session = Session()

Base = declarative_base()


# Base.metadata.create_all(engine)


class City(Base):
    __tablename__ = 'cities'
    city_id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    url = Column(String)
    population = Column(Integer)

    def add(self):
        session.add(self)
        session.commit()

    def exists(self):
        return session.query(exists().where(
            City.name == self.name)).scalar()

    def update_data(self):
        session.execute(
            update(City).where(City.name == self.name).values(population=self.population, url=self.url))
        session.commit()

    @staticmethod
    def find_by_name(message: str):
        return session.execute(select(City).where(City.name.like(f"{message.capitalize()}%"))).scalars().all()
