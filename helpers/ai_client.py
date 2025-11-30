import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def ai_chat(message):
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an AI assistant for an professionals Booking app. "
                    "Answer concisely and clearly about bookings, schedules, and professionals."
                )
            },
            {"role": "user", "content": message}
        ]
    )
    return response.choices[0].message.content



# def ai_chat(message):
#     response = client.chat.completions.create(
#         model="llama-3.1-8b-instant",
#         messages=[
#             {
#                 "role": "system",
#                 "content": (
#                     "You are an AI assistant for an Employee Booking application. "
#                     "This app allows users to book employees, check availability, "
#                     "and manage schedules. Answer queries related to this app only."
#                 )
#             },
#             {"role": "user", "content": message}
#         ]
#     )
#     return response.choices[0].message.content




# import os
# from dotenv import load_dotenv
# from groq import Groq

# load_dotenv()

# client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# def ai_chat(message):
#     response = client.chat.completions.create(
#         model="llama-3.1-8b-instant",  # Free model
#         messages=[{"role": "user", "content": message}]
#     )
#     # Access content as an attribute
#     return response.choices[0].message.content
