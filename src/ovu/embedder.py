"""EmbeddingGemma 2: one 768-d space for text, images, video and audio."""

MODEL = "google/embeddinggemma-2"
DIM = 768


def load_embedder(audio: bool = True):
    import torch
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(
        MODEL,
        device="cuda",
        model_kwargs={"torch_dtype": torch.bfloat16},
        config_kwargs={} if audio else {"audio_config": None},
    )
    model.max_seq_length = 8192
    # frames are already sampled at 1 fps; keep all of them
    model[0].processor.video_processor.do_sample_frames = False
    return model


def as_document(text: str, title: str = "none") -> str:
    return f"title: {title} | text: {text}"


def encode_queries(model, queries: list[str]):
    return model.encode(queries, prompt_name="SearchQuery", normalize_embeddings=True)
