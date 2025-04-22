from backend.main import clean_latex


def test_clean_latex_removes_code_block_markers():
    input_str = "```latex\n\\documentclass{article}\n```"
    expected = "\\documentclass{article}"
    assert clean_latex(input_str) == expected


def test_clean_latex_removes_plain_code_block():
    input_str = "```\n\\begin{document}\nHello\n```"
    expected = "\\begin{document}\nHello"
    assert clean_latex(input_str) == expected


def test_clean_latex_no_markers():
    input_str = "\\section{Test}"
    assert clean_latex(input_str) == input_str


def test_clean_latex_empty_string():
    assert clean_latex("") == ""


def test_clean_latex_only_markers():
    assert clean_latex("```latex```") == ""
