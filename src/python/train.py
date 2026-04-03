"""
train.py ──────────────────────────────────────────────────────────────
Launch a Hugging Face / Transformers fine-tune on AWS SageMaker,
upload checkpoints to S3, and register the resulting model in Snowflake.

Structure
─────────
• get_hyperparameters()  → command-line & YAML merge
• build_estimator()      → SageMaker HuggingFace estimator object
• launch_training()      → fit() call + async logs
• register_model()      → INSERT row in SNOWFLAKE.MODEL_REGISTRY
• main()                 → glue above pieces

Usage
─────
$ python train.py --dataset s3://bucket/mydata --base_model meta-llama/Llama-3-8B
"""

import argparse
import os
from datetime import datetime
from typing import Dict

from sagemaker.huggingface import HuggingFace
import snowflake.connector


# ---------------------------------------------------------------------
# 1. Parse CLI arguments & default hyper-params
# ---------------------------------------------------------------------
def get_hyperparameters() -> Dict:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True, help="S3 URI of training dataset")
    parser.add_argument("--base_model", default="bertscore/bert-base-uncased")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--lr", type=float, default=2e-5)
    parser.add_argument("--batch_size", type=int, default=8)
    parser.add_argument("--out_path", default="s3://transformerforge/models/")
    parser.add_argument("--job_suffix", default=datetime.utcnow().strftime("%Y%m%d-%H%M%S"))
    args = parser.parse_args()

    return {
        "dataset_uri": args.dataset,
        "model_name": args.base_model,
        "learning_rate": args.lr,
        "epochs": args.epochs,
        "per_device_train_batch_size": args.batch_size,
        "output_dir": args.out_path,
        "job_name": f"tf-finetune-{args.job_suffix}",
    }


# ---------------------------------------------------------------------
# 2. Build SageMaker Hugging Face estimator
# ---------------------------------------------------------------------
def build_estimator(hp: Dict) -> HuggingFace:
    huggingface_estimator = HuggingFace(
        transformers_version="4.39",
        pytorch_version="2.2",
        python_version="3.11",
        instance_type="ml.g5.xlarge",
        instance_count=1,
        role=os.environ["SAGEMAKER_EXEC_ROLE"],
        base_job_name=hp["job_name"],
        hyperparameters={
            "model_name_or_path": hp["model_name"],
            "dataset_uri": hp["dataset_uri"],
            "num_train_epochs": hp["epochs"],
            "learning_rate": hp["learning_rate"],
            "per_device_train_batch_size": hp["per_device_train_batch_size"],
            "output_dir": "/opt/ml/model",
        },
    )
    return huggingface_estimator


# ---------------------------------------------------------------------
# 3. Launch training & stream logs
# ---------------------------------------------------------------------
def launch_training(estimator: HuggingFace, hp: Dict) -> str:
    estimator.fit(
        inputs={"train": hp["dataset_uri"]},
        wait=True,
        logs="All",
    )
    model_artifact = estimator.model_data  # s3://.../output/model.tar.gz
    return model_artifact


# ---------------------------------------------------------------------
# 4. Register model + metadata in Snowflake
# ---------------------------------------------------------------------
def register_model(hp: Dict, model_uri: str) -> None:
    conn = snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        database="TRANSFORMERFORGE",
        schema="PUBLIC",
        warehouse="COMPUTE_WH",
    )
    try:
        cur = None
        cur = conn.cursor()
        try:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS MODEL_REGISTRY (
                  ts TIMESTAMP,
                  job_name STRING,
                  base_model STRING,
                  epochs INT,
                  lr FLOAT,
                  model_uri STRING
                )
                """
            )
            cur.execute(
                """
                INSERT INTO MODEL_REGISTRY (ts, job_name, base_model, epochs, lr, model_uri)
                VALUES (%(ts)s, %(job)s, %(base)s, %(ep)s, %(lr)s, %(uri)s)
                """,
                {
                    "ts": datetime.utcnow(),
                    "job": hp["job_name"],
                    "base": hp["model_name"],
                    "ep": hp["epochs"],
                    "lr": hp["learning_rate"],
                    "uri": model_uri,
                },
            )
        finally:
            if cur is not None:
                cur.close()
    finally:
        conn.close()
    print("✅ Model metadata logged to Snowflake")


# ---------------------------------------------------------------------
# 5. Main entry-point
# ---------------------------------------------------------------------
def main():
    hp = get_hyperparameters()
    estimator = build_estimator(hp)
    artifact_uri = launch_training(estimator, hp)
    register_model(hp, artifact_uri)
    print(f"🎉 Training completed • Artifact → {artifact_uri}")


if __name__ == "__main__":
    main()
