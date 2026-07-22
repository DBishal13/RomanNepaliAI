from pathlib import Path
from roman_nepali_ai.batch import process_srt_folder


def test_process_srt_folder(tmp_path):
    src = tmp_path / "in"
    dst = tmp_path / "out"
    src.mkdir()
    # create two small srt files
    (src / "a.srt").write_text("1\n00:00:00,000 --> 00:00:01,000\nma ghar gaye\n", encoding='utf-8')
    (src / "b.srt").write_text("1\n00:00:00,000 --> 00:00:01,000\nyo ramro cha\n", encoding='utf-8')

    count = process_srt_folder(str(src), str(dst), backend='stub')
    assert count == 2
    # outputs exist
    assert (dst / 'a.srt').exists()
    assert (dst / 'b.srt').exists()
    assert 'ma ghar gaye' in (dst / 'a.srt').read_text(encoding='utf-8')
