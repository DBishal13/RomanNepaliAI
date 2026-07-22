import pytest

from roman_nepali_ai import cli


def run_cli(monkeypatch, args):
    monkeypatch.setattr("sys.argv", ["roman-nepali-ai"] + args)
    cli.main()


def test_default_direction_unchanged(monkeypatch, capsys):
    run_cli(monkeypatch, ["namaste", "--backend", "stub"])
    assert capsys.readouterr().out.strip() == "namaste"


def test_explicit_reverse_direction_with_stub(monkeypatch, capsys):
    # stub ignores direction but the flags must still parse and run cleanly
    run_cli(monkeypatch, ["hello", "--backend", "stub", "--src", "en", "--tgt", "ne"])
    assert capsys.readouterr().out.strip() == "hello"


def test_unsupported_language_code_exits(monkeypatch):
    monkeypatch.setattr("sys.argv", ["roman-nepali-ai", "hello", "--src", "fr"])
    with pytest.raises(SystemExit):
        cli.main()


def test_transliterate_casual_flag(monkeypatch, capsys):
    run_cli(monkeypatch, ["malai tha xaina", "--transliterate", "--casual"])
    assert capsys.readouterr().out.strip() == "मलाई था छैन"


def test_transliterate_formal_flag(monkeypatch, capsys):
    run_cli(monkeypatch, ["ghar", "--transliterate"])
    assert capsys.readouterr().out.strip() == "घर्"


def test_srt_in_without_srt_out_prints_guard(monkeypatch, capsys):
    run_cli(monkeypatch, ["--srt-in", "in.srt"])
    assert "--srt-out is required" in capsys.readouterr().out


def test_no_text_and_no_srt_prints_guard(monkeypatch, capsys):
    run_cli(monkeypatch, [])
    assert "Either provide text" in capsys.readouterr().out


def test_srt_roundtrip_with_direction_flags(monkeypatch, capsys, tmp_path):
    in_path = tmp_path / "in.srt"
    out_path = tmp_path / "out.srt"
    in_path.write_text("1\n00:00:00,000 --> 00:00:01,000\nhello\n", encoding="utf-8")

    run_cli(monkeypatch, [
        "--srt-in", str(in_path), "--srt-out", str(out_path),
        "--backend", "stub", "--src", "en", "--tgt", "ne",
    ])
    assert out_path.exists()
    assert f"Wrote translated SRT to {out_path}" in capsys.readouterr().out
    assert "hello" in out_path.read_text(encoding="utf-8")


def test_batch_with_direction_flags(monkeypatch, capsys, tmp_path):
    in_dir = tmp_path / "in"
    out_dir = tmp_path / "out"
    in_dir.mkdir()
    (in_dir / "a.srt").write_text("1\n00:00:00,000 --> 00:00:01,000\nhello\n", encoding="utf-8")

    run_cli(monkeypatch, [
        "--batch-in", str(in_dir), "--batch-out", str(out_dir),
        "--backend", "stub", "--src", "en", "--tgt", "ne",
    ])
    assert (out_dir / "a.srt").exists()
    assert "Processed 1 files" in capsys.readouterr().out
