import openai
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from database import Topic, Question, get_session, init_db

# OpenAI API Key (Set your API key here)
OPENAI_API_KEY = "your-api-key"
openai.api_key = OPENAI_API_KEY

class QuestionGenerator:
    def __init__(self, user_input, user_id):
        self.user_input = user_input
        self.user_id = user_id

    def get_topics(self):
        """Fetch interview topics from OpenAI API."""
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Generate a list of 5 interview topics around this topic for the user."},
                {"role": "user", "content": self.user_input}
            ]
        )
        topics = response["choices"][0]["message"]["content"].split("\n")
        return [topic.strip() for topic in topics if topic.strip()]

    def get_questions(self, topic):
        """Fetch interview questions for a given topic."""
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Generate 25 interview questions for a person on this topic."},
                {"role": "user", "content": f"{self.user_input} Topic: {topic}"}
            ]
        )
        questions = response["choices"][0]["message"]["content"].split("\n")
        return [q.strip() for q in questions if q.strip()]

    def save_to_db(self, topics_with_questions):
        """Save topics and questions to the database."""
        for topic_name, questions in topics_with_questions.items():
            topic = Topic(name=topic_name, user_id=self.user_id)
            session.add(topic)
            session.commit()
            for question_text in questions:
                question = Question(text=question_text, topic_id=topic.id)
                session.add(question)
            session.commit()

    def run(self):
        """Execute the full workflow."""
        topics = self.get_topics()
        topics_with_questions = {}
        
        for topic in topics:
            questions = self.get_questions(topic)
            topics_with_questions[topic] = questions
        
        self.save_to_db(topics_with_questions)
        print("Successfully saved topics and questions to the database.")

# Example usage
if __name__ == "__main__":
    user_input = "Machine Learning in Healthcare"
    user_id = 1  # Example user ID
    generator = InterviewQuestionGenerator(user_input, user_id)
    generator.run()
