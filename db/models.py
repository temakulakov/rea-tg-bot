from sqlalchemy.ext.declarative import declarative_base
import sqlalchemy as sql
from sqlalchemy.orm import class_mapper
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

Base = declarative_base()

class School(Base):
    __tablename__ = 'schools'
    id = sql.Column(sql.Integer, primary_key=True)
    school_name = sql.Column(sql.String(1024))


class Product(Base):
    __tablename__ = 'products'
    id = sql.Column(sql.Integer, primary_key=True)
    section = sql.Column(sql.String(1024))
    product_name = sql.Column(sql.String(1024))
    date_time_start = sql.Column(sql.DateTime, default=datetime.now)
    date_time_end = sql.Column(sql.DateTime, default=datetime.now)
    id_school = sql.Column(sql.Integer, sql.ForeignKey('schools.id', ondelete="CASCADE"))
    location = sql.Column(sql.String(1024))
    url_scheme = sql.Column(sql.String(1024))
    id_conference = sql.Column(sql.Integer, sql.ForeignKey('conference.id', ondelete="CASCADE"))
    project_format = sql.Column(sql.String(1024))

class Conference(Base):
    __tablename__ = 'conference'
    id = sql.Column(sql.Integer, primary_key=True)
    name = sql.Column(sql.String(1024))
    date= sql.Column(sql.Date)

class MasterClass(Base):
    __tablename__ = 'master_class'
    id = sql.Column(sql.Integer, primary_key=True)
    name = sql.Column(sql.String(1024))
    date_time_start = sql.Column(sql.DateTime, default=datetime.now)
    date_time_end = sql.Column(sql.DateTime, default=datetime.now)
    url_link = sql.Column(sql.String(1024))
    location = sql.Column(sql.String(1024))
    id_conference = sql.Column(sql.Integer, sql.ForeignKey('conference.id', ondelete="CASCADE"))
    def to_dict(self):
        """Конвертирует объект в словарь."""
        return {c.key: getattr(self, c.key) for c in class_mapper(self.__class__).columns}

class Students(Base):
    __tablename__ = "students"
    id = sql.Column(sql.Integer, primary_key=True)
    
    surname = sql.Column(sql.String(1024))
    name = sql.Column(sql.String(1024))
    father_name = sql.Column(sql.String(1024))
    grade = sql.Column(sql.Integer)
    
    id_school = sql.Column(sql.Integer, sql.ForeignKey('schools.id', ondelete="CASCADE"))
    id_product = sql.Column(sql.Integer, sql.ForeignKey('products.id', ondelete="CASCADE"))

    def to_dict(self):
        """Конвертирует объект в словарь."""
        return {c.key: getattr(self, c.key) for c in class_mapper(self.__class__).columns}

class Teacher(Base):
    __tablename__ = "teachers"
    id = sql.Column(sql.Integer, primary_key=True)
    
    surname = sql.Column(sql.String(1024))
    name = sql.Column(sql.String(1024))
    father_name = sql.Column(sql.String(1024))
    
    id_school = sql.Column(sql.Integer, sql.ForeignKey('schools.id', ondelete="CASCADE"))
    
    login = sql.Column(sql.String(1024))
    password = sql.Column(sql.String(1024))
    admin = sql.Column(sql.Boolean, default=False)

    def set_password(self, password):
        self.password = generate_password_hash(password)  # werkzeug
        # self.password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    
    def check_password(self, password):
        return check_password_hash(self.password, password)  # werkzeug
        # return bcrypt.checkpw(password.encode(), self.password_hash.encode())
        
    def to_dict(self):
        """Конвертирует объект в словарь."""
        return {c.key: getattr(self, c.key) for c in class_mapper(self.__class__).columns}
