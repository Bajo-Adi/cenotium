from llmcompiler.tools_wrappers import TwilioAgentTool

if __name__ == "__main__":
    tool = TwilioAgentTool()
    result = tool.invoke({
        "to_number": "+14709977644",
        "message": "This is a call to confirm your booking! Have a safe trip!"
    })
    print(result)
