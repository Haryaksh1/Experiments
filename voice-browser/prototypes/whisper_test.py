import whisper

model = whisper.load_model("tiny")

result = model.transcribe("test.wav", fp16=False)

print("\nTranscription:")
print(result["text"])