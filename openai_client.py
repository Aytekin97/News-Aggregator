from openai import OpenAI

from config import settings


class OpenAiClient:
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model

    def query_gpt(self, messages, response_format):
        completion = self.client.beta.chat.completions.parse(
            model=self.model, messages=messages, response_format=response_format
        )
        return completion.choices[0].message.parsed
    
class OpenAiClientForDates:
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model_dates

    def query_gpt(self, messages, response_format):
        completion = self.client.beta.chat.completions.parse(
            model=self.model, messages=messages, response_format=response_format
        )
        return completion.choices[0].message.parsed
