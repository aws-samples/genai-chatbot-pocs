import streamlit as st
import boto3
from botocore.exceptions import ClientError
import json
import base64
import os
import jmespath
import inspect

from cognito import CognitoAuthenticator
authenticator = CognitoAuthenticator()

## Create Logger 
import logging
logger = logging.getLogger(__name__)
# ConsoleOutputHandler = logging.StreamHandler()
# logger.addHandler(ConsoleOutputHandler)
logger.setLevel(os.getenv("LOG_LEVEL","INFO"))


# Initialize S3 client
s3 = boto3.client('s3')

bedrock_client = boto3.client('bedrock-agent', region_name='us-east-1')
bedrock_agent_runtime = boto3.client('bedrock-agent-runtime')

 # Input for Knowledge Base ID
# data_source_id = os.getenv("DataSourceId","")
# bucket_name = os.getenv("KnowledgeBaseBucket","")
# model_id = os.getenv("ModelId","amazon.nova-lite-v1:0")

knowledge_base_id = st.session_state.knowledge_base_id if 'knowledge_base_id' in st.session_state else os.getenv("KnowledgeBaseId","")
data_source_id = st.session_state.data_source_id if 'data_source_id' in st.session_state else os.getenv("DataSourceId", "")
bucket_name = st.session_state.bucket_name if 'bucket_name' in st.session_state else  os.getenv("KnowledgeBaseBucket", "")
model_id = st.session_state.model_id if 'model_id' in st.session_state else os.getenv("ModelId", "amazon.nova-lite-v1:0")

if 'data_source_id' in st.session_state:
    data_source_id = st.session_state.data_source_id

if 'bucket_name' in st.session_state:
    bucket_name = st.session_state.bucket_name



@st.dialog("File Content",width="large")
def view_content(file):
    logger.info(f"Execution Started :  {inspect.currentframe().f_code.co_name}")
    try:
        file_obj = s3.get_object(Bucket=bucket_name, Key=file)
        file_content = file_obj['Body'].read()
        b64 = base64.b64encode(file_content).decode()
        pdf_display = f'<iframe src="data:application/pdf;base64,{b64}" width="700" height="1000" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)
    except ClientError as e:
        st.error(f"Error downloading file: {e}")
    
# S3 file management function
def s3_file_management():
    logger.info(f"Execution Started :  {inspect.currentframe().f_code.co_name}")
    userName = authenticator.User.UserName
    # userName=USER_INFO.get('Username', 'User')
    if bucket_name:
        # List files in the bucket
        try:
            response = s3.list_objects_v2(Bucket=bucket_name, Prefix=userName)
            files = [obj['Key'] for obj in response.get('Contents', [])]
        except ClientError as e:
            st.error(f"Error listing files: {e}")
            files = []

        # Display existing files
        st.subheader("Existing Files")
        with st.expander("Files", expanded=True):
            if files:
                for file in [x for x in files if x.endswith('.pdf')]:
                    col1, col2, col3 = st.columns([2,1,1])
                    with col1:
                        st.write(file.split('/')[1])
                    with col2:
                        if st.button("Delete", key=f"delete_{file}"):
                            try:
                                s3.delete_object(Bucket=bucket_name, Key=file)
                                st.success(f"File {file} deleted successfully!")
                                st.rerun()
                            except ClientError as e:
                                st.error(f"Error deleting file: {e}")
                    with col3:
                        if st.button("View File",key=f"view_{file}"):
                            view_content(file)
            else:
                st.info("No files found in the bucket.")

        # Upload new file
        st.subheader("Upload New File")
        uploaded_file = st.file_uploader("Choose a file",type=['pdf'])
        if uploaded_file is not None:
            if st.button("Upload"):
                try:
                    
                    s3.upload_fileobj(uploaded_file, bucket_name, userName + "/" +uploaded_file.name,
                                      ExtraArgs={
                                          "Metadata":{
                                              "user":userName
                                              }
                                          }
                                      )
                    metadata = {
                                "metadataAttributes": {
                                        "user":userName
                                        }
                                }
                    metadata = json.dumps(metadata,indent=2)
                    s3.put_object(
                                    Bucket=bucket_name,
                                    Key=f'{userName}/{uploaded_file.name}.metadata.json',
                                    Body=metadata,
                                    ContentType='application/json'
                                 )
                    st.success(f"File {uploaded_file.name} uploaded successfully!")
                    uploaded_file = None
                    st.rerun()
                except ClientError as e:
                    st.error(f"Error uploading file: {e}")

