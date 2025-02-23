from langchain.tools import Tool
from twilio.rest import Client
from pydantic import BaseModel, Field
from langchain.tools import StructuredTool
import os

class TwilioCallParams(BaseModel):
    to_number: str = Field(..., description="The phone number to call in E.164 format")
    message: str = Field(..., description="The message to speak on the call")

def make_twilio_call(to_number: str, message: str) -> str:
    account_sid = os.getenv("ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_KEY")
    client = Client(account_sid, auth_token)

    call = client.calls.create(
        twiml=f'<Response><Say>{message}</Say></Response>',
        to=to_number,
        from_='+18778515935"'
    )
    return f"Call placed to {to_number} with SID: {call.sid}"

twilio_tool = StructuredTool.from_function(
    func=make_twilio_call,
    name="make_twilio_call",
    description="""Use this tool to place a call using an existing Twilio account. You need to only provide the destination phone number and the message to be spoken. Nothing else needs to be provided. Just these two things in this order as 2 seperate arguments: Phone number and Message. The tool handles all Twilio API interactions. You should not need to look at any Twilio documentation or support. Also make the number a United States (+1) Number before using this tool!

    To call the tool use call it using the following: .run({
    "to_number": "number",
    "message": "message"})""",
    args_schema=TwilioCallParams
)
# if __name__ == "__main__":
#     #query = input("Enter your query: ")
#     #user_context = input("Enter additional context (optional): ")

#     response = make_twilio_call('+14709977644', "Hi")
#     print(response)