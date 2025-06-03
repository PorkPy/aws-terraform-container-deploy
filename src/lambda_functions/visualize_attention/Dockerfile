FROM public.ecr.aws/lambda/python:3.9

# Install specific NumPy version FIRST
RUN pip install "numpy>=1.21.0,<2.0"

# Then install PyTorch CPU version
RUN pip install torch==2.2.0 --extra-index-url https://download.pytorch.org/whl/cpu

# Install other dependencies (includes matplotlib for visualization)
RUN pip install boto3 matplotlib

# Create model directory structure to match original project
RUN mkdir -p ${LAMBDA_TASK_ROOT}/model

# Copy function code maintaining directory structure
COPY main.py tokenizer.py ${LAMBDA_TASK_ROOT}/
COPY transformer.py embedding.py encoder.py attention.py ${LAMBDA_TASK_ROOT}/model/

# Set the CMD to your handler
CMD ["main.lambda_handler"]