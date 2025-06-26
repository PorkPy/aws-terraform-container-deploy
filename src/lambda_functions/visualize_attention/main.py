import json
import os
import tempfile

import boto3
import matplotlib
import torch

matplotlib.use("Agg")
import base64
from io import BytesIO

import matplotlib.pyplot as plt
import numpy as np
from tokenizer import SimpleTokenizer as Tokenizer

# Initialize S3 client
s3 = boto3.client("s3")


def lambda_handler(event, context):
    """
    Lambda handler for visualizing transformer attention.
    The model is downloaded from S3 at runtime.
    """
    try:
        # Parse request body
        if "body" in event:
            body = json.loads(event["body"])
        else:
            body = event

        text = body.get("text", "Hello, world!")
        layer = int(body.get("layer", 0))

        # Handle both single head and multiple heads
        heads = body.get("heads", [body.get("head", 0)])
        if not isinstance(heads, list):
            heads = [heads]

        # Handle warmup requests
        if text == "warmup":
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
                "body": json.dumps({"status": "warmed"}),
            }

        # Get environment variables
        model_bucket = os.environ["MODEL_BUCKET"]
        model_key = os.environ["MODEL_KEY"]
        tokenizer_key = os.environ["TOKENIZER_KEY"]

        # Create temp directory for downloads
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Download model and tokenizer
            model_path = f"{tmp_dir}/model.pt"
            tokenizer_path = f"{tmp_dir}/tokenizer.json"

            print(f"Downloading model from s3://{model_bucket}/{model_key}")
            s3.download_file(model_bucket, model_key, model_path)

            print(f"Downloading tokenizer from s3://{model_bucket}/{tokenizer_key}")
            s3.download_file(model_bucket, tokenizer_key, tokenizer_path)

            # Load tokenizer
            tokenizer = Tokenizer.load(tokenizer_path)

            # Load model - handle the fact it was saved as full model object
            from model.transformer import SimpleTransformer

            # Create model with the SAME parameters
            model = SimpleTransformer(
                vocab_size=len(tokenizer.word_to_idx),
                d_model=256,
                n_layers=4,
                n_heads=8,
                d_ff=1024,
                max_seq_length=128,
                dropout=0.1,
            )

            # Load checkpoint - EXACTLY like working generate_text
            checkpoint = torch.load(model_path, map_location=torch.device("cpu"), weights_only=True)
            model.load_state_dict(checkpoint["model_state_dict"])
            model.eval()

            print("Model loaded successfully!")

            # Tokenize input
            input_ids = tokenizer.encode(text)

            # Get attention weights
            print("Getting attention weights...")
            print(f"DEBUG: input_ids: {input_ids}")
            print(f"DEBUG: text: '{text}'")

            with torch.no_grad():
                try:
                    input_tensor = torch.tensor([input_ids])
                    print(f"DEBUG: input_tensor shape: {input_tensor.shape}")
                    print(f"DEBUG: About to call model forward pass")

                    # Forward pass to get logits and attention weights
                    logits, attentions = model(input_tensor)

                    print(f"DEBUG: Forward pass successful")
                    print(f"DEBUG: logits shape: {logits.shape if logits is not None else 'None'}")
                    print(f"DEBUG: attentions type: {type(attentions)}")
                    print(
                        f"DEBUG: attentions length: {len(attentions) if attentions is not None else 'None'}"
                    )

                except Exception as e:
                    print(f"DEBUG: Model forward pass failed: {e}")
                    import traceback

                    print(f"DEBUG: Forward pass traceback: {traceback.format_exc()}")
                    raise e

            print("DEBUG: About to create visualization")

            # Create visualization
            tokens = [tokenizer.idx_to_word.get(idx, "<UNK>") for idx in input_ids]
            print(f"DEBUG: tokens: {tokens}")

            attention_image = visualize_attention(tokens, attentions, layer, heads)

            if attention_image is None:
                raise Exception("Visualization failed - returned None")

            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
                "body": json.dumps(
                    {"attention_image": attention_image, "tokens": tokens, "text": text}
                ),
            }

    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback

        print(f"Traceback: {traceback.format_exc()}")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"error": str(e)}),
        }


def visualize_attention(tokens, attentions, layer=0, head=0):
    """Create an attention visualization image as a base64 string."""
    try:
        # Ensure layer and head indices are valid
        if layer >= len(attentions):
            layer = 0

        attention_tensor = attentions[layer]
        print(f"DEBUG: attention_tensor shape: {attention_tensor.shape}")
        print(f"DEBUG: attention_tensor type: {type(attention_tensor)}")

        if len(attention_tensor.shape) == 4:  # [batch, heads, seq, seq]
            if head >= attention_tensor.shape[1]:
                head = 0
            print(f"DEBUG: Using 4D tensor, extracting [0, {head}]")
            attention = attention_tensor[0, head].cpu().numpy()
        else:
            print(f"DEBUG: Using non-4D tensor, extracting [0]")
            attention = attention_tensor[0].cpu().numpy()

        print(f"DEBUG: attention array shape: {attention.shape}")
        print(f"DEBUG: attention array type: {type(attention)}")

        fig, ax = plt.subplots(figsize=(10, 10))
        print("DEBUG: Created matplotlib figure")

        im = ax.imshow(attention, cmap="Blues")
        print("DEBUG: Created imshow")

        # Set ticks and labels
        ax.set_xticks(range(len(tokens)))
        ax.set_yticks(range(len(tokens)))
        ax.set_xticklabels(tokens, rotation=45, ha="right")
        ax.set_yticklabels(tokens)
        print("DEBUG: Set ticks and labels")

        ax.set_title(f"Attention Layer {layer+1}, Head {head+1}")
        ax.set_xlabel("Key")
        ax.set_ylabel("Query")
        print("DEBUG: Set titles and labels")

        plt.colorbar(im, ax=ax)
        plt.tight_layout()
        print("DEBUG: Added colorbar and tight layout")

        # Convert plot to base64 string
        buffer = BytesIO()
        plt.savefig(buffer, format="png", dpi=150, bbox_inches="tight")
        buffer.seek(0)
        print("DEBUG: Saved figure to buffer")

        image_base64 = base64.b64encode(buffer.read()).decode("utf-8")
        plt.close(fig)
        print("DEBUG: Converted to base64 and closed figure")

        return image_base64

    except Exception as e:
        print(f"Visualization error details: {e}")
        print(f"Error type: {type(e)}")
        import traceback

        print(f"Full traceback: {traceback.format_exc()}")
        return None
