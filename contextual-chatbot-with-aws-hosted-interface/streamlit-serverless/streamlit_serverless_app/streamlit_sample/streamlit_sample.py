import streamlit as st
import boto3
import json
from botocore.exceptions import ClientError

region = boto3.Session().region_name
session = boto3.Session(region_name=region)
lambda_client = session.client('lambda')

st.title("Amazon Bedrock Powered AI Chat Assistant")

# Initialize chat history and session id
if "messages" not in st.session_state:
    st.session_state.messages = []

if 'sessionId' not in st.session_state:
    st.session_state['sessionId'] = ""

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("Ask me anything"):
    try:
        # Display user input in chat message container
        question = prompt
        st.chat_message("user").markdown(question)

        # Call lambda function to get response from the model
        payload = json.dumps({
            "question": prompt,
            "sessionId": st.session_state['sessionId']
        })
        
        try:
            result = lambda_client.invoke(
                FunctionName='InvokeKnowledgeBase',
                Payload=payload
            )
            
            result = json.loads(result['Payload'].read().decode("utf-8"))
            response = json.loads(result['body'])
            answer = response['answer']
            sessionId = response['sessionId']

            st.session_state['sessionId'] = sessionId

            # Add user input to chat history
            st.session_state.messages.append({"role": "user", "content": question})

            # Display assistant response in chat message container
            with st.chat_message("assistant"):
                st.markdown(answer)

            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": answer})

        except ClientError as e:
            error_message = "Sorry, I'm having trouble connecting to the service. Please try again later."
            st.error(error_message)
            print(f"AWS Lambda Error: {str(e)}")
            
        except json.JSONDecodeError as e:
            error_message = "Sorry, I received an invalid response. Please try again."
            st.error(error_message)
            print(f"JSON Decode Error: {str(e)}")

    except Exception as e:
        error_message = "An unexpected error occurred. Please try again later."
        st.error(error_message)
        print(f"Unexpected Error: {str(e)}")
