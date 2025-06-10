FROM public.ecr.aws/lambda/python:3.9

COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install -r requirements.txt

RUN mkdir -p ${LAMBDA_TASK_ROOT}/model

COPY main.py tokenizer.py ${LAMBDA_TASK_ROOT}/
COPY transformer.py embedding.py encoder.py attention.py ${LAMBDA_TASK_ROOT}/model/

CMD ["main.lambda_handler"]