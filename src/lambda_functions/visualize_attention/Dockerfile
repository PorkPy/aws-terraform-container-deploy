FROM public.ecr.aws/lambda/python:3.9

# Copy requirements and install all dependencies
COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install -r requirements.txt

# Create model directory structure to match original project
RUN mkdir -p ${LAMBDA_TASK_ROOT}/model

# Copy function code maintaining directory structure
COPY main.py tokenizer.py ${LAMBDA_TASK_ROOT}/
COPY transformer.py embedding.py encoder.py attention.py ${LAMBDA_TASK_ROOT}/model/

# Set the CMD to your handler
CMD ["main.lambda_handler"]