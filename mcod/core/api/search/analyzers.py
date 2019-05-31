from elasticsearch_dsl import analyzer, token_filter

__all__ = ('standard_analyzer', 'polish_analyzer')

polish_hunspell = token_filter(
    'pl',
    type="hunspell",
    locale="pl_PL",
    dedup=True
)

polish_stopwords = token_filter(
    'polish_stopwords',
    type="stop",
    ignore_case=True,
    stopwords_path='stopwords.txt'
)

standard_analyzer = analyzer(
    'standard_analyzer',
    tokenizer="standard",
    filter=["standard", polish_stopwords, "lowercase"],
    char_filter=["html_strip"]
)

standard_asciied = analyzer(
    'standard_analyzer',
    tokenizer="standard",
    filter=["lowercase", "asciifolding", "trim"],
    char_filter=["html_strip"]
)

polish_analyzer = analyzer(
    'polish_analyzer',
    tokenizer="standard",
    filter=["standard", polish_stopwords, "lowercase", polish_hunspell],
    char_filter=["html_strip"]
)

pl_ascii_folding = token_filter(
    'pl_ascii_folding',
    type='asciifolding',
    preserve_original=True
)

polish_asciied = analyzer(
    'polish_asciied',
    type='custom',
    tokenizer="standard",
    filter=["lowercase", pl_ascii_folding, "trim"],
    char_filter=["html_strip"]
)
