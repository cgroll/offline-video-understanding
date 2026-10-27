"""Speaker diarization with NVIDIA Sortformer (NeMo, GPU), reused from `conversation-transcriptor`'s working
integration (model: nvidia/diar_streaming_sortformer_4spk-v2.1). Loaded, used and freed inside one call so it is
never resident at the same time as the VLM.
"""

MODEL = "nvidia/diar_streaming_sortformer_4spk-v2.1"


def diarize(wav_path: str) -> list[dict]:
    """Diarized speaker intervals for a whole (short) audio file: [{start, end, speaker}], speaker as
    "SPEAKER_00".."SPEAKER_03" (Sortformer supports at most 4 concurrent speakers)."""
    import torch
    from nemo.collections.asr.models import SortformerEncLabelModel

    model = SortformerEncLabelModel.from_pretrained(MODEL).eval().cuda()
    try:
        # high-latency streaming setup from the model card, best for whole offline files (same as
        # conversation-transcriptor's proven configuration)
        modules = model.sortformer_modules
        modules.chunk_len = 340
        modules.chunk_right_context = 40
        modules.fifo_len = 40
        modules.spkcache_update_period = 300
        modules.spkcache_len = 188
        modules._check_streaming_parameters()

        raw = model.diarize(audio=[wav_path], batch_size=1, verbose=False)[0]
    finally:
        del model
        torch.cuda.empty_cache()

    intervals = []
    for seg in raw:
        start, end, speaker = seg.split()
        speaker_no = int(speaker.split("_")[-1])
        intervals.append({"start": round(float(start), 2), "end": round(float(end), 2),
                          "speaker": f"SPEAKER_{speaker_no:02d}"})
    return intervals


def assign_speakers(segments: list[dict], intervals: list[dict]) -> None:
    """Sets segment["speaker"] in place: the diarized interval with the largest time overlap with the segment, or
    None if no interval overlaps it at all."""
    for seg in segments:
        best_speaker, best_overlap = None, 0.0
        for iv in intervals:
            overlap = min(seg["end"], iv["end"]) - max(seg["start"], iv["start"])
            if overlap > best_overlap:
                best_overlap, best_speaker = overlap, iv["speaker"]
        seg["speaker"] = best_speaker
