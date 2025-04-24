## Table of Contents

- [Project Overview](#project-overview)
  - [Knowledge Bases for Amazon Bedrock](#knowledge-bases-for-amazon-bedrock)
- [Solution Overview](#solution-overview)
- [Part 1 - Deploying an Amazon Bedrock Knowledge Base](#part-1---deploying-an-amazon-bedrock-knowledge-base)
  - [Prerequisites](#prerequisites)
  - [Upload your datasource to Amazon S3 Bucket](#upload-your-datasource-to-amazon-s3-bucket)
  - [Create an Amazon S3 Bucket and Upload Source Code](#create-an-amazon-s3-bucket-and-upload-source-code)
  - [Deploy AWS CloudFormation Stack](#deploy-aws-cloudformation-stack)
  - [Sync Knowledge Base](#sync-knowledge-base)
- [Part 2 - Deploying a Serverless Streamlit Application](#part-2---deploying-a-serverless-streamlit-application)
  - [Create Amazon CodeBuild Project to deploy Streamlit Application on Amazon ECS](#create-amazon-codebuild-project-to-deploy-streamlit-application-on-amazon-ecs)
- [Cleanup](#cleanup)

## Project Overview

Modern chatbots have revolutionized customer service by providing 24/7 support using advanced natural language capabilities through Large Language Models (LLMs). While basic question-answering chatbots have limitations, integration with internal knowledge bases and information systems enables more contextual and personalized conversations. The implementation of [Retrieval Augmented Generation](https://docs.aws.amazon.com/sagemaker/latest/dg/jumpstart-foundation-models-customize-rag.html) (RAG) architecture, particularly through services like [Knowledge Bases for Amazon Bedrock](https://aws.amazon.com/bedrock/knowledge-bases/), allows chatbots to provide more accurate and relevant responses by grounding them in factual information from existing data sources.

### Knowledge Bases for Amazon Bedrock

[Knowledge Bases for Amazon Bedrock](https://aws.amazon.com/bedrock/knowledge-bases/) is a serverless option to build powerful conversational AI systems using RAG. It offers fully managed data ingestion and text generation workflows. 

For data ingestion, it handles creating, storing, managing, and updating text embeddings of document data in the vector database automatically. It splits the documents into manageable chunks for efficient retrieval. The chunks are then converted to embeddings and written to a vector index, while allowing you to see the source documents when answering a question. 

For text generation, Amazon Bedrock provides the [RetrieveAndGenerate](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_agent-runtime_RetrieveAndGenerate.html) API to create embeddings of user queries, and retrieves relevant chunks from the vector database to generate accurate responses. It also supports source attribution and short-term memory needed for RAG applications.

</br><img src="./amazon-bedrock-knowledgebase/images/architecture_2.jpg" alt="architecture2" width="800" align="center" border="1"/></br>

## Solution overview

This solution includes the following AWS services:

* [Amazon Simple Storage Service)](https://aws.amazon.com/s3/) (Amazon S3) as a private data source
* [Knowledge Bases for Amazon Bedrock](https://aws.amazon.com/bedrock/knowledge-bases/) to give foundation models and agents contextual information from your company’s private data sources to deliver more relevant, accurate, and customized responses
* [Amazon OpenSearch Serverless](https://aws.amazon.com/opensearch-service/features/serverless/) vector store to save text embeddings
* [AWS Lambda](https://aws.amazon.com/lambda/) as API function to invoke Knowledge Bases API

</br><img src="./amazon-bedrock-knowledgebase/images/architecture_3.jpg" alt="architecture3" width="800" align="center" border="1"/></br>

This project is separated into two parts for ease of deployment.

1. CloudFormation Template for Deploying an Amazon Bedrock Knowledge Base
2. AWS CDK Project for Deploying a Serverless Streamlit Application for a Chat Interface

## Part 1 - Deploying an Amazon Bedrock Knowledge Base

#### Prerequisites

* Follow the Instructions to [Add or remove access to Amazon Bedrock foundation models](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access-modify.html) listed below:
    * Titan Text Embeddings V2
    * Amazon Nova Lite

#### Upload your datasource to Amazon S3 Bucket

1. Open [Amazon S3](https://console.aws.amazon.com/s3/), choose **Buckets** in the navigation pane.
2. Click **Create bucket**.
3. Name the bucket ```knowledgebase-<*your-account-number*>```.
4. Leave all other bucket settings as default and choose **Create**. 
5. Navigate to the ```knowledgebase-<*your-account-number*>``` bucket. 
6. Choose Create folder and name it ```datasource```.
7. Leave all other folder settings as default and choose **Create**.
8. Navigate to the ```datasource``` folder
9. Drag and drop the source files you prepared earlier to this bucket and choose **Upload**.

#### Create an Amazon S3 Bucket and Upload Source Code

1. Open [AWS CloudShell](https://console.aws.amazon.com/cloudshell/).
2. Clone the Git Repository and zip the source code

    ```bash
    git clone https://github.com/aws-samples/genai-chatbot-pocs.git
    cd genai-chatbot-pocs/contextual-chatbot-with-aws-hosted-interface
    zip -r ../contextual-chatbot-with-aws-hosted-interface.zip ./* && cd ..
    ```
3. Create an Amazon S3 bucket and upload source code as a zip file

    ```bash
    export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query 'Account' --output text)
    if [ "$AWS_REGION" = "us-east-1" ]; then
        aws s3api create-bucket \
            --bucket "codebuild-s3-source-$AWS_ACCOUNT_ID" \
            --region "$AWS_REGION"
    else
        aws s3api create-bucket \
            --bucket "codebuild-s3-source-$AWS_ACCOUNT_ID" \
            --region "$AWS_REGION" \
            --create-bucket-configuration "LocationConstraint=$AWS_REGION"
    fi
    aws s3 cp contextual-chatbot-with-aws-hosted-interface.zip s3://codebuild-s3-source-$AWS_ACCOUNT_ID
4. Upload AWS CloudFormation Template from source code and copy Amazon S3 URL.

    ```bash
    aws s3 cp contextual-chatbot-with-aws-hosted-interface/amazon-bedrock-knowledgebase/template/DeployKnowledgeBase.yaml s3://codebuild-s3-source-$AWS_ACCOUNT_ID/contextual-chatbot-with-aws-hosted-interface/amazon-bedrock-knowledgebase/template/DeployKnowledgeBase.yaml
    echo "AWS CloudFormation Template S3 URL:"
    aws s3 presign s3://codebuild-s3-source-$AWS_ACCOUNT_ID/contextual-chatbot-with-aws-hosted-interface/amazon-bedrock-knowledgebase/template/DeployKnowledgeBase.yaml
    ```

#### Deploy AWS CloudFormation Stack

1. Navigate to [AWS CloudFormation Console](https://console.aws.amazon.com/cloudformation/), click Create stack.
2. Select **Template is ready** for **Prepare template**. 
3. Select **Amazon S3 URL** file for **Template source** and paste the AWS CloudFormation Template URL copied from previous step. Choose **Next**.
4. For **Stack name**, enter a name. In the **Parameters** section, For **S3BucketName**, enter `knowledgebase-<*your-account-number*>`.  Click **Next**.
5.	Leave all default options as is, choose **Next**, and choose **Submit**.
6.	Verify that the CloudFormation template ran successfully, and there are no errors.

#### Sync Knowledge Base

1. Access [Amazon Bedrock Console](https://console.aws.amazon.com/bedrock/)
2. Click on `Knowledge Bases` in the navigation menu
3. Click on the newly created Knowledge Base.
4. Under Data Sources, select `Amazon S3 Source` and click on `Sync`.
4. Wait for the sync to finish.


## Part 2 - Deploying a Serverless Streamlit Application

This guide will walk you through the process of deploying a Streamlit web application on Amazon Web Services (AWS) using the AWS Cloud Development Kit (CDK). Streamlit is a popular Python library for creating web applications with minimal code, and CDK is an infrastructure as code (IaC) tool that simplifies the process of provisioning and managing AWS resources.

</br><img src="./streamlit-serverless/architecture.jpg" alt="architecture" width="800" align="center"/></br>

#### Create Amazon CodeBuild Project to deploy Streamlit Application on Amazon ECS

1. Open [AWS CloudShell](https://console.aws.amazon.com/cloudshell/).

2. Create an AWS IAM Service Role for AWS CodeBuild

    Observe that the same IAM policy attached to logged in user role is attached to CodeBuild's Service Role as well.

    ```bash
    cat << 'EOF' > codebuild-trust-policy.json
    {
    "Version": "2012-10-17",
    "Statement": [
        {
        "Effect": "Allow",
        "Principal": {
            "Service": "codebuild.amazonaws.com"
        },
        "Action": "sts:AssumeRole"
        }
    ]
    }
    EOF

    aws iam create-role --role-name CodeBuildServiceRole-$AWS_REGION --assume-role-policy-document file://codebuild-trust-policy.json

    aws iam attach-role-policy --role-name CodeBuildServiceRole-$AWS_REGION --policy-arn $(aws iam list-attached-role-policies --role-name $(aws sts get-caller-identity --query 'Arn' --output text | cut -d'/' -f2) --query 'AttachedPolicies[0].PolicyArn' --output text)
    ```

2. Create an AWS CodeBuild project using Amazon S3 as source and start building the project

    ```bash
    export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query 'Account' --output text)
    aws codebuild create-project \
    --name "contextual-chatbot-with-aws-hosted-interface" \
    --source "{
        \"type\": \"S3\",
        \"location\": \"codebuild-s3-source-$AWS_ACCOUNT_ID/contextual-chatbot-with-aws-hosted-interface.zip\",
        \"buildspec\": \"buildspec.yml\"
    }" \
    --artifacts "{
        \"type\": \"NO_ARTIFACTS\"
    }" \
    --environment "{
        \"type\": \"LINUX_CONTAINER\",
        \"image\": \"aws/codebuild/amazonlinux2-x86_64-standard:5.0\",
        \"computeType\": \"BUILD_GENERAL1_SMALL\",
        \"privilegedMode\": true
    }" \
    --service-role $(aws iam get-role --role-name CodeBuildServiceRole-$AWS_REGION --query 'Role.Arn' --output text)

    aws codebuild start-build --project-name "contextual-chatbot-with-aws-hosted-interface"
    ```

Navigate to [AWS CodeBuild](https://console.aws.amazon.com/codesuite/codebuild/projects) to see the logs.

**If this is your first time deploying it, the process may take approximately 15-20 minutes.**

Once the deployment process is complete, you will see the Amazon CloudFront URL for the hosted Streamlit Application. Click on the link to access the application.


The chatbot interface will open in your default browser, ready for natural language interactions.

## Cleanup

1. Open [Amazon S3](https://console.aws.amazon.com/s3/),  select `knowledgebase-XXXXXX` bucket and click on **Empty** bucket. Repeat the process for `codebuild-s3-source-xxxx` bucket.
2. Delete `knowledgebase-XXXXXX` and `codebuild-s3-source-xxxx` once they are empty.
3.  Open [AWS CloudFormation](https://console.aws.amazon.com/cloudformation/), delete `StreamlitServerlessApp-FrontendStack` and `amazon-bedrock-knowledge-base` stacks.
4. Open [Amazon CodeBuild](https://console.aws.amazon.com/codesuite/codebuild/projects), delete `contextual-chatbot-with-aws-hosted-interface` project.