# Function to initiate knowledge base synchronization
def sync_knowledge_base():
    logger.info(f"Execution Started :  {inspect.currentframe().f_code.co_name}")
    try:
        response = bedrock_client.start_ingestion_job(
            knowledgeBaseId=knowledge_base_id,
            dataSourceId=data_source_id
        )
        return response['ingestionJob']['ingestionJobId']
    except ClientError as e:
        st.error(f"Error starting ingestion job: {e}")
        return None

#  Function to monitor ingestion job status
def check_ingestion_job_status(ingestion_job_id):
    logger.info(f"Execution Started :  {inspect.currentframe().f_code.co_name}")
    try:
        # Get current status of the ingestion job
        response = bedrock_client.get_ingestion_job(
            knowledgeBaseId=knowledge_base_id,
            dataSourceId=data_source_id,
            ingestionJobId=ingestion_job_id
        )
        return response['ingestionJob']['status']
    
    except ClientError as e:
        st.error(f"Error checking ingestion job status: {e}")
        return None

def sync_knowledge_base_job():
    logger.info(f"Execution Started :  {inspect.currentframe().f_code.co_name}")
    if st.button("Sync Knowledge Base", key="sync"):
        if knowledge_base_id:
            with st.spinner("Syncing ..."):
                ingestion_job_id = sync_knowledge_base()
                if ingestion_job_id:
                    st.success(f"Sync started. Ingestion Job ID: {ingestion_job_id}")
                    # Check status
                    while True:
                        status = check_ingestion_job_status(ingestion_job_id)
                        if status not in  ['IN_PROGRESS','STARTING','STOPPING']:
                            break
                    st.success(f"Sync Completed. Ingestion Job ID: {ingestion_job_id}")
                else:
                    st.error("Failed to start sync.")
        else:
            st.warning("Please enter a Knowledge Base ID.")


######## CHATBOT Functions #########

def query_knowledge_base(query,sessionId=None):
    logger.info(f"Execution Started :  {inspect.currentframe().f_code.co_name}")
    try:
        # Initialize the Bedrock Agent Runtime client
        model_arn = f'arn:aws:bedrock:us-east-1::foundation-model/{model_id}'

        # Call the retrieve_and_generate method
        if sessionId:
            response = bedrock_agent_runtime.retrieve_and_generate(
                input={
                    'text': query
                },
                sessionId=sessionId,
                retrieveAndGenerateConfiguration={
                    'type': 'KNOWLEDGE_BASE',
                    'knowledgeBaseConfiguration': {
                        'knowledgeBaseId': knowledge_base_id,
                        'modelArn': model_arn,
                        "retrievalConfiguration": { 
                            "vectorSearchConfiguration": { 
                                "filter": { 
                                    "equals":{
                                            "key": "user",
                                            "value": authenticator.User.UserName
                                    }
                                },
                            "numberOfResults": 5
                            }
                        }   
                    },       
                }
            )
        else:
            response = bedrock_agent_runtime.retrieve_and_generate(
                input={
                    'text': query
                },
                retrieveAndGenerateConfiguration={
                    'type': 'KNOWLEDGE_BASE',
                    'knowledgeBaseConfiguration': {
                        'knowledgeBaseId': knowledge_base_id,
                        'modelArn': model_arn,
                        "retrievalConfiguration": { 
                            "vectorSearchConfiguration": { 
                                "filter": { 
                                    "equals":{
                                            "key": "user",
                                            "value": authenticator.User.UserName
                                    }
                                },
                            "numberOfResults": 5
                            }
                        }   
                    },       
                }
            )
        # response = bedrock_agent_runtime.invoke_agent(**payload)
        # Process the response
        generated_text = response['output']['text']
        sessionId = response['sessionId']

        citations = None
        # Return Citation if exist in response 
        # add jmes query to get retrievedReferences from citations root list 
        if 'citations' in response  :
            citations = jmespath.search('citations[].retrievedReferences[].{Text:content.text, Reference:\
                                        { document:metadata."x-amz-bedrock-kb-source-uri", page:metadata."x-amz-bedrock-kb-document-page-number"} }' \
                                        ,response)
        logger.info(f"Generated response: {response}")
        return generated_text,sessionId,citations
    except ClientError as e:
        logger.error (f"Error querying knowledge base: {e}")
        st.error(f"Error querying knowledge base: {e}")
        
        return None

