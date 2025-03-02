from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

# Database setup
Base = declarative_base()
engine = create_engine("sqlite:///interview_questions.db")
Session = sessionmaker(bind=engine)

# Define the database models
class Topic(Base):
    __tablename__ = 'topics'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    user_id = Column(Integer, nullable=False)
    questions = relationship("Question", back_populates="topic")

class Question(Base):
    __tablename__ = 'questions'
    id = Column(Integer, primary_key=True)
    text = Column(String, nullable=False)
    topic_id = Column(Integer, ForeignKey('topics.id'), nullable=False)
    topic = relationship("Topic", back_populates="questions")

# Function to initialize the database
def init_db():
    Base.metadata.create_all(engine)

# Get session instance
def get_session():
    return Session()
