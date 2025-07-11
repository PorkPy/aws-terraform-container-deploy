FROM public.ecr.aws/lambda/python:3.9

# Debug: Check what's already installed in the base image
RUN echo "=== Python packages in base image ===" && pip list | grep -i numpy || echo "No numpy found in base image"

# Debug: Show what requirements file we're actually using
COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN echo "=== Requirements file content ===" && cat requirements.txt && echo "=== End requirements ==="

# Install packages with no cache to save space and clean up after
RUN pip install --no-cache-dir -r requirements.txt && \
    pip cache purge && \
    rm -rf /root/.cache/pip

RUN mkdir -p ${LAMBDA_TASK_ROOT}/model

COPY main.py tokenizer.py ${LAMBDA_TASK_ROOT}/
COPY transformer.py embedding.py encoder.py attention.py ${LAMBDA_TASK_ROOT}/model/

CMD ["main.lambda_handler"]