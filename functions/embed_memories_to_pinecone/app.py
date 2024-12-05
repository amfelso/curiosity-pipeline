from random import randint


def lambda_handler(event, context):
    """
    Lambda function to embed memories and diary entries into PineconeDB for RAG.
    """
    # Check current price of the stock
    stock_price = randint(
        0, 100
    )  # Current stock price is mocked as a random integer between 0 and 100
    return {"stock_price": stock_price}
