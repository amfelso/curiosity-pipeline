from functions.embed_memories_to_pinecone import app


def test_generate_embeddings():
    input_payload = {"urls": [("https://curiosity-data-1205.s3.us-east-1.amazonaws.com/memories/"
                                "2024-01-08/image1216927_memory.txt"),
                              ("https://curiosity-data-1205.s3.us-east-1.amazonaws.com/memories/"
                                "2024-01-08/image1216942_memory.txt"),
                              ("https://curiosity-data-1205.s3.us-east-1.amazonaws.com/memories/"
                                "2024-01-08/image1216944_memory.txt"),
                              ("https://curiosity-data-1205.s3.us-east-1.amazonaws.com/memories/"
                                "2024-01-08/image1216948_memory.txt"),
                              ("https://curiosity-data-1205.s3.us-east-1.amazonaws.com/memories/"
                                "2024-01-08/image1216966_memory.txt")]}

    data = app.lambda_handler(input_payload, "")

    assert data["statusCode"] == 200
    assert len(data["body"]) == 5

    assert "id" in data["body"][0]
    assert "date" in data["body"][0]
    assert "type" in data["body"][0]
    assert "s3_url" in data["body"][0]
