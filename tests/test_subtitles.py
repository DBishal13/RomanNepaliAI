from roman_nepali_ai.subtitles import parse_srt, write_srt, translate_srt


def test_parse_and_write_roundtrip(tmp_path):
    content = """1
00:00:00,000 --> 00:00:02,000
ma ghar gaye

2
00:00:02,500 --> 00:00:04,000
yo ramro cha
"""
    infile = tmp_path / "in.srt"
    outfile = tmp_path / "out.srt"
    infile.write_text(content, encoding='utf-8')

    # Using stub backend should produce identical texts
    translate_srt(str(infile), str(outfile), backend='stub')
    out = outfile.read_text(encoding='utf-8')
    assert 'ma ghar gaye' in out
    assert 'yo ramro cha' in out

    # parse and ensure structure
    caps = parse_srt(str(infile))
    assert len(caps) == 2
    assert caps[0]['text'].strip() == 'ma ghar gaye'


def test_normalize_wraps_long_lines(tmp_path):
    # create a single caption with a very long line
    long_text = """1
00:00:00,000 --> 00:00:05,000
" + ("word " * 30).strip() + "\n"
    infile = tmp_path / "in2.srt"
    outfile = tmp_path / "out2.srt"
    infile.write_text(long_text, encoding='utf-8')

    # stub backend + normalization should wrap lines (introducing a newline)
    translate_srt(str(infile), str(outfile), backend='stub', normalize=True)
    out = outfile.read_text(encoding='utf-8')
    # the output text should contain at least one newline inside the caption text
    assert '\n' in out.strip().split('\n', 2)[-1]
