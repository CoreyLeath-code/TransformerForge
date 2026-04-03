from moto import mock_sagemaker
from src.python.train import build_estimator

@mock_sagemaker
def test_estimator_builds():
    hp = {
        "job_name": "test-job",
        "model_name": "bert-base-uncased",
        "dataset_uri": "s3://dummy",
        "epochs": 1,
        "learning_rate": 1e-5,
        "per_device_train_batch_size": 2,
    }
    # Moto creates a fake SageMaker endpoint so build_estimator should succeed
    est = build_estimator(hp)
    assert est.hyperparameters["model_name_or_path"] == "bert-base-uncased"
