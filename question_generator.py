import openai
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from database import Topic, Question, get_session, init_db
import os

# OpenAI API Key (Set your API key here)
OPENAI_API_KEY = os.getenv("OPENAI_KEY")
openai.api_key = OPENAI_API_KEY

class QuestionGenerator:
    def __init__(self, user_input, user_id):
        self.user_input = user_input
        self.user_id = user_id
        self.session = get_session()

    def get_topics(self):
        """Fetch interview topics from OpenAI API with guaranteed JSON format."""
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Generate a list of 5 interview topics around this subject in valid JSON format."},
                {"role": "user", "content": self.user_input}
            ],
            temperature=0.7
        )

        try:
            topics_json = json.loads(response["choices"][0]["message"]["content"])
            if isinstance(topics_json, list):
                return topics_json
            else:
                return []
        except json.JSONDecodeError:
            print("Error: Received malformed JSON response for topics.")
            return []

    def get_questions(self, topic):
        """Fetch interview questions for a given topic with guaranteed JSON format."""
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Generate a list of 25 interview questions for this topic in valid JSON format."},
                {"role": "user", "content": f"{self.user_input} Topic: {topic}"}
            ],
            temperature=0.7
        )

        try:
            questions_json = json.loads(response["choices"][0]["message"]["content"])
            if isinstance(questions_json, list):
                return questions_json
            else:
                return []
        except json.JSONDecodeError:
            print(f"Error: Received malformed JSON response for topic {topic}.")
            return []

    def save_to_db(self, topics_with_questions):
        """Save topics and questions to the database."""
        for topic_name, questions in topics_with_questions.items():
            topic = Topic(name=topic_name, user_id=self.user_id)
            self.session.add(topic)
            self.session.commit()
            for question_text in questions:
                question = Question(text=question_text, topic_id=topic.id)
                self.session.add(question)
            self.session.commit()

    def run(self):
        """Execute the full workflow."""
        topics = self.get_topics()
        topics_with_questions = {}

        for topic in topics:
            questions = self.get_questions(topic)
            topics_with_questions[topic] = questions

        self.save_to_db(topics_with_questions)
        print("Successfully saved topics and questions to the database.")
