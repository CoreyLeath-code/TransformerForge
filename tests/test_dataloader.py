"""
tests/test_dataloader.py
────────────────────────────────────────────────────────────────────────────
Validates that the Java DataLoader JAR can read Parquet/Delta input and
produce sharded JSONL output.

The test:
1. Generates a tiny Parquet file containing a 'body_text' column.
2. Invokes the shaded DataLoader JAR via `subprocess`.
3. Verifies that JSONL shards exist and contain the expected number of rows.

PySpark is used only if installed; otherwise the test is skipped in CI.
"""

import json
import subprocess
from pathlib import Path

import pytest

JAR_PATH = Path("src/java/target").glob("dataloader-*-shaded.jar")
JAR_PATH = next(JAR_PATH, None)


@pytest.mark.skipif(JAR_PATH is None, reason="DataLoader jar not built")
def test_dataloader_end_to_end(tmp_path):
    try:
        from pyspark.sql import SparkSession
    except ImportError:
        pytest.skip("PySpark not installed")

    spark = (
        SparkSession.builder.master("local[*]")
        .appName("ForgeTest")
        .config("spark.sql.shuffle.partitions", 1)
        .getOrCreate()
    )

    # 1. Create sample Parquet input
    in_dir = tmp_path / "parquet"
    out_dir = tmp_path / "jsonl"
    df = spark.createDataFrame(
        [(1, "TransformerForge is awesome."), (2, "Multi-language MLOps rocks!")],
        ["id", "body_text"],
    )
    df.write.mode("overwrite").parquet(str(in_dir))

    # 2. Run DataLoader JAR
    cmd = [
        "spark-submit",
        "--class",
        "dataloader.DataLoader",
        str(JAR_PATH),
        str(in_dir),
        str(out_dir),
        "body_text",
    ]
    subprocess.check_call(cmd)

    # 3. Validate output shards
    shards = list(out_dir.glob("part-*"))
    assert shards, "No JSONL shards produced"
    lines = sum(1 for f in shards for _ in f.open())
    assert lines == 2, f"Expected 2 lines, found {lines}"

    # Check JSON validity
    sample_line = shards[0].open().readline().strip()
    json.loads(sample_line)

    # Cleanup Spark
    spark.stop()