def chatbot_interface():
    logger.info(f"Execution Started :  {inspect.currentframe().f_code.co_name}")
    # Initialize session state for chat history
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    container = st.container(border=True)
   
    # Chat interface
    user_input = st.chat_input("Ask a question:")
    if user_input: 
        if user_input and knowledge_base_id:
            with st.spinner("Thinking..."):
                
                response,sessionId,citations = query_knowledge_base(user_input, sessionId=st.session_state.get("sessionId", None))

                # Store the SessionId if not stored 
                if "sessionId" not in st.session_state:
                    st.session_state.sessionId = sessionId

                # Append current interactions in chat_history 
                st.session_state.chat_history.append({"user":user_input})
                st.session_state.chat_history.append({"assistant":response,'citations':citations}) 
        else:
            st.warning("Please enter a question and ensure a Knowledge Base ID under **Parameter** is provided.")
    
    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(list(message.keys())[0],avatar=":material/person:" if list(message.keys())[0]=="user" else ":material/robot_2:"):
            st.text(list(message.values())[0]) 
            if 'citations' in message and len(message['citations'])>0:
                with st.expander("Sources", expanded=False):
                    st.json(message['citations'])     

def kb_parametersettings():
    with st.expander("Parameters", expanded=False):
        knowledge_base_id_local = st.text_input("Knowledge Base ID", value= knowledge_base_id)
        data_source_id_local = st.text_input("Data Source ID", value= data_source_id)
        bucket_name_local = st.text_input("Bucket Name", value= bucket_name)
        model_id_local = st.text_input("Model ID", value= model_id)

    # Update the parameter to Global varibale if updated and rerun the application
    if st.button("Save", type="primary", key="save"):
        st.session_state.knowledge_base_id = knowledge_base_id_local
        st.session_state.data_source_id = data_source_id_local
        st.session_state.bucket_name = bucket_name_local
        st.session_state.model_id = model_id_local
        # Remove the session id if parameter updated
        if 'sessionId' in  st.session_state:
            del st.session_state['sessionId']
        st.rerun()

# Main app
def main():
    logger.info (f" Stored User Information: {authenticator.User}")
    st.warning(
            "**NOTE:** This application is a Proof of Concept (PoC) developed **strictly for demonstration** purposes."
            "It is not intended for production use or deployment as a real application. "
            "This application can stop working at any time and may have defects. While this application does "
            "not use information for any purpose, users are strongly advised not to upload any sensitive data." 
        )
    auth_code = st.query_params.get("code", None)
    if auth_code:
        st.query_params.clear()
        authenticator.login_from_code(auth_code)
    elif not authenticator.User.IsLoggedIn :
        authenticator.login()
    else :
        # Display user information
        col1,col2 = st.columns([3,1])
        with col1:
            st.subheader(f"Welcome, {authenticator.User.UserName}!")
        with col2:
            if st.button("Logout"):
                authenticator.logout()
        
        st.markdown("---")
        st.subheader("Chatbot")
        chatbot_interface()
        with st.sidebar:
            st.title("S3 File Manager")
            s3_file_management()
            sync_knowledge_base_job()
            kb_parametersettings()


    

if __name__ == "__main__":
    main()