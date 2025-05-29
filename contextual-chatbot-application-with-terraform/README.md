
## Table of Contents

- [Project Overview](#project-overview)
  - [Introduction](#introduction)
  - [Retrieval Augmented Generation (RAG)](#retrieval-augmented-generation-rag)
  - [Application Features](#features)
- [Solution Overview](#solution-overview)
  - [Infrastructure as Code (IaC)](#infrastructure-as-code-iac)
  - [Core Application Components](#core-application-components)
  - [AWS Services Used](#aws-services-used)
  - [Demo](#demo)
- [Deployment Steps](#steps-for-deployment)
  - [Option 1 : Using AWS Cloud Shell](#option-1--using-aws-cloud-shell)
  - [Option 2 : Using AWS CLI](#option-2--using-aws-cli)
- [Cleanup](#cleanup)


## Project Overview 

### Introduction
Generative AI refers to artificial intelligence systems capable of creating new content, such as text, images, audio, or video. These systems learn patterns from vast amounts of data and use that knowledge to generate novel outputs. Large Language Models (LLMs) like GPT-3, Claude, LLAMA and its successors are prime examples of generative AI in the text domain.

### Retrieval Augmented Generation (RAG)
RAG, or Retrieval-Augmented Generation, is a hybrid approach that combines the strengths of retrieval-based systems with generative AI. This technique enhances the capabilities of large language models by allowing them to access and incorporate external knowledge during the generation process.

#### Key Components of RAG
- **Retriever:** Searches and retrieves relevant information from a knowledge base.
- **Generator:** A large language model that produces coherent text based on the input and retrieved information. 
- **Knowledge Base:** A curated collection of documents, databases, or other sources of information.

#### Benefits of RAG
- **Improved Accuracy:** By grounding responses in retrieved information, RAG reduces hallucinations common in pure generative models.
- **Customization:** Easily adaptable to specific domains by updating the knowledge base.
- **Transparency:** The retrieval step allows for better traceability of the information sources.
- **Up-to-date Information:** The knowledge base can be regularly updated, ensuring the model has access to current information

### Features 
This PoC illustrates building a RAG Application using [Knowledge Bases for Amazon Bedrock](https://aws.amazon.com/bedrock/knowledge-bases/), a fully managed serverless service. The Knowledge Bases for Amazon Bedrock integration allows system to provide more relevant, personalized responses by linking user queries to related information data points. Internally, [Amazon Bedrock](https://aws.amazon.com/bedrock/) uses embeddings stored in a vector database to augment user query context at runtime and enable a managed RAG architecture solution.

**Key Benefits and Architecture Highlights**
- Rapid proof-of-concept deployment for stakeholder demonstrations
- Seamless integration of organizational knowledge with AI capabilities
- Scalable and secure architecture leveraging AWS serverless technologies:
    - ECS and Fargate for flexible, containerized backend services
    - OpenSearch for high-performance vector storage and similarity search
    - User-friendly Streamlit-based frontend for easy adoption and utilization

## Solution Overview

### Infrastructure as Code (IaC)
- Utilizes Terraform and AWS CloudFormation for rapid deployment
- Enables quick setup and reproducibility across environments
- Facilitates version control and scalability of infrastructure


### Core Application Components

- Authentication
    - Secure user authentication via AWS Cognito
    - Basic user management and login functionality
- Knowledge Base Management
    - PDF document upload and management interface
    - Version control for knowledge base documents
- AI-Powered Chatbot
    - Integration with Anthropic Claude models
    - Context-aware responses based on organizational knowledge
    - Natural language understanding capabilities
- Data Syncing and Isolation
    - Direct sync from application with AWS Bedrock knowledge base
    - Incremental updates for efficient data transfer
    - User data segregation and encryption
- User Interface
    - Simple, intuitive UI built with Streamlit
    - Streamlined navigation and search functionality


### AWS Services Used

This Proof of Concept (PoC) demonstrates the implementation of a Retrieval-Augmented Generation (RAG) application using various AWS services. By leveraging the power of generative AI and the robustness of AWS infrastructure, we've created a scalable and efficient RAG solution.

- **Amazon Cognito:** Provides secure user authentication and authorization for the application.
- **Amazon Bedrock Knowledge Base:** Serves as the foundation for our RAG system, offering a managed solution for storing and retrieving relevant information to augment the generative AI model.

- **Amazon OpenSearch Serverless:** Enables efficient and scalable search capabilities, crucial for the retrieval component of our RAG system.

- **Amazon ECS (Elastic Container Service):** Hosts and manages the containerized application, ensuring high availability and easy scalability.

- **Amazon ECR (Elastic Container Registry):** Stores and manages the Docker images used by our ECS deployment.

- **Amazon S3 (Simple Storage Service):** Used for storing documentations which can be used as  knowledge base.

- **Streamlit:** While not an AWS service, Streamlit is used to create the user interface for our RAG application, hosted within the ECS environment.

- **CloudFormation:** Used in conjunction with Terraform for some AWS-specific resources that are better handled by CloudFormation, such as certain aspects of Cognito or Bedrock configurations.

- **Terraform:** The primary tool used for defining and provisioning the AWS infrastructure. Terraform manages most of the AWS resources, including VPC configuration, ECS clusters, S3 buckets, IAM roles, and OpenSearch Serverless domains.


### Demo
<img src="RAGApplication.gif">

## Steps for Deployment

* **This solution has been tested in following regions.** You might need some tweaks if you are planning to deploy in any other AWS Region
    - **us-east-1**
    - **us-west-2**

* **This Solution will be deployed in default VPC**

### Option 1 : Using AWS Cloud Shell 


1. Navigate to AWS Console and Open the AWS Cloudshell 
1. Install **terraform** on Aws Clould Shell 
    ```
     git clone https://github.com/tfutils/tfenv.git ~/.tfenv
    mkdir ~/bin
    ln -s ~/.tfenv/bin/* ~/bin/
    tfenv install
    tfenv use
    terraform --version 
    ```
1. Clone the repo `https://github.com/aws-samples/genai-chatbot-pocs`
    ```
    git clone https://github.com/aws-samples/genai-chatbot-pocs.git
    ```

1. Go to Folder `contextual-chatbot-application-with-terraform`
    ```
    cd genai-chatbot-pocs/contextual-chatbot-application-with-terraform
    ```
1. run below terraform command to install application 
    ```
    terraform -chdir="terraform" init
    terraform -chdir="terraform" apply -auto-approve -var="image_tag=1" -var="aws_region=us-east-1"
    ```
1. you will get the cloudfront domain at end. Please use it to login ( user3 , Test@1234567)


### Option 2 : Using AWS CLI 

#### Pre-Requisite 
1. AWS CLI installed 
1. AWS User with appropriate access logged-in through AWS CLI  

#### Steps for Deployment 


1. Navigate to your Terminal / Command window 

1. Install **terraform** 
    ```
    git clone https://github.com/tfutils/tfenv.git ~/.tfenv
    mkdir ~/bin
    ln -s ~/.tfenv/bin/* ~/bin/
    tfenv install
    tfenv use
    terraform --version 
    ```

1. Clone the repo `https://github.com/aws-samples/genai-chatbot-pocs`
    ```
    git clone https://github.com/aws-samples/genai-chatbot-pocs.git
    ```

1. Go to Folder `contextual-chatbot-application-with-terraform`
    ```
    cd genai-chatbot-pocs/contextual-chatbot-application-with-terraform
    ```
1. run below terraform command to install application 
    ```
    terraform -chdir="terraform" init
    terraform -chdir="terraform" apply -auto-approve -var="image_tag=1" -var="aws_region=us-east-1"
    ```
1. you will get the cloudfront domain at end. Please use it to login ( user3 , Test@1234567). It may take couple of mins before it is loaded on cloudfront domain.



## Cleanup 

### Deleting All Resources / Destroying 

1. Please run below code from same folder to delete all resources created for this application 
    ```
    terraform -chdir="terraform" destroy -auto-approve
    ```


