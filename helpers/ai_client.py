import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def ai_chat(message, context_data=None):
    """
    context_data = Python dictionary (user info, bookings, etc.)
    """
    system_base = (
        "FyndPro is an online service-booking platform that connects clients with trusted professionals "
        "for home services such as cleaning, electrical work, glass work, roofing, and more. "
        "Users can register using their mobile number, verify the OTP, and log in securely. "
        "The app has role-based access: clients can browse services and book professionals, "
        "while professionals can manage the bookings assigned to them. "
        "You are an AI assistant for the FyndPro booking application. "
        "Answer concisely and clearly about bookings, schedules, and professionals. "
    )

    system_context = ""
    if context_data:
        system_context = f"Here is the authenticated user's information and database context:\n{context_data}\nUse this ONLY to answer the user's message."

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": system_base},
            {"role": "system", "content": system_context},
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
