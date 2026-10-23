import json
from minisense.cli import main


def test_generate_cli(tmp_path, capsys):
    path = tmp_path / "responses.json"
    main(["--data", str(path), "generate", "--count", "100"])
    assert len(json.loads(path.read_text())["responses"]) == 100


def test_dataset_validation_cli(tmp_path, capsys):
    path = tmp_path / "responses.json"
    main(["--data", str(path), "generate", "--count", "100000"])
    main(["--data", str(path), "validate"])
    result = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert result["count"] == 100000
    assert result["months"] == {"2026-05": 47000, "2026-06": 53000}
